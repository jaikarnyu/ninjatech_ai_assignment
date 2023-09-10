"""
Users Service

"""
from flask import jsonify, request, abort
from service.common import status  # HTTP Status Codes
from service import app
from service.models.users import Users
from flask_restx import Api, Resource, fields, reqparse

# TODO Encrypt API keys
API = Api(
    app,
    version="1.0.0",
    title="Ninjatech REST API Service",
    description="This service contains Users, Orders and Notifications.",
    default="NINJATECH",
    default_label="Ninjatech operations",
    doc="/",
    prefix="/api",
)

"""
flask-restx model for service.models.users.Users
"""
USERS_MODEL = API.model(
    "Users",
    {
        "id": fields.Integer(
            readOnly=True,
            required=False,
            description="The unique id assigned internally by service",
        ),
        "email": fields.String(
            required=True, description="The email address of the user"
        ),
        "name": fields.String(required=True, description="The name of the user"),
        "created_date": fields.DateTime(
            required=False,
            description="The created timestamp of the user",
        ),
        "modified_date": fields.DateTime(
            required=False,
            description="The modified timestamp of the user",
        ),
        "status": fields.String(
            required=False,
            description="The status of the user",
        ),
        "active": fields.Boolean(
            required=False, description="Active status of the user", default=True
        ),
    },
)

USER_QUERY_PARSER = reqparse.RequestParser()
USER_QUERY_PARSER.add_argument(
    "user_id", type=int, required=False, help="Filter by user token"
)
USER_QUERY_PARSER.add_argument(
    "email", type=str, required=False, help="Filter by user email"
)

USER_QUERY_PARSER.add_argument(
    "status", type=str, required=False, help="Filter by user status"
)

USER_QUERY_PARSER.add_argument(
    "active", type=bool, required=False, help="Filter by active status"
)


######################################################################
# GET HEALTH CHECK
######################################################################
@app.route("/health")
def healthcheck():
    """Let them know our heart is still beating"""
    return jsonify(status=200, message="Healthy"), status.HTTP_200_OK


######################################################################


@API.route("/users/<int:user_id>")
@API.param("user_id", "The User identifier")
@API.response(404, "User not found")
class UserResource(Resource):
    @API.doc("get_user")
    @API.marshal_with(USERS_MODEL)
    @API.response(404, "User not found")
    def get(self, user_id):
        """Returns a single User"""
        app.logger.info("Request for user with id: %s", user_id)
        user = Users.find(user_id)
        if not user:
            abort(
                status.HTTP_404_NOT_FOUND,
                "User with id '{}' was not found.".format(user_id),
            )
        return user.serialize(), status.HTTP_200_OK

    @API.doc("update_user")
    @API.expect(USERS_MODEL)
    @API.response(400, "The posted User data was not valid")
    @API.response(404, "User not found")
    @API.marshal_with(USERS_MODEL, code=200)
    def put(self, user_id):
        """Updates a User"""
        app.logger.info("Request to update user with id: %s", user_id)
        check_content_type("application/json")
        user = Users.find(user_id)
        if not user:
            abort(
                status.HTTP_404_NOT_FOUND,
                "User with id '{}' was not found.".format(user_id),
            )
        data = request.get_json()
        user.deserialize(data)
        user.id = user_id
        user.update()
        return user.serialize(), status.HTTP_200_OK

    @API.doc("delete_user")
    @API.response(204, "User deleted")
    def delete(self, user_id):
        """Deletes a User"""
        app.logger.info("Request to delete user with id: %s", user_id)
        user = Users.find(user_id)
        if user:
            user.delete()
        return "", status.HTTP_204_NO_CONTENT


@API.route("/users")
class UserCollection(Resource):
    """Handles all interactions with collections of Users"""

    @API.doc("list_users")
    @API.expect(USER_QUERY_PARSER)
    @API.marshal_list_with(USERS_MODEL)
    def get(self):
        """Returns all of the Users"""
        app.logger.info("Request for user list")
        users = []
        args = request.args
        if len(args) > 0:
            users = Users.query.filter_by(**args)
        else:
            users = Users.all()

        results = [user.serialize() for user in users]
        app.logger.info("Returning %d users", len(results))
        return results, status.HTTP_200_OK

    @API.doc("create_user")
    @API.expect(USERS_MODEL)
    @API.response(400, "The posted User data was not valid")
    @API.response(201, "User created successfully")
    @API.marshal_with(USERS_MODEL, code=201)
    def post(self):
        """Creates a User"""
        app.logger.info("Request to create a user")
        check_content_type("application/json")
        data = request.get_json()
        # Validate the data in the request
        if "email" not in data or "name" not in data:
            abort(
                status.HTTP_400_BAD_REQUEST,
                "The posted data is not in JSON format or missing email or name",
            )
        
        # Check if email and name are strings
        if not isinstance(data["email"], str) or not isinstance(data["name"], str):
            abort(
                status.HTTP_400_BAD_REQUEST,
                "Email and name must be strings",
            )

        user = Users.find_by_email(email=data["email"])
        if not user:
            user = Users()
            user.deserialize(data)
            user.create()
            app.logger.info("User with new id [%s] saved!", user.id)

        else:
            app.logger.info("User with email [%s] already exists!", user.email)

        return user.serialize(), status.HTTP_201_CREATED


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


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
