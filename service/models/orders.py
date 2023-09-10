"""
Model for Orders
"""
import logging
from enum import Enum
from datetime import date, datetime
from flask import Flask
from service.models.users import db, DataValidationError


logger = logging.getLogger("flask.app")


def init_db(app):
    """Initialize the SQLAlchemy app"""
    Orders.init_db(app)


class DataValidationError(Exception):
    """Used for an data validation errors when deserializing"""


class OrderStatus(Enum):
    """Enumeration of valid Order statuses"""

    CREATION_REQUEST_RECEIVED = "CREATION_REQUEST_RECEIVED"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Orders(db.Model):
    """
    Class that represents a Order

    This version uses a relational database for persistence which is hidden
    from us by SQLAlchemy's object relational mappings (ORM)
    """

    ##################################################
    # Table Schema
    ##################################################
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    send_notification = db.Column(db.Boolean, nullable=False, default=True)
    created_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    modified_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    active = db.Column(db.Boolean, nullable=False, default=True)
    status = db.Column(
        db.String(),
        nullable=False,
        default=OrderStatus.CREATION_REQUEST_RECEIVED.value,
    )

    ##################################################
    # INSTANCE METHODS
    ##################################################

    def __repr__(self):
        return f"<Order {self.name} id=[{self.id}]>"

    def create(self):
        """
        Creates a Order to the database
        """
        logger.info("Creating %s", self.name)
        # id must be none to generate next primary key
        self.id = None  # pylint: disable=invalid-name
        self.created_date = datetime.utcnow()
        self.modified_date = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    def update(self):
        """
        Updates a Order to the database
        """
        logger.info("Saving %s", self.name)
        if not self.id:
            raise DataValidationError("Update called with empty ID field")
        self.modified_date = datetime.utcnow()
        db.session.commit()

    def delete(self):
        """Removes a Order from the data store"""
        logger.info("Deleting %s", self.name)
        self.active = False
        self.modified_date = datetime.utcnow()
        db.session.commit()

    def serialize(self):
        """Serializes a Order into a dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "user_id": self.user_id,
            "created_date": self.created_date.isoformat(),
            "modified_date": self.modified_date.isoformat(),
            "active": self.active,
            "status": self.status,
            "send_notification": self.send_notification,
        }

    def deserialize(self, data: dict):
        """
        Deserializes a Order from a dictionary
        Args:
            data (dict): A dictionary containing the Order data
        """
        try:
            self.name = data["name"]
            self.user_id = data["user_id"]
            self.status = data.get(
                "status", OrderStatus.CREATION_REQUEST_RECEIVED.value
            )
            self.send_notification = data.get("send_notification", True)
            self.created_date = data.get("created_date", datetime.utcnow())
            self.modified_date = data.get("modified_date", datetime.utcnow())
        except AttributeError as error:
            raise DataValidationError("Invalid attribute: " + error.args[0]) from error
        except KeyError as error:
            raise DataValidationError(
                "Invalid Order: missing " + error.args[0]
            ) from error
        except TypeError as error:
            raise DataValidationError(
                "Invalid Order: body of request contained bad or no data " + str(error)
            ) from error
        except ValueError as error:
            raise DataValidationError(
                "Invalid Webbot: body of request contained bad or no data " + str(error)
            ) from error
        return self

    ##################################################
    # CLASS METHODS
    ##################################################

    @classmethod
    def init_db(cls, app: Flask):
        """Initializes the database session

        :param app: the Flask app
        :type data: Flask

        """
        logger.info("Initializing database")
        # This is where we initialize SQLAlchemy from the Flask app
        # db.init_app(app)
        app.app_context().push()
        db.create_all()  # make our sqlalchemy tables

    @classmethod
    def all(cls) -> list:
        """Returns all of the Orders in the database"""
        logger.info("Processing all Orders")
        return cls.query.filter(cls.active == True)

    @classmethod
    def find(cls, device_id: int):
        """Finds a Order by it's ID

        :param device_id: the id of the Order to find
        :type device_id: int

        :return: an instance with the device_id, or None if not found
        :rtype: Order

        """
        logger.info("Processing lookup for id %s ...", device_id)
        return cls.query.get(device_id)

    @classmethod
    def find_or_404(cls, device_id: int):
        """Find a Order by it's id

        :param device_id: the id of the Order to find
        :type device_id: int

        :return: an instance with the device_id, or 404_NOT_FOUND if not found
        :rtype: Order

        """
        logger.info("Processing lookup or 404 for id %s ...", device_id)
        return cls.query.get_or_404(device_id)

    @classmethod
    def find_by_user_id(cls, user_id: int) -> list:
        """Returns all Orders with the given user id

        :param user_id : the user_id of the Orders you want to match
        :type user_id: int

        :return: a collection of Orders with that user_id
        :rtype: list

        """
        logger.info("Processing user_id query for %s ...", user_id)
        return cls.query.filter(cls.user_id == user_id and cls.active is True)

    @classmethod
    def find_by_status(cls, status) -> list:
        """Returns all Orders by their status

        :param status : OrderStatus Enum
        :type OrderStatus: Enum

        :return: a collection of Orders that are available
        :rtype: list

        """
        logger.info("Processing status query for %s ...", status)
        return cls.query.filter(cls.status == status)
