"""
Model for Notifications
"""
import logging
from enum import Enum
from datetime import datetime
from flask import Flask
from service.models.users import db, DataValidationError
from sqlalchemy.dialects.postgresql import UUID
import uuid

logger = logging.getLogger("flask.app")


def init_db(app):
    """Initialize the SQLAlchemy app"""
    Notifications.init_db(app)


class DataValidationError(Exception):
    """Used for an data validation errors when deserializing"""


class NotificationStatus(Enum):
    """Enumeration of valid Notification statuses"""

    CREATION_REQUEST_RECEIVED = "CREATION_REQUEST_RECEIVED"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class NotificationType(Enum):
    """Enumeration of valid Notification type"""

    EMAIL = "EMAIL"
    SMS = "SMS"
    PUSH = "PUSH"


class Notifications(db.Model):
    """
    Class that represents a Notification

    This notification uses a relational database for persistence which is hidden
    from us by SQLAlchemy's object relational mappings (ORM)
    """

    ##################################################
    # Table Schema
    ##################################################
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    notification_type = db.Column(
        db.String(), nullable=False, default=NotificationType.EMAIL.value
    )
    notification = db.Column(db.String(), nullable=False)
    created_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    modified_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    active = db.Column(db.Boolean, nullable=False, default=True)
    status = db.Column(
        db.String(),
        nullable=False,
        default=NotificationStatus.CREATION_REQUEST_RECEIVED.value,
    )
    __table_args__ = (
        db.UniqueConstraint(
            user_id, notification, created_date, name="user_notification_timestamp"
        ),
    )

    ##################################################
    # INSTANCE METHODS
    ##################################################

    def __repr__(self):
        return f"<Notification {self.user_id} id=[{self.id}]>"

    def create(self):
        """
        Creates a Notification to the database
        """
        logger.info("Creating %s", self.user_id)
        # id must be none to generate next primary key
        self.id = None
        self.modified_date = datetime.utcnow()
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as error:
            db.session.rollback()
            raise DataValidationError(str(error))

    def update(self):
        """
        Updates a Notification to the database
        """
        logger.info("Saving %s", self.user_id)
        if not self.id:
            raise DataValidationError("Update called with empty ID field")
        self.modified_date = datetime.utcnow()
        try:
            db.session.commit()
        except Exception as error:
            db.session.rollback()
            raise DataValidationError(str(error))

    def delete(self):
        """Removes a Notification from the data store"""
        logger.info(f"Deleting api key for user_id : {self.user_id}")
        self.active = False
        self.modified_date = datetime.utcnow()
        try:
            db.session.commit()
        except Exception as error:
            db.session.rollback()
            raise DataValidationError(str(error))

    def serialize(self):
        """Serializes a Notification into a dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "notification": self.notification,
            "notification_type": self.notification_type,
            "created_date": self.created_date.isoformat(),
            "modified_date": self.modified_date.isoformat(),
            "active": self.active,
            "status": self.status,
        }

    def deserialize(self, data: dict):
        """
        Deserializes a Notification from a dictionary
        Args:
            data (dict): A dictionary containing the Notification data
        """
        try:
            self.user_id = data["user_id"]
            self.notification = data["notification"]
            self.status = data.get(
                "status", NotificationStatus.CREATION_REQUEST_RECEIVED.value
            )
            self.notification_type = data.get(
                "notification_type", NotificationType.EMAIL.value
            )
            self.created_date = data.get("created_date", datetime.utcnow())
            self.modified_date = data.get("modified_date", datetime.utcnow())
        except AttributeError as error:
            raise DataValidationError("Invalid attribute: " + error.args[0]) from error
        except KeyError as error:
            raise DataValidationError(
                "Invalid Notification: missing " + error.args[0]
            ) from error
        except TypeError as error:
            raise DataValidationError(
                "Invalid Notification: body of request contained bad or no data "
                + str(error)
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
        """Returns all of the Notifications in the database"""
        logger.info("Processing all Notifications")
        return cls.query.filter(cls.active == True)

    @classmethod
    def find(cls, id: int):
        """Finds a Notification by it's ID

        :param id: the id of the Notification to find
        :type id: int

        :return: an instance with the id, or None if not found
        :rtype: Notification

        """
        logger.info("Processing lookup for id %s ...", id)
        return cls.query.get(id)

    @classmethod
    def find_or_404(cls, id: int):
        """Find a Notification by it's id

        :param id: the id of the Notification to find
        :type id: int

        :return: an instance with the id, or 404_NOT_FOUND if not found
        :rtype: Notification

        """
        logger.info("Processing lookup or 404 for id %s ...", id)
        return cls.query.get_or_404(id)

    @classmethod
    def find_by_user_id(cls, user_id: int) -> list:
        """Returns all Notifications with the given user_id

        :param user_id: the user_id of the Notifications you want to match
        :type user_id: int

        :return: a collection of Notifications with that user_id
        :rtype: list

        """
        logger.info("Processing user_id query for %s ...", user_id)
        return cls.query.filter(cls.user_id == user_id and cls.active is True)

    @classmethod
    def find_by_status(cls, status) -> list:
        """Returns all Notifications by their status

        :param status : NotificationStatus Enum
        :type NotificationStatus: Enum

        :return: a collection of Notifications that are available
        :rtype: list

        """
        logger.info("Processing status query for %s ...", status)
        return cls.query.filter(cls.status == status)
