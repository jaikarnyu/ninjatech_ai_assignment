"""
Model for Users
"""
import logging
from enum import Enum
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from service.common.error_handlers import DataValidationError

logger = logging.getLogger("flask.app")

# Create the SQLAlchemy object to be initialized later in init_db()
db = SQLAlchemy()


def init_db(app):
    """Initialize the SQLAlchemy app"""
    Users.init_db(app)


class UserStatus(Enum):
    """Enumeration of valid User statuses"""

    CREATION_REQUEST_RECEIVED = "CREATION_REQUEST_RECEIVED"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Users(db.Model):
    """
    Class that represents a User

    This version uses a relational database for persistence which is hidden
    from us by SQLAlchemy's object relational mappings (ORM)
    """

    ##################################################
    # Table Schema
    ##################################################
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    email = db.Column(db.String(), nullable=False, unique=True)
    created_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    modified_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    active = db.Column(db.Boolean, nullable=False, default=True)
    status = db.Column(
        db.String(),
        nullable=False,
        default=UserStatus.CREATION_REQUEST_RECEIVED.value,
    )
    orders = db.relationship(
        "Orders",
        backref="users",
        lazy=True,
        order_by="desc(Orders.created_date)",
    )

    notifications = db.relationship(
        "Notifications",
        backref="users",
        lazy=True,
        order_by="desc(Notifications.created_date)",
    )

    ##################################################
    # INSTANCE METHODS
    ##################################################

    def __repr__(self):
        return f"<User {self.name} id=[{self.id}]>"

    def create(self):
        """
        Creates a User to the database
        """
        logger.info("Creating %s", self.name)
        # id must be none to generate next primary key
        self.id = None  # pylint: disable=invalid-name
        self.created_date = datetime.utcnow()
        self.modified_date = datetime.utcnow()
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as error:
            db.session.rollback()
            raise DataValidationError(str(error))

    def update(self):
        """
        Updates a User to the database
        """
        logger.info("Saving %s", self.name)
        if not self.id:
            raise DataValidationError("Update called with empty ID field")
        self.modified_date = datetime.utcnow()
        try:
            db.session.commit()
        except Exception as error:
            db.session.rollback()
            raise DataValidationError(str(error))

    def delete(self):
        """Removes a User from the data store"""
        logger.info("Deleting %s", self.name)
        self.active = False
        self.modified_date = datetime.utcnow()
        try:
            db.session.commit()
        except Exception as error:
            db.session.rollback()
            raise DataValidationError(str(error))

    def serialize(self):
        """Serializes a User into a dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "created_date": self.created_date.isoformat(),
            "modified_date": self.modified_date.isoformat(),
            "active": self.active,
            "status": self.status
            
        }

    def deserialize(self, data: dict):
        """
        Deserializes a User from a dictionary
        Args:
            data (dict): A dictionary containing the User data
        """
        try:
            self.name = data["name"]
            self.email = data["email"]
            self.status = data.get("status", UserStatus.CREATION_REQUEST_RECEIVED.value)
            self.active = data.get("active", True)
            self.created_date = data.get("created_date", datetime.utcnow())
            self.modified_date = data.get("modified_date", datetime.utcnow())


        except AttributeError as error:
            raise DataValidationError("Invalid attribute: " + error.args[0]) from error
        except KeyError as error:
            raise DataValidationError(
                "Invalid User: missing " + error.args[0]
            ) from error
        except TypeError as error:
            raise DataValidationError(
                "Invalid User: body of request contained bad or no data " + str(error)
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
        """Returns all of the Users in the database"""
        logger.info("Processing all Users")
        return cls.query.filter(cls.active == True)

    @classmethod
    def find(cls, user_id: int):
        """Finds a User by it's ID

        :param user_id: the id of the User to find
        :type user_id: int

        :return: an instance with the user_id, or None if not found
        :rtype: User

        """
        logger.info("Processing lookup for id %s ...", user_id)
        return cls.query.get(user_id)

    @classmethod
    def find_or_404(cls, user_id: int):
        """Find a User by it's id

        :param user_id: the id of the User to find
        :type user_id: int

        :return: an instance with the user_id, or 404_NOT_FOUND if not found
        :rtype: User

        """
        logger.info("Processing lookup or 404 for id %s ...", user_id)
        return cls.query.get_or_404(user_id)

    @classmethod
    def find_by_name(cls, name: str) -> list:
        """Returns all Users with the given name

        :param name: the name of the Users you want to match
        :type name: str

        :return: a collection of Users with that name
        :rtype: list

        """
        logger.info("Processing name query for %s ...", name)
        return cls.query.filter(cls.name == name and cls.active == True)

    @classmethod
    def find_by_status(cls, status) -> list:
        """Returns all Users by their status

        :param status : UserStatus Enum
        :type UserStatus: Enum

        :return: a collection of Users that are available
        :rtype: list

        """
        logger.info("Processing status query for %s ...", status)
        return cls.query.filter(cls.status == status)

    @classmethod
    def find_by_email(cls, email: str) -> list:
        """Returns all Users with the given email

        :param email: the email of the Users you want to match
        :type email: str

        :return: a collection of Users with that email
        :rtype: list

        """
        logger.info("Processing email query for %s ...", email)
        return cls.query.filter(cls.email == email and cls.active == True).all()
