"""
Model for ProjectMemberships
"""
import logging
from enum import Enum
from datetime import datetime
from flask import Flask
from service.models.projects import db, DataValidationError


logger = logging.getLogger("flask.app")


def init_db(app):
    """Initialize the SQLAlchemy app"""
    ProjectMemberships.init_db(app)


class ProjectMembershipStatus(Enum):
    """Enumeration of valid ProjectMembership statuses"""

    CREATION_REQUEST_RECEIVED = "CREATION_REQUEST_RECEIVED"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class ProjectMemberships(db.Model):
    """
    Class that represents a ProjectMembership

    This version uses a relational database for persistence which is hidden
    from us by SQLAlchemy's object relational mappings (ORM)
    """

    ##################################################
    # Table Schema
    ##################################################
    __tablename__ = "project_memberships"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    email = db.Column(db.String(), nullable=False, index=True)
    created_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    modified_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    active = db.Column(db.Boolean, nullable=False, default=True)
    status = db.Column(
        db.String(),
        nullable=False,
        default=ProjectMembershipStatus.CREATION_REQUEST_RECEIVED.value,
    )

    ##################################################
    # INSTANCE METHODS
    ##################################################

    def __repr__(self):
        return f"<ProjectMembership {self.email} id=[{self.id}]>"

    def create(self):
        """
        Creates a ProjectMembership to the database
        """
        logger.info("Creating %s", self.email)
        # id must be none to generate next primary key
        self.id = None
        self.created_date = datetime.utcnow()
        self.modified_date = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    def update(self):
        """
        Updates a ProjectMembership to the database
        """
        logger.info("Saving %s", self.email)
        if not self.id:
            raise DataValidationError("Update called with empty ID field")
        self.modified_date = datetime.utcnow()
        db.session.commit()

    def delete(self):
        """Removes a ProjectMembership from the data store"""
        logger.info(
            f"Deleting {self.email} membership for project_id : {self.project_id}"
        )
        self.active = False
        self.modified_date = datetime.utcnow()
        db.session.commit()

    def serialize(self):
        """Serializes a ProjectMembership into a dictionary"""
        return {
            "id": self.id,
            "email": self.email,
            "created_date": self.created_date.isoformat(),
            "modified_date": self.modified_date.isoformat(),
            "active": self.active,
            "status": self.status,
        }

    def deserialize(self, data: dict):
        """
        Deserializes a ProjectMembership from a dictionary
        Args:
            data (dict): A dictionary containing the ProjectMembership data
        """
        try:
            self.email = data["email"]
            self.status = data.get(
                "status", ProjectMembershipStatus.CREATION_REQUEST_RECEIVED.value
            )
        except AttributeError as error:
            raise DataValidationError("Invalid attribute: " + error.args[0]) from error
        except KeyError as error:
            raise DataValidationError(
                "Invalid ProjectMembership: missing " + error.args[0]
            ) from error
        except TypeError as error:
            raise DataValidationError(
                "Invalid ProjectMembership: body of request contained bad or no data "
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
        """Returns all of the ProjectMemberships in the database"""
        logger.info("Processing all ProjectMemberships")
        return cls.query.filter(cls.active == True)

    @classmethod
    def find(cls, project_membership_id: int):
        """Finds a ProjectMembership by it's ID

        :param project_membership_id: the id of the ProjectMembership to find
        :type project_membership_id: int

        :return: an instance with the project_membership_id, or None if not found
        :rtype: ProjectMembership

        """
        logger.info("Processing lookup for id %s ...", project_membership_id)
        return cls.query.get(project_membership_id)

    @classmethod
    def find_or_404(cls, project_membership_id: int):
        """Find a ProjectMembership by it's id

        :param project_membership_id: the id of the ProjectMembership to find
        :type project_membership_id: int

        :return: an instance with the project_membership_id, or 404_NOT_FOUND if not found
        :rtype: ProjectMembership

        """
        logger.info("Processing lookup or 404 for id %s ...", project_membership_id)
        return cls.query.get_or_404(project_membership_id)

    @classmethod
    def find_by_email(cls, email: str) -> list:
        """Returns all ProjectMemberships with the given email

        :param email: the email of the ProjectMemberships you want to match
        :type email: str

        :return: a collection of ProjectMemberships with that email
        :rtype: list

        """
        logger.info("Processing email query for %s ...", email)
        return cls.query.filter(cls.email == email and cls.active == True)

    @classmethod
    def find_by_status(cls, status) -> list:
        """Returns all ProjectMemberships by their status

        :param status : ProjectMembershipStatus Enum
        :type ProjectMembershipStatus: Enum

        :return: a collection of ProjectMemberships that are available
        :rtype: list

        """
        logger.info("Processing status query for %s ...", status)
        return cls.query.filter(cls.status == status)
