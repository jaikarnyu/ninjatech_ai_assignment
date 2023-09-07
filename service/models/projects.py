"""
Model for Projects
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
    Projects.init_db(app)


class ProjectStatus(Enum):
    """Enumeration of valid Project statuses"""

    CREATION_REQUEST_RECEIVED = "CREATION_REQUEST_RECEIVED"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Projects(db.Model):
    """
    Class that represents a Project

    This version uses a relational database for persistence which is hidden
    from us by SQLAlchemy's object relational mappings (ORM)
    """

    ##################################################
    # Table Schema
    ##################################################
    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    created_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    modified_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    active = db.Column(db.Boolean, nullable=False, default=True)
    status = db.Column(
        db.String(),
        nullable=False,
        default=ProjectStatus.CREATION_REQUEST_RECEIVED.value,
    )
    project_memberships = db.relationship(
        "ProjectMemberships",
        backref="projects",
        lazy=True,
        order_by="desc(ProjectMemberships.created_date)",
    )

    devices = db.relationship(
        "Devices",
        backref="projects",
        lazy=True,
        order_by="desc(Devices.created_date)",
    )

    ##################################################
    # INSTANCE METHODS
    ##################################################

    def __repr__(self):
        return f"<Project {self.name} id=[{self.id}]>"

    def create(self):
        """
        Creates a Project to the database
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
        Updates a Project to the database
        """
        logger.info("Saving %s", self.name)
        if not self.id:
            raise DataValidationError("Update called with empty ID field")
        self.modified_date = datetime.utcnow()
        db.session.commit()

    def delete(self):
        """Removes a Project from the data store"""
        logger.info("Deleting %s", self.name)
        self.active = False
        self.modified_date = datetime.utcnow()
        db.session.commit()

    def serialize(self):
        """Serializes a Project into a dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "created_date": self.created_date.isoformat(),
            "modified_date": self.modified_date.isoformat(),
            "active": self.active,
            "status": self.status,
            "project_memberships": self.project_memberships,
            "devices": self.devices,
        }

    def deserialize(self, data: dict):
        """
        Deserializes a Project from a dictionary
        Args:
            data (dict): A dictionary containing the Project data
        """
        try:
            self.name = data["name"]
            self.status = data.get(
                "status", ProjectStatus.CREATION_REQUEST_RECEIVED.value
            )
        except AttributeError as error:
            raise DataValidationError("Invalid attribute: " + error.args[0]) from error
        except KeyError as error:
            raise DataValidationError(
                "Invalid Project: missing " + error.args[0]
            ) from error
        except TypeError as error:
            raise DataValidationError(
                "Invalid Project: body of request contained bad or no data "
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
        """Returns all of the Projects in the database"""
        logger.info("Processing all Projects")
        return cls.query.filter(cls.active == True)

    @classmethod
    def find(cls, project_id: int):
        """Finds a Project by it's ID

        :param project_id: the id of the Project to find
        :type project_id: int

        :return: an instance with the project_id, or None if not found
        :rtype: Project

        """
        logger.info("Processing lookup for id %s ...", project_id)
        return cls.query.get(project_id)

    @classmethod
    def find_or_404(cls, project_id: int):
        """Find a Project by it's id

        :param project_id: the id of the Project to find
        :type project_id: int

        :return: an instance with the project_id, or 404_NOT_FOUND if not found
        :rtype: Project

        """
        logger.info("Processing lookup or 404 for id %s ...", project_id)
        return cls.query.get_or_404(project_id)

    @classmethod
    def find_by_name(cls, name: str) -> list:
        """Returns all Projects with the given name

        :param name: the name of the Projects you want to match
        :type name: str

        :return: a collection of Projects with that name
        :rtype: list

        """
        logger.info("Processing name query for %s ...", name)
        return cls.query.filter(cls.name == name and cls.active == True)

    @classmethod
    def find_by_status(cls, status) -> list:
        """Returns all Projects by their status

        :param status : ProjectStatus Enum
        :type ProjectStatus: Enum

        :return: a collection of Projects that are available
        :rtype: list

        """
        logger.info("Processing status query for %s ...", status)
        return cls.query.filter(cls.status == status)
