

"""
Notifications API Service Test Suite

"""

import os
import logging
from unittest import TestCase

# from unittest.mock import MagicMock, patch
from urllib.parse import quote_plus
from service import app
from service.common import status
from service.models.notifications import db, init_db, Notifications, NotificationStatus
from tests.factories import NotificationsFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/testdb"
)
BASE_URL = "/api/notifications"


######################################################################
#  T E S T   W E B B O T   S E R V I C E
######################################################################
class TestNotificationsService(TestCase):
    """Notifications Server Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Notifications).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    def _create_notifications(self, count):
        """Factory method to create notifications in bulk"""
        notifications = []
        for _ in range(count):
            test_notifications = NotificationsFactory()
            app.logger.info(test_notifications.serialize())
            response = self.client.post(BASE_URL, json=test_notifications.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test notifications",
            )
            new_notifications = response.get_json()
            test_notifications.id = new_notifications["id"]
            notifications.append(test_notifications)
        return notifications

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_health(self):
        """It should be healthy"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["status"], 200)
        self.assertEqual(data["message"], "Healthy")

    def test_get_notifications_list(self):
        """It should Get a list of Notificationss"""
        self._create_notifications(5)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 5)

    def test_get_notifications(self):
        """It should Get a single Notifications"""
        # get the id of a notifications
        test_notifications = self._create_notifications(1)[0]
        response = self.client.get(f"{BASE_URL}/{test_notifications.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["user_id"], test_notifications.user_id)

    def test_get_notifications_not_found(self):
        """It should not Get a Notifications thats not found"""
        response = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        logging.debug("Response data = %s", data)
        self.assertIn("was not found", data["message"])

    def test_create_notifications(self):
        """It should Create a new Notifications"""
        test_notifications = NotificationsFactory()
        logging.debug("Test Notifications: %s", test_notifications.serialize())
        response = self.client.post(BASE_URL, json=test_notifications.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check the data is correct
        new_notifications = response.get_json()
        self.assertEqual(new_notifications["user_id"], test_notifications.user_id)
        self.assertEqual(new_notifications["notification"], test_notifications.notification)
        
        # Check that the location header was correct
        location = BASE_URL + "/" + str(new_notifications["id"])
        response = self.client.get(location)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_notifications = response.get_json()
        self.assertEqual(new_notifications["user_id"], test_notifications.user_id)
        self.assertEqual(new_notifications["notification"], test_notifications.notification)
      
    def test_update_notifications(self):
        """It should Update an existing Notifications"""
        # create a notifications to update
        test_notifications = NotificationsFactory()
        response = self.client.post(BASE_URL, json=test_notifications.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # update the notifications
        new_notifications = response.get_json()
        logging.debug(new_notifications)
        new_notifications["notification"] = '2'
        response = self.client.put(f"{BASE_URL}/{new_notifications['id']}", json=new_notifications)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_notifications = response.get_json()
        self.assertEqual(updated_notifications["notification"], '2')

    def test_delete_notifications(self):
        """It should Delete a Notifications"""
        test_notifications = self._create_notifications(1)[0]
        response = self.client.delete(f"{BASE_URL}/{test_notifications.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.data), 0)
        # make sure they are deleted
        response = self.client.get(f"{BASE_URL}/{test_notifications.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    ######################################################################
    #  T E S T   S A D   P A T H S
    ######################################################################

    def test_create_notifications_no_data(self):
        """It should not Create a Notifications with missing data"""
        response = self.client.post(BASE_URL, json={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_notifications_no_content_type(self):
        """It should not Create a Notifications with no content type"""
        response = self.client.post(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_notifications_bad_notification(self):
        """It should not Create a Notifications with bad available data"""
        test_notifications = NotificationsFactory()
        logging.debug(test_notifications)
        # change available to a string
        test_notifications.user_id = "1"
        response = self.client.post(BASE_URL, json=test_notifications.serialize())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
