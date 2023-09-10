# Copyright 2016, 2021 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Package: service
Package for the application models and service routes
This module creates and configures the Flask app and sets up the logging
and SQL database
"""
import sys
from flask import Flask, jsonify, request
from service import config
from service.models.users import Users, db
from service.models.orders import Orders
from service.models.notifications import Notifications
import logging
import traceback
from flask_migrate import Migrate
from celery import Celery
import json


def make_celery(app):
    celery = Celery(app.import_name)
    celery.conf.update(app.config["CELERY_CONFIG"])

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


# Create Flask application
app = Flask(__name__)
app.config.from_object(config)
app.config["SQLALCHEMY_POOL_RECYCLE"] = 3600
celery = make_celery(app)


from service.routes import users
from service.routes import orders
from service.routes import notifications
from service.common import status
from service.common import log_handlers
from service.common.error_handlers import DataValidationError
from service.common import cli_commands

# Set up logging for production
log_handlers.init_logging(app, "service.log")

app.logger.setLevel(logging.DEBUG)


app.logger.info(70 * "*")
app.logger.info("  N I N J A T E C H  S E R V I C E  ".center(70, "*"))
app.logger.info(70 * "*")


try:
    db.init_app(app)
    Users.init_db(app)
    Orders.init_db(app)
    Notifications.init_db(app)
except Exception as error:  # pylint: disable=broad-except
    app.logger.critical("%s: Cannot continue", error)
    # gunicorn requires exit code 4 to stop spawning workers when they die
    sys.exit(4)

migrate = Migrate(app, db)
app.logger.info("Service initialized!")


######################################################################
# Error Handlers
######################################################################


@app.errorhandler(DataValidationError)
def request_validation_error(error):
    """Handles Value Errors from bad data"""
    return bad_request(error)


@app.errorhandler(status.HTTP_400_BAD_REQUEST)
def bad_request(error):
    """Handles bad requests with 400_BAD_REQUEST"""
    message = str(error)
    app.logger.warning(message)
    return (
        jsonify(
            status=status.HTTP_400_BAD_REQUEST, error="Bad Request", message=message
        ),
        status.HTTP_400_BAD_REQUEST,
    )


@app.errorhandler(status.HTTP_404_NOT_FOUND)
def not_found(error):
    """Handles resources not found with 404_NOT_FOUND"""
    message = str(error)
    app.logger.warning(message)
    return (
        jsonify(status=status.HTTP_404_NOT_FOUND, error="Not Found", message=message),
        status.HTTP_404_NOT_FOUND,
    )


@app.errorhandler(status.HTTP_405_METHOD_NOT_ALLOWED)
def method_not_supported(error):
    """Handles unsupported HTTP methods with 405_METHOD_NOT_SUPPORTED"""
    message = str(error)
    app.logger.warning(message)
    return (
        jsonify(
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
            error="Method not Allowed",
            message=message,
        ),
        status.HTTP_405_METHOD_NOT_ALLOWED,
    )


@app.errorhandler(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
def mediatype_not_supported(error):
    """Handles unsupported media requests with 415_UNSUPPORTED_MEDIA_TYPE"""
    message = str(error)
    app.logger.warning(message)
    return (
        jsonify(
            status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            error="Unsupported media type",
            message=message,
        ),
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    )


@app.errorhandler(status.HTTP_500_INTERNAL_SERVER_ERROR)
def internal_server_error(error):
    """Handles unexpected server error with 500_SERVER_ERROR"""
    message = str(error)
    app.logger.error(message)
    return (
        jsonify(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message=message,
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@app.before_request
def before_request():
    """Before each request, get the request and log it"""
    info = {
        "url": request.url,
        "method": request.method,
        "headers": dict(request.headers),
        "body": request.data.decode("utf-8"),
        "args": request.args,
    }
    app.logger.debug(json.dumps(info))
