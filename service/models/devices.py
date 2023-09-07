"""
Model for Devices
"""
import logging
from enum import Enum
from datetime import date, datetime
from flask import Flask
from service.models.projects import db, DataValidationError


logger = logging.getLogger("flask.app")


def init_db(app):
    """Initialize the SQLAlchemy app"""
    Devices.init_db(app)


class DataValidationError(Exception):
    """Used for an data validation errors when deserializing"""


class DeviceStatus(Enum):
    """Enumeration of valid Device statuses"""

    CREATION_REQUEST_RECEIVED = "CREATION_REQUEST_RECEIVED"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Devices(db.Model):
    """
    Class that represents a Device

    This version uses a relational database for persistence which is hidden
    from us by SQLAlchemy's object relational mappings (ORM)
    """

    ##################################################
    # Table Schema
    ##################################################
    __tablename__ = "devices"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    project_id = db.Column(
        db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    created_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    modified_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    active = db.Column(db.Boolean, nullable=False, default=True)
    status = db.Column(
        db.String(),
        nullable=False,
        default=DeviceStatus.CREATION_REQUEST_RECEIVED.value,
    )

    ##################################################
    # INSTANCE METHODS
    ##################################################

    def __repr__(self):
        return f"<Device {self.name} id=[{self.id}]>"

    def create(self):
        """
        Creates a Device to the database
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
        Updates a Device to the database
        """
        logger.info("Saving %s", self.name)
        if not self.id:
            raise DataValidationError("Update called with empty ID field")
        self.modified_date = datetime.utcnow()
        db.session.commit()

    def delete(self):
        """Removes a Device from the data store"""
        logger.info("Deleting %s", self.name)
        self.active = False
        self.modified_date = datetime.utcnow()
        db.session.commit()

    def serialize(self):
        """Serializes a Device into a dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "project_id": self.project_id,
            "created_date": self.created_date.isoformat(),
            "modified_date": self.modified_date.isoformat(),
            "active": self.active,
            "status": self.status,
        }

    def deserialize(self, data: dict):
        """
        Deserializes a Device from a dictionary
        Args:
            data (dict): A dictionary containing the Device data
        """
        try:
            self.name = data["name"]
            self.project_id = data["project_id"]
            self.status = data.get(
                "status", DeviceStatus.CREATION_REQUEST_RECEIVED.value
            )
        except AttributeError as error:
            raise DataValidationError("Invalid attribute: " + error.args[0]) from error
        except KeyError as error:
            raise DataValidationError(
                "Invalid Device: missing " + error.args[0]
            ) from error
        except TypeError as error:
            raise DataValidationError(
                "Invalid Device: body of request contained bad or no data " + str(error)
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
        """Returns all of the Devices in the database"""
        logger.info("Processing all Devices")
        return cls.query.filter(cls.active == True)

    @classmethod
    def find(cls, device_id: int):
        """Finds a Device by it's ID

        :param device_id: the id of the Device to find
        :type device_id: int

        :return: an instance with the device_id, or None if not found
        :rtype: Device

        """
        logger.info("Processing lookup for id %s ...", device_id)
        return cls.query.get(device_id)

    @classmethod
    def find_or_404(cls, device_id: int):
        """Find a Device by it's id

        :param device_id: the id of the Device to find
        :type device_id: int

        :return: an instance with the device_id, or 404_NOT_FOUND if not found
        :rtype: Device

        """
        logger.info("Processing lookup or 404 for id %s ...", device_id)
        return cls.query.get_or_404(device_id)

    @classmethod
    def find_by_project_id(cls, project_id: int) -> list:
        """Returns all Devices with the given project id

        :param project_id : the project_id of the Devices you want to match
        :type project_id: int

        :return: a collection of Devices with that project_id
        :rtype: list

        """
        logger.info("Processing project_id query for %s ...", project_id)
        return cls.query.filter(cls.project_id == project_id and cls.active is True)

    @classmethod
    def find_by_status(cls, status) -> list:
        """Returns all Devices by their status

        :param status : DeviceStatus Enum
        :type DeviceStatus: Enum

        :return: a collection of Devices that are available
        :rtype: list

        """
        logger.info("Processing status query for %s ...", status)
        return cls.query.filter(cls.status == status)
