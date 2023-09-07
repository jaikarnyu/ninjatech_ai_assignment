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
from datetime import datetime

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/testdb"
)
BASE_URL = "/api/firmware"


######################################################################
#  T E S T   M E M F A U L T  S E R V I C E
######################################################################
class TestFirmwareUpdateRoute(TestCase):
    """Firmware Update Route Tests"""

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
        self.create_api_keys()

    def tearDown(self):
        db.session.remove()


    def create_api_keys(self):
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

    def test_create_firmware_event(self):
        """It should create a new firmware event"""
        # create a firmware event
        test_firmware_event = {
            "timestamp": int(time.time()), # in epoch
            "version": "1.0.0",
        }
        headers = {
            "X-Device-Api-Key": self.device_api_key.secret,
            "Content-Type": "application/json"
        }
        response = self.client.post(BASE_URL, json=test_firmware_event, headers=headers)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        

    def test_create_firmware_event_with_invalid_device_api_key(self):
        """It should not create a new firmware event with invalid device api key"""
        # create a firmware event
        test_firmware_event = {
            "timestamp": int(time.time()), # in epoch
            "version": "1.0.0",
        }
        headers = {
            "X-Device-Api-Key": "invalid_device_api_key",
            "Content-Type": "application/json"
        }
        response = self.client.post(BASE_URL, json=test_firmware_event, headers=headers)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_firmware_event_without_device_api_key(self):
        """It should not create a new firmware event without device api key"""
        # create a firmware event
        test_firmware_event = {
            "timestamp": int(time.time()), # in epoch
            "version": "1.0.0",
        }
        headers = {
            "Content-Type": "application/json"
        }
        response = self.client.post(BASE_URL, json=test_firmware_event, headers=headers)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_firmware_event_with_invalid_version(self):
        """ It should not create a new firmware event with invalid version"""
        # create a firmware event
        test_firmware_event = {
            "timestamp": int(time.time()), # in epoch
            "version": "random version",
        }
        headers = {
            "X-Device-Api-Key": self.device_api_key.secret,
            "Content-Type": "application/json"
        }
        response = self.client.post(BASE_URL, data=test_firmware_event, headers=headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_firmware_event_with_invalid_timestamp(self):
        """ It should not create a new firmware event with invalid timestamp"""
        # create a firmware event
        test_firmware_event = {
            "timestamp": "random timestamp", # in epoch
            "version": "random version",
        }
        headers = {
            "X-Device-Api-Key": self.device_api_key.secret,
            "Content-Type": "application/json"
        }
        response = self.client.post(BASE_URL, data=test_firmware_event, headers=headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_firmware_event_without_version(self):
        """ It should not create a new firmware event without version"""
        # create a firmware event
        test_firmware_event = {
            "timestamp": int(time.time()), # in epoch
        }
        headers = {
            "X-Device-Api-Key": self.device_api_key.secret,
            "Content-Type": "application/json"
        }
        response = self.client.post(BASE_URL, data=test_firmware_event, headers=headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_firmware_event_without_timestamp(self):
        """ It should not create a new firmware event without timestamp"""
        # create a firmware event
        test_firmware_event = {
            "version": "1.0.0"
        }
        headers = {
            "X-Device-Api-Key": self.device_api_key.secret,
            "Content-Type": "application/json"
        }
        response = self.client.post(BASE_URL, data=test_firmware_event, headers=headers)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_save_firmware_events_to_db_task(self):
        """ It should save firmware events to db"""
        # create a firmware event
        test_firmware_event = {
            "timestamp": int(time.time()), # in epoch
            "version": "1.0.0",
        }
        time.sleep(5)
        for i in range(10):
            save_firmware_events_to_db(self.device_id, datetime.fromtimestamp(test_firmware_event["timestamp"]), test_firmware_event["version"])
        firmware_events = DeviceFirmwareEvents.query.all()
        self.assertEqual(len(firmware_events), 1)
        self.assertEqual(firmware_events[0].device_id, self.device_id)
        self.assertEqual(firmware_events[0].version, test_firmware_event["version"])
        self.assertEqual(firmware_events[0].status, "SUCCESS")
        self.assertEqual(firmware_events[0].created_date, datetime.fromtimestamp(test_firmware_event["timestamp"]))    

    def test_save_firmware_events_to_db_task(self):
        """ It should save firmware events to db"""
        # create a firmware event
        test_firmware_event = {
            "timestamp": int(time.time()), # in epoch
            "version": "1.0.0",
        }
        time.sleep(5)
        for i in range(10):
            save_firmware_events_to_db(self.device_id, datetime.fromtimestamp(test_firmware_event["timestamp"]), test_firmware_event["version"])
        firmware_events = DeviceFirmwareEvents.query.all()
        self.assertEqual(len(firmware_events), 1)
        self.assertEqual(firmware_events[0].device_id, self.device_id)
        self.assertEqual(firmware_events[0].version, test_firmware_event["version"])
        self.assertEqual(firmware_events[0].status, "SUCCESS")
        self.assertEqual(firmware_events[0].created_date, datetime.fromtimestamp(test_firmware_event["timestamp"]))
    
