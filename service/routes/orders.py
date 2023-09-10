"""
Orders Service

GET /api/orders - Returns a list all of the orders
GET /api/orders/{id} - Returns the order with a given id number
POST /api/orders - creates a new order record in the database
PUT /api/orders/{id} - updates a order record in the database
DELETE /api/orders/{id} - deletes a order record in the database

"""
from flask import jsonify, request, abort
from service.common import status  # HTTP Status Codes
from service import app
from service.models.orders import Orders
from flask_restx import Api, Resource, fields, reqparse
from service.routes.users import API
from service.tasks.send_notification import send_notification
from service.models.notifications import NotificationType
import service.config as config
from datetime import datetime

"""
flask-restx model for service.models.orders.Orders
"""
ORDERS_MODEL = API.model(
    "Orders",
    {
        "id": fields.Integer(
            readOnly=True,
            required=False,
            description="The unique id assigned internally by service",
        ),
        "user_id": fields.Integer(
            required=True, description="The user id of the order"
        ),
        "name": fields.String(required=True, description="The name of the order"),
        "created_date": fields.DateTime(
            required=False,
            description="The created timestamp of the order",
        ),
        "modified_date": fields.DateTime(
            required=False,
            description="The modified timestamp of the order",
        ),
        "status": fields.String(
            required=False,
            description="The status of the order",
        ),
        "active": fields.Boolean(
            required=False, description="Active status of the order", default=True
        ),
        "send_notification": fields.Boolean(
            required=False,
            description="Send notification for the order",
            default=True,
        ),
    },
)

ORDER_QUERY_PARSER = reqparse.RequestParser()
ORDER_QUERY_PARSER.add_argument(
    "order_id", type=int, required=False, help="Filter by order token"
)
ORDER_QUERY_PARSER.add_argument(
    "user_id", type=int, required=False, help="Filter by user token"
)

ORDER_QUERY_PARSER.add_argument(
    "status", type=str, required=False, help="Filter by order status"
)

ORDER_QUERY_PARSER.add_argument(
    "active", type=bool, required=False, help="Filter by active status"
)


######################################################################


@API.route("/orders/<int:order_id>")
@API.param("order_id", "The Order identifier")
@API.response(404, "Order not found")
class OrderResource(Resource):
    @API.doc("get_order")
    @API.marshal_with(ORDERS_MODEL)
    @API.response(404, "Order not found")
    def get(self, order_id):
        """Returns a single Order"""
        app.logger.info("Request for order with id: %s", order_id)
        order = Orders.find(order_id)
        if not order:
            abort(
                status.HTTP_404_NOT_FOUND,
                "Order with id '{}' was not found.".format(order_id),
            )
        return order.serialize(), status.HTTP_200_OK

    @API.doc("update_order")
    @API.expect(ORDERS_MODEL)
    @API.response(400, "The posted Order data was not valid")
    @API.response(404, "Order not found")
    @API.marshal_with(ORDERS_MODEL, code=200)
    def put(self, order_id):
        """Updates a Order"""
        app.logger.info("Request to update order with id: %s", order_id)
        check_content_type("application/json")
        order = Orders.find(order_id)
        if not order:
            abort(
                status.HTTP_404_NOT_FOUND,
                "Order with id '{}' was not found.".format(order_id),
            )
        data = request.get_json()
        order.deserialize(data)
        order.id = order_id
        order.update()
        app.logger.info("Order with id [%s] updated!", order.id)

        # Send notification
        if order.send_notification:
            user_id = order.user_id
            notification = (
                f"Order with id {order.id} has been updated. Status: {order.status}"
            )
            send_notification.apply_async(
                args=[
                    user_id,
                    NotificationType.EMAIL.value,
                    notification,
                    datetime.utcnow(),
                ],
                queue=config.CELERY_NOTIFICATIONS_QUEUE,
            )
        return order.serialize(), status.HTTP_200_OK

    @API.doc("delete_order")
    @API.response(204, "Order deleted")
    def delete(self, order_id):
        """Deletes a Order"""
        app.logger.info("Request to delete order with id: %s", order_id)
        order = Orders.find(order_id)
        if order:
            order.delete()
            app.logger.info("Order with id [%s] deleted!", order_id)

            # Send notification
            if order.send_notification:
                user_id = order.user_id
                notification = f"Order with id {order.id} has been cancelled."
                send_notification.apply_async(
                    args=[
                        user_id,
                        NotificationType.EMAIL.value,
                        notification,
                        datetime.utcnow(),
                    ],
                    queue=config.CELERY_NOTIFICATIONS_QUEUE,
                )
        return "", status.HTTP_204_NO_CONTENT


@API.route("/orders")
class OrderCollection(Resource):
    """Handles all interactions with collections of Orders"""

    @API.doc("list_orders")
    @API.expect(ORDER_QUERY_PARSER)
    @API.marshal_list_with(ORDERS_MODEL)
    def get(self):
        """Returns all of the Orders"""
        app.logger.info("Request for order list")
        orders = []
        args = request.args
        if len(args) > 0:
            orders = Orders.query.filter_by(**args)
        else:
            orders = Orders.all()

        results = [order.serialize() for order in orders]
        app.logger.info("Returning %d orders", len(results))
        return results, status.HTTP_200_OK

    @API.doc("create_order")
    @API.expect(ORDERS_MODEL)
    @API.response(400, "The posted Order data was not valid")
    @API.response(201, "Order created successfully")
    @API.marshal_with(ORDERS_MODEL, code=201)
    def post(self):
        """Creates a Order"""
        app.logger.info("Request to create a order")
        check_content_type("application/json")
        data = request.get_json()
        check_request_data(data)
        order = Orders()
        order.deserialize(data)
        order.create()
        app.logger.info("Order with new id [%s] saved!", order.id)

        # Send notification
        if order.send_notification:
            user_id = order.user_id
            notification = f"Order with id {order.id} has been created."
            send_notification.apply_async(
                args=[
                    user_id,
                    NotificationType.EMAIL.value,
                    notification,
                    datetime.utcnow(),
                ],
                queue=config.CELERY_NOTIFICATIONS_QUEUE,
            )

        return order.serialize(), status.HTTP_201_CREATED


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################

def check_request_data(data):

    # Check if user id is present
    if "user_id" not in data or "name" not in data:
            abort(
                status.HTTP_400_BAD_REQUEST,
                "The posted data is not in JSON format or missing user_id or name",
            )
        
    # Check if email and name are strings
    if not isinstance(data["user_id"], int) or not isinstance(data["name"], str):
        abort(
            status.HTTP_400_BAD_REQUEST,
            "User_id must be int and name must be string",
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
