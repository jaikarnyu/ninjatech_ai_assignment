
# NINJATECH TAKE HOME ASSIGNMENT 

## Overview

Implemented services for Users, Orders, and Notifications.

## How to Run the Service Locally

Follow the steps below to run the service locally:

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

### 5. Setup AWS keys

``` export aws_access_key_id=<AWS_ACCESS_KEY> ```
``` export aws_secret_key_id=<AWS_SECRET_KEY> ```

Make sure to use these keys either in github actions script/ github secrets to enable CD Pipeline

### 6. Run Tests

To run the tests, execute the following command:

```bash
nosetests tests
```


### 7. Start the Service

To start the service, run the startup script:

```bash
sh startup.sh
```

### 8. Try Out the APIs

Open your web browser and navigate to:

```
http://localhost:8080
```

You can now try out the APIs and explore the service.



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





