"""
Firmware events Service
"""
from flask import jsonify, request, abort
from service.common import status  # HTTP Status Codes
import service.config as config
import os
import traceback
from service import app
import re
from datetime import datetime
from service.tasks.device_firmware_events import save_firmware_events_to_db
from service.models.projects import Projects
from service.models.device_firmware_events import DeviceFirmwareEvents
from service.models.device_api_keys import DeviceApiKeys
from service.models.devices import Devices
from service.models.project_membership_api_keys import ProjectMembershipApiKeys
from service.models.project_memberships import ProjectMemberships
from flask_restx import Api, Resource, fields, reqparse
import uuid

# TODO Encrypt API keys
API = Api(
    app,
    version="1.0.0",
    title="Firmware Events service",
    description="Firmware Events server for MemFault",
    default="Events",
    default_label="Events-Operations",
    doc="/",
    prefix="/api",
)

"""
flask-restx model for service.models.device_firmware_events.DeviceFirmwareEvents
"""
FIRMWARE_EVENTS_MODEL = API.model(
    "Events",
    {
        "id": fields.Integer(
            readOnly=True,
            required=False,
            description="The unique id assigned internally by service",
        ),
        "device_id": fields.Integer(
            required=True, description="The device id of the events"
        ),
        "version": fields.String(
            required=True, description="The firmware version of the events"
        ),
        "created_date": fields.DateTime(
            required=False,
            description="The created at of the events",
        ),
        "modified_date": fields.DateTime(
            required=False,
            description="The updated at of the events",
        ),
        "status": fields.String(
            required=False,
            description="The status of the events",
        ),
        "active": fields.Boolean(
            required=False, description="The active status of the events", default=True
        ),
    },
)


FIRMWARE_UPDATE_EVENT_QUERY_PARSER = API.parser()
FIRMWARE_UPDATE_EVENT_QUERY_PARSER.add_argument(
    "X-Device-Api-Key", location="headers", required=True
)
FIRMWARE_UPDATE_EVENT_QUERY_PARSER.add_argument(
    "version",
    type="str",
    required=True,
    location="json",
    help="The firmware version of the device",
    default="0.0.0",
)
FIRMWARE_UPDATE_EVENT_QUERY_PARSER.add_argument(
    "timestamp", type=int, required=True, location="json", help="Epoch timestamp"
)


FIRMWARE_EVENTS_QUERY_PARSER = reqparse.RequestParser()
FIRMWARE_EVENTS_QUERY_PARSER.add_argument(
    "device_id", type=int, required=False, help="Filter by device id"
)
FIRMWARE_EVENTS_QUERY_PARSER.add_argument(
    "X-Project-Membership-Api-Key",
    location="headers",
    help="Member API Key",
    required=True,
)


######################################################################
# GET HEALTH CHECK
######################################################################
@app.route("/healthcheck")
def healthcheck():
    """Let them know our heart is still beating"""
    return jsonify(status=200, message="Healthy"), status.HTTP_200_OK


######################################################################


@API.route("/firmware")
class FirmwareEventsResource(Resource):
    """Resource for Firmware Events"""

    @API.doc("list_firmware_events")
    @API.expect(FIRMWARE_EVENTS_QUERY_PARSER)
    @API.marshal_with(FIRMWARE_EVENTS_MODEL)
    @API.response(400, "Bad Request. Invalid request data")
    @API.response(401, "Unauthorized request")
    @API.response(404, "Device/Member not found")
    @API.response(200, "Success")
    @API.response(500, "Internal Server Error")
    def get(self):
        """Returns a list of firmware events for device id"""
        app.logger.info("Request to list firmware events")

        # Check if device id is provided
        device_id = check_device_id()

        # Check if member has access to device
        check_membership_access(device_id)

        # Get the firmware events from the database
        firmware_events = DeviceFirmwareEvents.find_by_device_id(device_id)
        results = [event.serialize() for event in firmware_events]
        app.logger.debug("Returning %d events", len(results))
        return results, status.HTTP_200_OK

    @API.doc("create_firmware_event")
    @API.expect(FIRMWARE_UPDATE_EVENT_QUERY_PARSER)
    @API.response(202, "Update Accepted")
    @API.response(400, "Bad Request. Invalid request data")
    @API.response(401, "Unauthorized request")
    @API.response(404, "Device not found")
    @API.response(500, "Internal Server Error")
    def post(self):
        """Creates a Firmware Event"""
        app.logger.info("Request to create a firmware update event")
        # Validate the request
        check_content_type("application/json")
        device_id = check_device_api_key()
        version = check_version()
        timestamp = check_timestamp()

        # Send a message to save the firmware event task queue
        queue_name = "save_firmware_events_to_db"
        save_firmware_events_to_db.apply_async(
            (device_id, timestamp, version), queue=queue_name
        )

        return {"message": "Update Accepted."}, status.HTTP_202_ACCEPTED


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


