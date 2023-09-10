"""
Notifications Service

GET /api/notifications - Returns a list all of the notifications
GET /api/notifications/{id} - Returns the notification with a given id number
POST /api/notifications - creates a new notification record in the database
PUT /api/notifications/{id} - updates a notification record in the database
DELETE /api/notifications/{id} - deletes a notification record in the database

"""
from flask import jsonify, request, abort
from service.common import status  # HTTP Status Codes
from service import app
from service.models.notifications import Notifications, NotificationType
from flask_restx import Api, Resource, fields, reqparse
from service.routes.users import API

"""
flask-restx model for service.models.notifications.Notifications
"""
NOTIFICATIONS_MODEL = API.model(
    "Notifications",
    {
        "id": fields.Integer(
            readOnly=True,
            required=False,
            description="The unique id assigned internally by service",
        ),
        "user_id": fields.Integer(
            required=True, description="The user id of the notification"
        ),
        "notification_type": fields.String(
            required=True,
            description="The type of the notification",
            default=NotificationType.EMAIL.value,
        ),
        "notification": fields.String(required=True, description="The notification"),
        "created_date": fields.DateTime(
            required=False,
            description="The created timestamp of the notification",
        ),
        "modified_date": fields.DateTime(
            required=False,
            description="The modified timestamp of the notification",
        ),
        "status": fields.String(
            required=False,
            description="The status of the notification",
        ),
        "active": fields.Boolean(
            required=False,
            description="Active status of the notification",
            default=True,
        ),
    },
)

NOTIFICATION_QUERY_PARSER = reqparse.RequestParser()
NOTIFICATION_QUERY_PARSER.add_argument(
    "notification_id", type=int, required=False, help="Filter by notification token"
)
NOTIFICATION_QUERY_PARSER.add_argument(
    "user_id", type=int, required=False, help="Filter by user id"
)

NOTIFICATION_QUERY_PARSER.add_argument(
    "status", type=str, required=False, help="Filter by notification status"
)


######################################################################


@API.route("/notifications/<int:notification_id>")
@API.param("notification_id", "The Notification identifier")
@API.response(404, "Notification not found")
class NotificationResource(Resource):
    @API.doc("get_notification")
    @API.marshal_with(NOTIFICATIONS_MODEL)
    @API.response(404, "Notification not found")
    def get(self, notification_id):
        """Returns a single Notification"""
        app.logger.info("Request for notification with id: %s", notification_id)
        notification = Notifications.find(notification_id)
        if not notification:
            abort(
                status.HTTP_404_NOT_FOUND,
                "Notification with id '{}' was not found.".format(notification_id),
            )
        return notification.serialize(), status.HTTP_200_OK

    @API.doc("update_notification")
    @API.expect(NOTIFICATIONS_MODEL)
    @API.response(400, "The posted Notification data was not valid")
    @API.response(404, "Notification not found")
    @API.marshal_with(NOTIFICATIONS_MODEL, code=200)
    def put(self, notification_id):
        """Updates a Notification"""
        app.logger.info("Request to update notification with id: %s", notification_id)
        check_content_type("application/json")
        notification = Notifications.find(notification_id)
        if not notification:
            abort(
                status.HTTP_404_NOT_FOUND,
                "Notification with id '{}' was not found.".format(notification_id),
            )
        data = request.get_json()
        notification.deserialize(data)
        notification.id = notification_id
        notification.update()
        return notification.serialize(), status.HTTP_200_OK

    @API.doc("delete_notification")
    @API.response(204, "Notification deleted")
    def delete(self, notification_id):
        """Deletes a Notification"""
        app.logger.info("Request to delete notification with id: %s", notification_id)
        notification = Notifications.find(notification_id)
        if notification:
            notification.delete()
        return "", status.HTTP_204_NO_CONTENT


@API.route("/notifications")
class NotificationCollection(Resource):
    """Handles all interactions with collections of Notifications"""

    @API.doc("list_notifications")
    @API.expect(NOTIFICATION_QUERY_PARSER)
    @API.marshal_list_with(NOTIFICATIONS_MODEL)
    def get(self):
        """Returns all of the Notifications"""
        app.logger.info("Request for notification list")
        notifications = []
        args = request.args
        if len(args) > 0:
            notifications = Notifications.query.filter_by(**args)
        else:
            notifications = Notifications.all()

        results = [notification.serialize() for notification in notifications]
        app.logger.info("Returning %d notifications", len(results))
        return results, status.HTTP_200_OK

    @API.doc("create_notification")
    @API.expect(NOTIFICATIONS_MODEL)
    @API.response(400, "The posted Notification data was not valid")
    @API.response(201, "Notification created successfully")
    @API.marshal_with(NOTIFICATIONS_MODEL, code=201)
    def post(self):
        """Creates a Notification"""
        app.logger.info("Request to create a notification")
        check_content_type("application/json")
        data = request.get_json()
        check_request_data(data)
        notification = Notifications()
        notification.deserialize(data)
        notification.create()
        app.logger.info("Notification with new id [%s] saved!", notification.id)
        return notification.serialize(), status.HTTP_201_CREATED


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################

def check_request_data(data):
    # Check if user id is present
    if "user_id" not in data or "notification" not in data:
            abort(
                status.HTTP_400_BAD_REQUEST,
                "The posted data is not in JSON format or missing user_id or notification",
            )
        
    # Check if email and name are strings
    if not isinstance(data["user_id"], int) or not isinstance(data["notification"], str):
        abort(
            status.HTTP_400_BAD_REQUEST,
            "User_id must be int and notification must be string",
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
