import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import os
import requests
from typing import List, Dict, Any
from flask import Flask, jsonify, request
import redis
from geopy.geocoders import Nominatim
import math
from math import atan2, sqrt, degrees

#Redis connection
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = int(os.getenv('REDIS_PORT', 6379))    # port
try:
    redis_client = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)
    redis_client.ping()  # test connection
except redis.exceptions.ConnectionError as e:
    raise Exception(f"Failed to connect to Redis: {e}")

app = Flask(__name__)

iss_data_global = []

def fetch_iss_data(url: str) -> List[Dict[str, Any]]:
    '''
    Fetches ISS trajectory data from NASA's website and parses it.
    
    Inputs:
        url: URL for the NASA ISS trajectory data
    
    Returns:
        List of dictionaries containing ISS state vectors
    '''
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        xml_content = response.text #looks for weird tags in xml data that won't be processed
        start_idx = xml_content.find('<stateVector')
        end_idx = xml_content.rfind('</stateVector>') + len('</stateVector>')
        
        if start_idx == -1 or end_idx == -1:
            raise ValueError("No ISS Vectors found")
        #makes an xml file that holds the vector data in a processable way
        clean_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        clean_xml += '<ndm><oem><body><segment>\n'
        clean_xml += xml_content[start_idx:end_idx]
        clean_xml += '\n</segment></body></oem></ndm>'
        #parse that data
        root = ET.fromstring(clean_xml)
        data = []
        
        for elem in root.findall('.//stateVector'): #takes components of position, velocity, and epoch values
            epoch = elem.find('EPOCH').text
            position = {
                'X': float(elem.find('X').text),
                'Y': float(elem.find('Y').text),
                'Z': float(elem.find('Z').text)
            }
            velocity = {
                'X_DOT': float(elem.find('X_DOT').text),
                'Y_DOT': float(elem.find('Y_DOT').text),
                'Z_DOT': float(elem.find('Z_DOT').text)
            }
            data.append({
                'EPOCH': epoch,
                'POSITION': position,
                'VELOCITY': velocity
            })
            
            #store each state vector in Redis using epoch as key
            redis_client.set(epoch, json.dumps({
                'EPOCH': epoch,
                'POSITION': position,
                'VELOCITY': velocity,
                }))

        print(f"Stored {len(data)} state vectors in Redis.")
        return data

    except requests.RequestException as e:
        raise Exception(f"Failed to fetch data from NASA: {e}")
    except ET.ParseError as e:
        raise Exception(f"Failed in XML data: {e}")

def calculate_speed(velocity: Dict[str, float]) -> float:
    '''
    Calculates the speed (magnitude of velocity vector) of the ISS.
    
    Inputs:
        velocity: dictionary with velocity components
    
    Returns:
        Calculated speed
    '''
    return math.sqrt(velocity['X_DOT']**2 + velocity['Y_DOT']**2 + velocity['Z_DOT']**2) #general vector magnitude formula

def find_closest_epoch(data: List[Dict[str, Any]], current_time: datetime) -> Dict[str, Any]:
    '''
    Finds the closest epoch to the current time.
    
    Inputs:
        data: ISS data points
        current_time: Current time to compare against
    
    Returns:
        Data entry with the closest epoch
    '''
    #current_time is offset-aware -> include further explanation in write up
    current_time = current_time.replace(tzinfo=timezone.utc)

    # find the closest epoch
    return min(data, key=lambda x: abs(datetime.strptime(x['EPOCH'], "%Y-%jT%H:%M:%S.%f%z") - current_time))

@app.route('/', methods=['GET'])
def home():
    '''
    Returns information about the API
    '''
    return jsonify({
        'description': 'ISS Tracking API',
        'endpoints': [
            '/epochs', #gets all state vectors
            '/epochs?limit=int&offset=int',
            '/epochs/<epoch>', #specific vector
            '/epochs/<epoch>/speed', #speed
            '/now'#nearest time
        ]
    })

@app.route('/epochs', methods=['GET'])
def get_epochs():
    '''
    Returns epochs based on parameters
    '''
    #breaks data into smaller workable parts
    limit = request.args.get('limit', default=None, type=int)
    offset = request.args.get('offset', default=0, type=int)
    
    #get all epochs from Redis
    keys = sorted(redis_client.keys()) #sorts by ascending order

    if not keys:
        return jsonify([])

    #return parts within limit, no limit means all epochs
    if limit is not None:
        keys = keys[offset:offset + limit]
    else:
        keys = keys[offset:]

    #get data for each key
    data = [json.loads(redis_client.get(key)) for key in keys]
    return jsonify(data)


