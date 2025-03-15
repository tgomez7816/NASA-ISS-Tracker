# International Space Station Tracker Data Analysis 

This directory contains a Python scripts that processes data from NASA's Spot the Station website containing vector information about the position and velocity of the International Space Station. The script includes functions to analyze the data, such as, parse the XML file, calculate the speed of the ISS, and find the closest timestamp (EPOCH) to a given time. The code implements a Flask-based REST API with dedicated routes that allow you to navigate the data easily.

# Script Overview

Many of the scripts within this repository are interlinked and will be discussed as they are grouped.

### Docker Compose Related Files
- **`Dockerfile`**: this file creates an image for the application using the working directory and the necessary dependencies listed in the `requirements.txt` file.

- **`docker-compose.yml`**: this file defines the multi-container Docker application with three services; iss_tracker, redis, and test.

- **`requirements.txt`**: this file contains all the required dependencies need to create a suitable Docker environment for the application. 

### Main Function and Test Files
- **`iss_tracker.py`**
    This script includes multiple functions and routes that are used to analyze/navigate the ISS data.

    Functions included:

1. `fetch_iss_data`: this function takes the data provided from the NASA url and parses the xml data. Additionally this function is responsible for storing the data is Redis.

2. `calculate_speed`: this function uses the general vector magnitude formula to calulate the speed of the ISS.

3. `fine_closest_epoch`: this function finds the closest timestamp (EPOCH) to the current time the application is run.

The endpoint routes that are also included in this document will be discussed with there implementation in the "Instructions to Curl all Routes" section.

- **`test_iss_tracker.py`**
    This file includes all of the unit tests to evaluate the functionality of each function and route availible in the iss_tracker.py script. It also includes test related to general Redis connection (which are the first tests conducted). If this test fails other Redis dependent tests, such as any route test will fail.

# Getting Started

Follow these steps to prepare to run the application using Docker-Compose:

## 1. Clone the Repository

First, clone the repository to your local machine:

```bash
git clone git@github.com:tgomez7816/NASA-ISS-Tracker.git
cd NASA-ISS_Tracker
```

# Instructions to Deploy Application using Docker-Compose

## 1. Build Docker Images

Run the following command in your terminal to build images for the services provided in the application:
```bash
docker-compose build
```

## 2. Start It Up
Run the following command in your terminal to start up the application:
```bash
docker-compse up
```
This will start the Flask app and Redis service together. The Flask application will be accessible through:
```bash
http://localhost:5000/
```

## 3. Verify Deployment
These instructions will curl to test the deployment of the API. You can verify that the API is running by:
```bash
curl http://localhost:5000/
```
The result should be the API description.

## 4. Stop Services
To stop the services, in the terminal where the `docker-compose up` is running use:
```bash
docker-compose down
```

# Instructions to Curl all Routes

1. **`/epochs`**

Using GET method, this route returns the entire data set. This can be achieved by running:

```bash
curl http://localhost:5000/epochs
```

Expected Output: JSON array of all epochs with their respective state vectors.

2. **`/epochs?limit=int&offset=int`**

Using GET method, this route returns a modified list of epochs given search parameters. This can be achieved by running:
```bash
curl "http://localhost:5000/epochs?limit=5&offset=2"
```

To make your seach more specific you can edit the numbers in the command.

`limit=` sets the maximum number of epochs to return.

`offset=` determines the number of epochs to skip before starting to return results 

Expected Output: JSON array of epochs starting from the offset and limited to the limit.

3. **`/epochs/<epoch>`**

Using GET method, this route returns state vectors for a specific epoch. This can be achieved by running:
```bash
curl http://localhost:5000/epochs/2025-02-21T12:00:00.000Z
```

Expected Output: JSON containing the state vector for the specified epoch.

4. **`/epochs/<epoch>/speed`**

Using GET method, this route returns the instantaneous speed of a specific epoch. This can be achieved by running:
```bash
curl http://localhost:5000/epochs/2025-02-21T12:00:00.000Z/speed
```

Expected output: JSON containing speed calculation

5. **`/epochs/<epoch>/location`**

Using GET method, this route returns the latitude, longitude, altitude, and geoposition of a specific epoch. This can be achieved by running:
```bash
curl http://localhost:5000/epochs/2025-02-21T12:00:00.000Z/location
```

Expected output: JSON containing, latitude (deg), longitude (deg), altitude (km), and geoposition.

6. **`/now`**

Using GET method, this route returns instantaneous speed, latitude, longitude, altitude, and geoposition for the epoch closest to the current time. This can be achieved by running:
```bash
curl http://localhost:5000/now
```

Expected Output: JSON containing latitude (deg), longitude (deg), altitude
(km), geoposition, speed (km/s), and the nearest epoch.

# Instructions to Run Containerized Tests

These steps can only be run after the application is deployed (instructions included in previous section).

1. Run Tests

In the terminal run:
```bash
docker-compose run test
```
This will execute pytest with the corresponding test file within the container.

2. Verify Results

After running the above command, you should see pytest running with a line `test session starts` visible to you. If any tests fail, the output will include information about the failed tests.

3. Stop Services

After the tests are complete, you can stop the services using:
```bash
docker-compose down
```


# International Space Station Tracking Data

The following link is the xml data that is hard coded into the iss_tracker.py file: https://nasa-public-data.s3.amazonaws.com/iss-coords/current/ISS_OEM/ISS.OEM_J2K_EPH.xml

For further exploration of ISS data visit: https://spotthestation.nasa.gov/trajectory_data.cfm

# Software Diagram



