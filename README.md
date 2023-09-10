
# NINJATECH TAKE HOME ASSIGNMENT 

## Overview

Implemented services for Users, Orders, and Notifications.

## How to Run the Service Locally

Follow the steps below to run the service:

### 1. Clone the Repository

```bash
git clone https://github.com/jaikarnyu/ninjatech_ai_assignment.git
```

### 2. Navigate to the Repository

```bash
cd ninjatech_ai_assignment
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


### 6. Start the Service

To start the service, run the startup script:

```bash
sh startup.sh
```

### 7. Try Out the APIs

Open your web browser and navigate to:

```
http://localhost:8080
```

You can now try out the APIs and explore the service.


## Users API

This section describes the API endpoints related to Users.


### Endpoints

GET /api/users - Returns a list all of the users
GET /api/users/{id} - Returns the user with a given id number
POST /api/users - creates a new user record in the database
PUT /api/users/{id} - updates a user record in the database
DELETE /api/users/{id} - deletes a user record in the database

GET /api/orders - Returns a list all of the orders
GET /api/orders/{id} - Returns the order with a given id number
POST /api/orders - creates a new order record in the database
PUT /api/orders/{id} - updates a order record in the database
DELETE /api/orders/{id} - deletes a order record in the database


GET /api/notifications - Returns a list all of the notifications
GET /api/notifications/{id} - Returns the notification with a given id number
POST /api/notifications - creates a new notification record in the database
PUT /api/notifications/{id} - updates a notification record in the database
DELETE /api/notifications/{id} - deletes a notification record in the database



- **Status Codes**:
  - 200: Successfully retrieved.
  - 201: Resource created
  - 204: Delete request success
  - 400: Bad request, validation error.
  - 401: Unauthorized request or bad api key.
  - 404: Resource not found.
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

