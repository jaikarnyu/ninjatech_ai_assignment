
# MEMFAULT TAKE HOME ASSIGNMENT 

## Overview

Implemented a REST API and SQL schema for a multi-tenant system enabling customers to see what firmware updates have happened on a device.

## How to Run the Service

Follow the steps below to run the service:

### 1. Clone the Repository

```bash
git clone https://github.com/jaikarnyu/memfault-assignment
```

### 2. Navigate to the Repository

```bash
cd memfault-assignment
```

### 3. Open the Project in Visual Studio Code

```bash
code .
```

### 4. Reopen in Container

Click on "Reopen in Container" in Visual Studio Code to launch the development environment in a container.

### 5. Run Tests

To run the tests, execute the following command:

```bash
nosetests tests
```

### 6. Load Sample Data

To load sample data and get API keys and device ID, run the following script:

```bash
python service/scripts/load_sample_data.py
```

This will create and print device & member api-keys along with device_id on the console

### 7. Start the Service

To start the service, run the startup script:

```bash
sh startup.sh
```

### 8. Try Out the APIs

Open your web browser and navigate to:

```
http://localhost:8000
```

You can now try out the APIs and explore the service.


## Firmware Events API

This section describes the API endpoints related to firmware events.

---

#### POST /firmware

- **Description**: Creates a new firmware update event and adds it to task queue. Celery worker receives the message from the queue and persists the record to database
- **Request Parameters**:
  - Body: {"version" : "1.0.0", "timestamp" : 123456677}
  - version should follow semantic versioning & timestamp should be in epoch
  - Headers - X-Device-Api-Key (Device API key)
- **Status Codes**:
  - 202: Update Accepted
  - 400: Bad request, validation error.
  - 401: Unauthorized request or bad api key
  - 404: Device not found 
  - 500: Internal server error.

#### GET /firmware

- **Description**: Lists all the firmware events for a device.
- **Request Parameters**: 
  - path parameter : device_id
  - headers : X-Project-Membership-Api-Key (Membership api key)
- **Response**: A JSON array of firmware event objects.
- **Status Codes**:
  - 200: Successfully retrieved.
  - 400: Bad request, validation error.
  - 401: Unauthorized request or bad api key.
  - 404: Device/member not found.
  - 500: Internal server error.


## Design choices

1. **Flask**:
   - **Why Picked**: Flask is a lightweight and flexible web framework for building web applications. It is chosen for its simplicity and ease of use. Flask comes with handy ORM with flasksqlalchemy & flask-restx for API documentation & UI to try out the APIs
   - **Experience Level**: Flask is my go-to framework for developing APIs. Have 5+ years of experience in using flask.

2. **PostgreSQL**:
   - **Why Picked**: I choose PostgreSQL as my backend database. It provides robustness, scalability, and strong community support. Also,comes with support for multiple data types including JSON. Works well with Flask.
   - **Experience Level**: 5+ years of experience

3. **Celery**:
   - **Why Picked**: Celery is an asynchronous task queue/job queue that can distribute work across machines. I used celery task to persist firmware events to database. Decoupling persistance workload from APIs to celery workers, allows us to distribute the task across machines, reduces latency of APIs, increases fault tolerance by allowing for retrying the failed messages & using dead letter queues.
   - **Experience Level**: 5+ years of experience
  
4. **Redis**:
   - **Why Picked**: Redis is an in-memory data structure store used as a database, cache, and message broker. It is paired with Celery to manage the task queue. I chose redis for its ease of use & works well with celery.
   - **Experience Level**: 5+ years of experience

5. **Gunicorn**:
   - **Why Picked**: Gunicorn is a WSGI HTTP Server used to serve Flask applications in a production environment. It offers efficient multi-process and multi-threaded handling of requests, enhancing application scalability.
   - **Experience Level**: 5+ years of experience

6. **Docker**:
   - **Why Picked**: Docker is a platform used to containerize applications, ensuring that they run consistently across different environments. It simplifies deployment, scaling, and management of the application, promoting DevOps best practices.
   - **Experience Level**: 3+ years of experience.


### TODOs / Future Improvements

1. **Add CI/CD Pipelines Using GitHub Actions**:
- **Description**: Implement Continuous Integration (CI) and Continuous Deployment (CD) pipelines using GitHub Actions. This will automate the build, test, and deployment process, ensuring that the code is consistently validated and seamlessly delivered to the production environment.


2. **Add Routes for CRUD Operations on Models**:
   - **Description**: Implement routes to enable Create, Read, Update, and Delete (CRUD) operations on all models.

3. **Add Tests for Models**:
   - **Description**: Implement test cases to validate the functionality of the data models.
   
4. **Encrypt API Keys**:
   - **Description**: Implement encryption using a private key for API keys to enhance security.


