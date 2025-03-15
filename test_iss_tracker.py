import pytest
import os
import json 
from datetime import datetime
from iss_tracker import app, fetch_iss_data, calculate_speed, find_closest_epoch, redis_client

@pytest.fixture #makes test client for flask application
def client():
    app.config['TEST'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture #makes test file with sample xml data
def test_file():
    test_file = "test_iss_data.xml"
    with open(test_file, "w") as f:
        f.write("""<?xml version="1.0"?>

<nmd>
    <stateVector>
        <EPOCH>2025-02-21T12:00:00.000Z</EPOCH>
        <X>1000</X>
        <Y>2000</Y>
        <Z>3000</Z>
        <X_DOT>1</X_DOT>
        <Y_DOT>2</Y_DOT>
        <Z_DOT>3</Z_DOT>
    </stateVector>
    <stateVector>
        <EPOCH>2025-02-21T12:01:00.000Z</EPOCH>
        <X>1001</X>
        <Y>2002</Y>
        <Z>3003</Z>
        <X_DOT>1.1</X_DOT>
        <Y_DOT>2.2</Y_DOT>
        <Z_DOT>3.3</Z_DOT>
    </stateVector>
</ndm>""")
    yield test_file
    if os.path.exists(test_file):
        os.remove(test_file)

def test_redis_population():
    NASA_URL = "https://nasa-public-data.s3.amazonaws.com/iss-coords/current/ISS_OEM/ISS.OEM_J2K_EPH.xml"
    fetch_iss_data(NASA_URL)  #fetch and store data in Redis

    keys = redis_client.keys()
    print(f"Number of keys in Redis: {len(keys)}")
    assert len(keys) > 0, "Redis is not populated with ISS data"

def test_fetch_iss_data(): #checks that epoch, position, and velocity are in in the dict returned by fetch_iss_data
    data = fetch_iss_data("https://nasa-public-data.s3.amazonaws.com/iss-coords/current/ISS_OEM/ISS.OEM_J2K_EPH.xml")
    assert isinstance(data, list)
    assert len(data) > 0
    assert 'EPOCH' in data[0]
    assert 'POSITION' in data[0]
    assert 'VELOCITY' in data[0]

def test_calculate_speed(): #tests calculate speed using a known vector with a ckecked magnitude
    velocity = {'X_DOT': 1.0, 'Y_DOT': 2.0, 'Z_DOT': 3.0}
    speed = calculate_speed(velocity)
    assert pytest.approx(speed, 0.0001) == 3.7416573867739413

def test_find_closest_epoch(): 
    data = fetch_iss_data("https://nasa-public-data.s3.amazonaws.com/iss-coords/current/ISS_OEM/ISS.OEM_J2K_EPH.xml")
    current_time = datetime.utcnow()
    closest = find_closest_epoch(data, current_time)
    assert 'EPOCH' in closest

def test_home_route(client):
    response = client.get('/')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'description' in data
    assert 'endpoints' in data

def test_epochs_route(client):
    #without parameters
    response = client.get('/epochs')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)

    #with parameters
    response = client.get('/epochs?limit=2&offset=0')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 2

def test_specific_epoch_route(client):
    response = client.get('/epochs')
    epochs = json.loads(response.data)
    if epochs:
        epoch = epochs[0]['EPOCH']
        response = client.get(f'/epochs/{epoch}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['EPOCH'] == epoch

def test_epoch_speed_route(client):
    response = client.get('/epochs')
    epochs = json.loads(response.data)
    if epochs:
        epoch = epochs[0]['EPOCH']
        response = client.get(f'/epochs/{epoch}/speed')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'speed' in data

def test_epoch_location_route(client):
    #fetch all epochs to get a valid epoch
    response = client.get('/epochs')
    assert response.status_code == 200
    epochs = json.loads(response.data)

    if epochs:
        #use the first epoch for testing
        epoch = epochs[0]['EPOCH']
        response = client.get(f'/epochs/{epoch}/location')
        assert response.status_code == 200

        #parse response data
        data = json.loads(response.data)
        assert 'latitude' in data
        assert 'longitude' in data
        assert 'altitude' in data
        assert 'geoposition' in data
        assert isinstance(data['latitude'], float)
        assert isinstance(data['longitude'], float)
        assert isinstance(data['altitude'], float)
        assert isinstance(data['geoposition'], str)
    else:
        pytest.skip("No epochs available to test /epochs/<epoch>/location route.")

def test_error_handling(client):
    #invalid epoch
    response = client.get('/epochs/invalid_epoch')
    assert response.status_code == 404

    #invalid speed calculation
    response = client.get('/epochs/invalid_epoch/speed')
    assert response.status_code == 404

