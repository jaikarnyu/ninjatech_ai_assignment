"""
Model for DeviceFirmwareEvents
"""
import logging
from enum import Enum
from datetime import datetime
from flask import Flask
from service.models.projects import db, DataValidationError
from sqlalchemy.dialects.postgresql import UUID
import uuid

logger = logging.getLogger("flask.app")


def init_db(app):
    """Initialize the SQLAlchemy app"""
    DeviceFirmwareEvents.init_db(app)


class DataValidationError(Exception):
    """Used for an data validation errors when deserializing"""


class DeviceFirmwareEventStatus(Enum):
    """Enumeration of valid DeviceFirmwareEvent statuses"""

    CREATION_REQUEST_RECEIVED = "CREATION_REQUEST_RECEIVED"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class DeviceFirmwareEvents(db.Model):
    """
    Class that represents a DeviceFirmwareEvent

    This version uses a relational database for persistence which is hidden
    from us by SQLAlchemy's object relational mappings (ORM)
    """

    ##################################################
    # Table Schema
    ##################################################
    __tablename__ = "device_firmware_events"
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(
        db.Integer,
        db.ForeignKey("devices.id", ondelete="CASCADE"),
        index=True,
    )
    version = db.Column(db.String(80), nullable=False)
    created_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    modified_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    active = db.Column(db.Boolean, nullable=False, default=True)
    status = db.Column(
        db.String(),
        nullable=False,
        default=DeviceFirmwareEventStatus.CREATION_REQUEST_RECEIVED.value,
    )
    __table_args__ = (
        db.UniqueConstraint(
            device_id, version, created_date, name="device_version_timestamp"
        ),
    )

    ##################################################
    # INSTANCE METHODS
    ##################################################

    def __repr__(self):
        return f"<DeviceFirmwareEvent {self.device_id} id=[{self.id}]>"

    def create(self):
        """
        Creates a DeviceFirmwareEvent to the database
        """
        logger.info("Creating %s", self.device_id)
        # id must be none to generate next primary key
        self.id = None
        self.modified_date = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    def update(self):
        """
        Updates a DeviceFirmwareEvent to the database
        """
        logger.info("Saving %s", self.device_id)
        if not self.id:
            raise DataValidationError("Update called with empty ID field")
        self.modified_date = datetime.utcnow()
        db.session.commit()

    def delete(self):
        """Removes a DeviceFirmwareEvent from the data store"""
        logger.info(f"Deleting api key for device_id : {self.device_id}")
        self.active = False
        self.modified_date = datetime.utcnow()
        db.session.commit()

    def serialize(self):
        """Serializes a DeviceFirmwareEvent into a dictionary"""
        return {
            "id": self.id,
            "device_id": self.device_id,
            "version": self.version,
            "created_date": self.created_date.isoformat(),
            "modified_date": self.modified_date.isoformat(),
            "active": self.active,
            "status": self.status,
        }

    def deserialize(self, data: dict):
        """
        Deserializes a DeviceFirmwareEvent from a dictionary
        Args:
            data (dict): A dictionary containing the DeviceFirmwareEvent data
        """
        try:
            self.device_id = data["device_id"]
            self.status = data.get(
                "status", DeviceFirmwareEventStatus.CREATION_REQUEST_RECEIVED.value
            )
        except AttributeError as error:
            raise DataValidationError("Invalid attribute: " + error.args[0]) from error
        except KeyError as error:
            raise DataValidationError(
                "Invalid DeviceFirmwareEvent: missing " + error.args[0]
            ) from error
        except TypeError as error:
            raise DataValidationError(
                "Invalid DeviceFirmwareEvent: body of request contained bad or no data "
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
        """Returns all of the DeviceFirmwareEvents in the database"""
        logger.info("Processing all DeviceFirmwareEvents")
        return cls.query.filter(cls.active == True)

    @classmethod
    def find(cls, id: int):
        """Finds a DeviceFirmwareEvent by it's ID

        :param id: the id of the DeviceFirmwareEvent to find
        :type id: int

        :return: an instance with the id, or None if not found
        :rtype: DeviceFirmwareEvent

        """
        logger.info("Processing lookup for id %s ...", id)
        return cls.query.get(id)

    @classmethod
    def find_or_404(cls, id: int):
        """Find a DeviceFirmwareEvent by it's id

        :param id: the id of the DeviceFirmwareEvent to find
        :type id: int

        :return: an instance with the id, or 404_NOT_FOUND if not found
        :rtype: DeviceFirmwareEvent

        """
        logger.info("Processing lookup or 404 for id %s ...", id)
        return cls.query.get_or_404(id)

    @classmethod
    def find_by_device_id(cls, device_id: int) -> list:
        """Returns all DeviceFirmwareEvents with the given device_id

        :param device_id: the device_id of the DeviceFirmwareEvents you want to match
        :type device_id: int

        :return: a collection of DeviceFirmwareEvents with that device_id
        :rtype: list

        """
        logger.info("Processing device_id query for %s ...", device_id)
        return cls.query.filter(cls.device_id == device_id and cls.active is True)

    @classmethod
    def find_by_status(cls, status) -> list:
        """Returns all DeviceFirmwareEvents by their status

        :param status : DeviceFirmwareEventStatus Enum
        :type DeviceFirmwareEventStatus: Enum

        :return: a collection of DeviceFirmwareEvents that are available
        :rtype: list

        """
        logger.info("Processing status query for %s ...", status)
        return cls.query.filter(cls.status == status)