@app.route('/epochs/<epoch>', methods=['GET'])
def get_epoch(epoch):
    '''
    Returns informaton on a specific epoch
    '''
    #looking for epoch that matches current time
    data = redis_client.get(epoch)
    if data:
        return jsonify(json.loads(data))
    return jsonify({'error': 'Epoch not found'}), 404 #error when no epoch is found

@app.route('/epochs/<epoch>/speed', methods=['GET'])
def get_epoch_speed(epoch):
    '''
    Returns the speed
    '''
    #looking for matching state vector
    data = redis_client.get(epoch)
    if data:
        data = json.loads(data) #makes json string into dict
        velocity = data['VELOCITY']
        speed = calculate_speed(velocity)
        return jsonify({'speed': speed})
    return jsonify({'error': 'No speed found'}), 404

@app.route('/now', methods=['GET'])
def get_nearest_epoch_location():
    '''
    Returns the latitude, longitude, altitude, and geoposition for the real-time position of the ISS.
    '''
    #make current_time offset-aware by adding UTC timezone
    current_time = datetime.utcnow().replace(tzinfo=timezone.utc)

    #gets all epochs from Redis
    keys = redis_client.keys()
    if not keys:
        return jsonify({'error': 'No ISS data available'}), 404  #error if Redis is empty

    try:
        #find the closest epoch to the current time
        closest_epoch = min(
            keys,
            key=lambda epoch: abs(
                datetime.fromisoformat(epoch.replace('Z', '+00:00')) - current_time
            )
        )

        #gets state vector for the closest epoch
        data = redis_client.get(closest_epoch)
        if not data:
            return jsonify({'error': 'No data found for the closest epoch'}), 404

        #parse the data
        data = json.loads(data)
        position = data['POSITION']
        x = position['X']
        y = position['Y']
        z = position['Z']

        #calculate latitude, longitude, and altitude
        earth_radius = 6371  # radius in km
        latitude = degrees(atan2(z, sqrt(x**2 + y**2)))  # degrees
        longitude = degrees(atan2(y, x))
        altitude = sqrt(x**2 + y**2 + z**2) - earth_radius  # altitude

        # GeoPy to get the geoposition
        geolocator = Nominatim(user_agent="iss_tracker")
        location = geolocator.reverse((latitude, longitude), language='en')
        geoposition = location.address if location else "Unknown location"

        return jsonify({
            'latitude': latitude,
            'longitude': longitude,
            'altitude': altitude,
            'geoposition': geoposition,
            'EPOCH': closest_epoch
        }), 200

    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@app.route('/epochs/<epoch>/location', methods=['GET'])
def get_epoch_location(epoch):
    '''
    Returns latitude, longitude, altitude, and geoposition for a given epoch.
    '''
    #get the state vector for the given epoch from Redis
    data = redis_client.get(epoch)
    if not data:
        return jsonify({'error': 'Epoch not found'}), 404

    try:
        # parse the data
        data = json.loads(data)
        position = data['POSITION']
        x = position['X']
        y = position['Y']
        z = position['Z']

        # calculate latitude, longitude, and altitude
        earth_radius = 6371  
        latitude = degrees(atan2(z, sqrt(x**2 + y**2)))  
        longitude = degrees(atan2(y, x))
        altitude = sqrt(x**2 + y**2 + z**2) - earth_radius

        geolocator = Nominatim(user_agent="iss_tracker")
        location = geolocator.reverse((latitude, longitude), language='en')

        return jsonify({
            'latitude': latitude,
            'longitude': longitude,
            'altitude': altitude,
            'geoposition': geoposition
        }), 200

    except Exception as e:
        #unexpected errors
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

def main():
    NASA_URL = "https://nasa-public-data.s3.amazonaws.com/iss-coords/current/ISS_OEM/ISS.OEM_J2K_EPH.xml"

    try:
        print("Fetching ISS data from NASA...")
        fetch_iss_data(NASA_URL)  # get data and store data in Redis
        print("ISS data successfully loaded into Redis.")
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == '__main__':
    main()
