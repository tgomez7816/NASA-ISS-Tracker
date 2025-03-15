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

# Instructions to Deploy Application using Docker-Compose
GENERAL INSTRUCTIONS NEED SPECIFICATION

1. Build Docker Images

2. Start It Up

3. Verify Deployment

4. Stop Services

# Instructions to Curl all Routes

1. /epochs

2. /epochs?limit=int&offset=int

3. /epochs/<epoch>

4. /epochs/<epoch>/speed

5. /epochs/<epoch>/location

6. /now

# Instructions to Run Containerized Tests

These steps can only be run after the application is deployed (instructions included in previous section).

1. Run Tests
-> include BASH docker-compsose run test

2. Verify Results

3. Stop Services

# International Space Station Tracking Data

The following link is the xml data that is hard coded into the iss_tracker.py file: https://nasa-public-data.s3.amazonaws.com/iss-coords/current/ISS_OEM/ISS.OEM_J2K_EPH.xml

For further exploration of ISS data visit: https://spotthestation.nasa.gov/trajectory_data.cfm

# Software Diagram