def check_timestamp():
    """Checks if valid timestamp exists in request"""

    try:
        # Check if timestamp is provided
        timestamp = request.get_json().get("timestamp")
        if not timestamp:
            abort(
                status.HTTP_400_BAD_REQUEST,
                "No timestamp provided",
            )
        # Convert the epoch timestamp to a datetime object
        datetime_ts = datetime.fromtimestamp(timestamp)
        return datetime_ts
    except Exception as error:
        app.logger.error(f"Invalid epoch timestamp {timestamp} Error {error}")
        abort(
            status.HTTP_400_BAD_REQUEST,
            "Invalid format for provided timestamp",
        )


def check_version():
    """Checks if version follows semantic versioning"""
    # Check if version is provided
    version = request.get_json().get("version")
    if not version:
        abort(
            status.HTTP_400_BAD_REQUEST,
            "No version provided",
        )
    # Check if version follows semantic versioning
    if not re.match(r"^\d+\.\d+\.\d+$", version):
        app.logger.error("Invalid version: %s", version)
        abort(status.HTTP_400_BAD_REQUEST, f"Invalid version: {version}")

    return version


def check_device_api_key():
    """Checks if device api key exists"""
    # Check if device secret is provided
    device_secret = request.headers.get("X-Device-Api-Key")
    if not device_secret:
        app.logger.error("No device secret provided")
        abort(
            status.HTTP_401_UNAUTHORIZED,
            "Access denied. Unauthorized request",
        )

    # Check if device secret is valid uuid
    try:
        device_secret = uuid.UUID(device_secret)
    except Exception as error:
        app.logger.error(f"Invalid uuid {device_secret} Error {error}")
        abort(
            status.HTTP_401_UNAUTHORIZED,
            "Access denied. Invalid device key",
        )

    # Check if device exists
    device_id = DeviceApiKeys.find_by_api_key(device_secret)
    if not device_id:
        app.logger.error("Device not found")
        abort(
            status.HTTP_404_NOT_FOUND,
            "Device not found",
        )

    return device_id


def check_device_id():
    # Check if device id is provided
    device_id = request.args.get("device_id")

    # If device id is null or not an int return 400
    if not device_id:
        app.logger.error("No device id provided")
        abort(
            status.HTTP_400_BAD_REQUEST,
            "No Device id provided",
        )

    # Check if device id is an int
    try:
        device_id = int(device_id)
    except Exception as error:
        app.logger.error(f"Invalid device id {device_id} Error {error}")
        abort(
            status.HTTP_400_BAD_REQUEST,
            "Invalid device id",
        )

    return device_id


def check_membership_access(device_id):
    """Checks if member has access to device"""

    # Check if member secret is provided
    member_secret = request.headers.get("X-Project-Membership-Api-Key")
    if not member_secret:
        app.logger.error("No member secret provided")
        abort(
            status.HTTP_401_UNAUTHORIZED,
            "Access Denied. Unauthorized request",
        )

    # Check if member secret is valid uuid
    try:
        member_secret = uuid.UUID(member_secret)
    except Exception as error:
        app.logger.error(f"Invalid uuid {member_secret} Error {error}")
        abort(
            status.HTTP_401_UNAUTHORIZED,
            "Access Denied. Invalid membership api key",
        )

    # Check if member exists
    member_id = ProjectMembershipApiKeys.find_by_api_key(member_secret)
    if not member_id:
        app.logger.error("Member not found")
        abort(
            status.HTTP_404_NOT_FOUND,
            "Member not found",
        )

    # Check if member's project & device project are same
    member_project_id = ProjectMemberships.find_or_404(
        project_membership_id=member_id
    ).project_id
    device_project_id = Devices.find_or_404(device_id=device_id).project_id
    if member_project_id != device_project_id:
        app.logger.error("Member doesn't have access to device")
        abort(
            status.HTTP_401_UNAUTHORIZED,
            "Access denied. Member doesn't have access to device",
        )


def check_content_type(content_type):
    """Checks that the media type is correct"""
    if "Content-Type" not in request.headers:
        app.logger.error("No Content-Type specified.")
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Content-Type must be {content_type}",
        )

    if request.headers["Content-Type"] == content_type:
        return

    app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {content_type}",
    )
