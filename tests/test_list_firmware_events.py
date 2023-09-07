"""
Firmware Events API Service Test Suite
"""

import os
import logging
from unittest import TestCase


# from unittest.mock import MagicMock, patch
from urllib.parse import quote_plus
from service import app
from service.common import status
from service.tasks.device_firmware_events import save_firmware_events_to_db
from service.models.projects import Projects, db, DataValidationError
from service.models.device_firmware_events import DeviceFirmwareEvents
from service.models.device_api_keys import DeviceApiKeys
from service.models.devices import Devices
from service.models.project_membership_api_keys import ProjectMembershipApiKeys
from service.models.project_memberships import ProjectMemberships
from service import config as conf
import time

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/testdb"
)
BASE_URL = "/api/firmware"


######################################################################
#  T E S T   M E M F A U L T  S E R V I C E
######################################################################
class TestListFirmwareEventRoutes(TestCase):
    """ List Firmware Event Routes Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        
        # Initialise tables
        Projects.init_db(app)
        Devices.init_db(app)
        DeviceApiKeys.init_db(app)
        ProjectMemberships.init_db(app)
        ProjectMembershipApiKeys.init_db(app)
        DeviceFirmwareEvents.init_db(app)


    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.drop_all()
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(DeviceFirmwareEvents).delete()  # clean up the last tests
        db.session.commit()
        self.create_firmware_events()

    def tearDown(self):
        db.session.remove()


    def create_firmware_events(self):
        # Setup initial projects, memberships, devices, device api keys
        app.logger.info("Creating test project")
        project = Projects(name="Test Project")
        project.create()

        app.logger.info("Creating test project membership")
        project_membership = ProjectMemberships(
            project_id=project.id, 
            email="test@email.com",
        )
        project_membership.create()

        app.logger.info("Creating test device")
        device = Devices(
            project_id=project.id,
            name="Test Device",
        )
        device.create()

        app.logger.info("Creating test device api key")
        device_api_key = DeviceApiKeys(
            device_id=device.id,
        )
        device_api_key.create()

        app.logger.info("Creating test project membership api key")
        project_membership_api_key = ProjectMembershipApiKeys(
            project_membership_id=project_membership.id,
        )
        project_membership_api_key.create()

        
        self.device_api_key = device_api_key
        self.project_membership_api_key = project_membership_api_key
        self.device_id = device.id


        app.logger.info("Test device api key: %s", device_api_key.secret)
        app.logger.info("Test project membership api key: %s", project_membership_api_key.secret)

        # create firmware events
        app.logger.info("Creating test firmware events")
        test_firmware_event_1 = DeviceFirmwareEvents(
            device_id=device.id,
            version="1.0.0",
        )
        test_firmware_event_1.create()

        test_firmware_event_2 = DeviceFirmwareEvents(
            device_id=device.id,
            version="1.0.1",
        )
        test_firmware_event_2.create()

        app.logger.info("Test setup complete")


    
    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_health(self):
        """It should be healthy"""
        response = self.client.get("/healthcheck")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["status"], 200)
        self.assertEqual(data["message"], "Healthy")

    def test_list_firmware_events(self):
        """It should return a list of firmware events"""
        url = BASE_URL + f"?device_id={self.device_id}"
        print(url)
        response = self.client.get(
            url,
            headers={
                "X-Project-Membership-Api-Key": self.project_membership_api_key.secret,
            },
        )
        print(response.get_json())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 2)

    def test_list_firmware_events_without_device_id(self):
        """It should return a 400 without device id"""
        url = BASE_URL
        response = self.client.get(
            url,
            headers={
                "X-Project-Membership-Api-Key": self.project_membership_api_key.secret,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_firmware_events_with_invalid_device_id(self):
        """It should return a 400 with invalid device id"""
        url = BASE_URL + "?device_id=invalid"
        response = self.client.get(
            url,
            headers={
                "X-Project-Membership-Api-Key": self.project_membership_api_key.secret,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_firmware_events_with_invalid_project_membership_api_key(self):
        """It should return a 401 with invalid project membership api key"""
        url = BASE_URL + f"?device_id={self.device_id}"
        response = self.client.get(
            url,
            headers={
                "X-Project-Membership-Api-Key": "invalid",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_firmware_events_without_project_membership_api_key(self):
        """It should return a 401 without project membership api key"""
        url = BASE_URL + f"?device_id={self.device_id}"
        response = self.client.get(
            url,
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    
    def test_list_firmware_events_with_device_id_not_exists(self):
        """ It should return a 404 when device id does not exist """   
        url = BASE_URL + f"?device_id=100000000"

        response = self.client.get(
            url,
            headers={
                "X-Project-Membership-Api-Key": self.project_membership_api_key.secret,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
                

    
