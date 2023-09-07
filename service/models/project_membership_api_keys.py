"""
Model for ProjectMembershipApiKeys
"""
import logging
from enum import Enum
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
import uuid
from service.models.projects import db, DataValidationError


logger = logging.getLogger("flask.app")


def init_db(app):
    """Initialize the SQLAlchemy app"""
    ProjectMembershipApiKeys.init_db(app)


class DataValidationError(Exception):
    """Used for an data validation errors when deserializing"""


class ProjectMembershipApiKeyStatus(Enum):
    """Enumeration of valid ProjectMembershipApiKey statuses"""

    CREATION_REQUEST_RECEIVED = "CREATION_REQUEST_RECEIVED"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class ProjectMembershipApiKeys(db.Model):
    """
    Class that represents a ProjectMembershipApiKey

    This version uses a relational database for persistence which is hidden
    from us by SQLAlchemy's object relational mappings (ORM)
    """

    ##################################################
    # Table Schema
    ##################################################
    __tablename__ = "project_membership_api_keys"
    id = db.Column(db.Integer, primary_key=True)
    project_membership_id = db.Column(
        db.Integer,
        db.ForeignKey("project_memberships.id", ondelete="CASCADE"),
        index=True,
    )
    secret = db.Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    created_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    modified_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    active = db.Column(db.Boolean, nullable=False, default=True)
    status = db.Column(
        db.String(),
        nullable=False,
        default=ProjectMembershipApiKeyStatus.CREATION_REQUEST_RECEIVED.value,
    )

    ##################################################
    # INSTANCE METHODS
    ##################################################

    def __repr__(self):
        return f"<ProjectMembershipApiKey {self.project_membership_id} id=[{self.id}]>"

    def create(self):
        """
        Creates a ProjectMembershipApiKey to the database
        """
        logger.info("Creating %s", self.project_membership_id)
        # id must be none to generate next primary key
        self.id = None
        self.created_date = datetime.utcnow()
        self.modified_date = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    def update(self):
        """
        Updates a ProjectMembershipApiKey to the database
        """
        logger.info("Saving %s", self.project_membership_id)
        if not self.id:
            raise DataValidationError("Update called with empty ID field")
        self.modified_date = datetime.utcnow()
        db.session.commit()

    def delete(self):
        """Removes a ProjectMembershipApiKey from the data store"""
        logger.info(
            f"Deleting api key for project_membership_id : {self.project_membership_id}"
        )
        self.active = False
        self.modified_date = datetime.utcnow()
        db.session.commit()

    def serialize(self):
        """Serializes a ProjectMembershipApiKey into a dictionary"""
        return {
            "id": self.id,
            "project_membership_id": self.project_membership_id,
            "secret": self.secret,
            "created_date": self.created_date.isoformat(),
            "modified_date": self.modified_date.isoformat(),
            "active": self.active,
            "status": self.status,
        }

    def deserialize(self, data: dict):
        """
        Deserializes a ProjectMembershipApiKey from a dictionary
        Args:
            data (dict): A dictionary containing the ProjectMembershipApiKey data
        """
        try:
            self.project_membership_id = data["project_membership_id"]
            self.status = data.get(
                "status", ProjectMembershipApiKeyStatus.CREATION_REQUEST_RECEIVED.value
            )
        except AttributeError as error:
            raise DataValidationError("Invalid attribute: " + error.args[0]) from error
        except KeyError as error:
            raise DataValidationError(
                "Invalid ProjectMembershipApiKey: missing " + error.args[0]
            ) from error
        except TypeError as error:
            raise DataValidationError(
                "Invalid ProjectMembershipApiKey: body of request contained bad or no data "
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
        """Returns all of the ProjectMembershipApiKeys in the database"""
        logger.info("Processing all ProjectMembershipApiKeys")
        return cls.query.filter(cls.active == True)

    @classmethod
    def find(cls, id: int):
        """Finds a ProjectMembershipApiKey by it's ID

        :param id: the id of the ProjectMembershipApiKey to find
        :type id: int

        :return: an instance with the id, or None if not found
        :rtype: ProjectMembershipApiKey

        """
        logger.info("Processing lookup for id %s ...", id)
        return cls.query.get(id)

    @classmethod
    def find_or_404(cls, id: int):
        """Find a ProjectMembershipApiKey by it's id

        :param id: the id of the ProjectMembershipApiKey to find
        :type id: int

        :return: an instance with the id, or 404_NOT_FOUND if not found
        :rtype: ProjectMembershipApiKey

        """
        logger.info("Processing lookup or 404 for id %s ...", id)
        return cls.query.get_or_404(id)

    @classmethod
    def find_by_membership_id(cls, project_membership_id: int) -> list:
        """Returns all ProjectMembershipApiKeys with the given project_membership_id

        :param project_membership_id: the project_membership_id of the ProjectMembershipApiKeys you want to match
        :type project_membership_id: int

        :return: a collection of ProjectMembershipApiKeys with that project_membership_id
        :rtype: list

        """
        logger.info(
            "Processing project_membership_id query for %s ...", project_membership_id
        )
        return cls.query.filter(
            cls.project_membership_id == project_membership_id and cls.active is True
        )

    @classmethod
    def find_by_status(cls, status) -> list:
        """Returns all ProjectMembershipApiKeys by their status

        :param status : ProjectMembershipApiKeyStatus Enum
        :type ProjectMembershipApiKeyStatus: Enum

        :return: a collection of ProjectMembershipApiKeys that are available
        :rtype: list

        """
        logger.info("Processing status query for %s ...", status)
        return cls.query.filter(cls.status == status)

    @classmethod
    def find_by_api_key(cls, secret):
        """Returns project_membership_id by their secret

        :param secret : secret
        :type secret: str

        :return: project_membership_id
        :rtype: int

        """
        logger.info("Processing secret query for %s ...", secret)
        return cls.query.filter(cls.secret == secret).first().project_membership_id
