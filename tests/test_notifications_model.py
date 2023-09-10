"""
Test cases for Notifications Model
"""
import os
import logging
import unittest
from datetime import date
from werkzeug.exceptions import NotFound
from service.models.notifications import (Notifications, 
    DataValidationError,
    db)
from service.models.users import Users
from service import app
from tests.factories import NotificationsFactory, UsersFactory
from flask import Flask
from service import config

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/testdb"
)


######################################################################
# U S E R   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestNotificationModel(unittest.TestCase):
    """Test Cases for Notification Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Notifications.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Notifications).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_notification(self):
        """It should Create a notification and assert that it exists"""
        notification = Notifications(
            notification="test"
        )
        self.assertTrue(notification is not None)
        self.assertEqual(notification.id, None)
        notification.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(notification.id)
        self.assertEqual(notification.notification, "test")


    def test_add_a_notification(self):
        """It should Create a notification and add it to the database"""
        data = UsersFactory().serialize()
        user = Users()
        user.deserialize(data)
        user.create()
        notifications = Notifications.query.all()
        self.assertEqual(notifications, [])
        notification = Notifications(
            notification="test",
            user_id = user.id

        )
        self.assertTrue(notification is not None)
        self.assertEqual(notification.id, None)
        notification.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(notification.id)
        notifications = Notifications.query.all()
        self.assertEqual(len(notifications), 1)

    def test_read_a_notification(self):
        """It should Read a Notification"""
        notification = NotificationsFactory()
        logging.debug(notification)
        notification.create()
        self.assertIsNotNone(notification.id)
        # Read it back
        notification = Notifications.find(notification.id)
        self.assertIsNotNone(notification)
        self.assertEqual(notification.id, notification.id)

    def test_update_a_notification(self):
        """It should Update a Notification"""
        notification = NotificationsFactory()
        logging.debug(notification)
        notification.id = None
        notification.create()
        logging.debug(notification)
        self.assertIsNotNone(notification.id)
        # Change it an save it
        notification.notification = 'notification-1'
        original_id = notification.id
        notification.update()
        self.assertEqual(notification.id, original_id)
        self.assertEqual(notification.notification, 'notification-1')
        # Fetch it back and make sure the id hasn't changed
        # but the data did change
        notifications = Notifications.query.all()
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0].id, original_id)
        self.assertEqual(notifications[0].notification, 'notification-1')

    def test_update_no_id(self):
        """It should not Update a Notification with no id"""
        notification = NotificationsFactory()
        logging.debug(notification)
        notification.id = None
        self.assertRaises(DataValidationError, notification.update)

    def test_delete_a_notification(self):
        """It should Delete a Notification"""
        notification = NotificationsFactory()
        notification.create()
        self.assertEqual(len(Notifications.query.all()), 1)
        # delete the notification and make sure it isn't in the database
        notification.delete()
        self.assertEqual(notification.active, False)

    def test_list_all_notifications(self):
        """It should List all Notifications in the database"""
        notifications = Notifications.query.all()
        self.assertEqual(notifications, [])
        # Create 5 Notifications
        for _ in range(5):
            notification = NotificationsFactory()
            notification.create()
        # See if we get back 5 notifications
        notifications = Notifications.query.all()
        self.assertEqual(len(notifications), 5)

    def test_serialize_a_notification(self):
        """It should serialize a Notification"""
        notification = NotificationsFactory()
        data = notification.serialize()
        self.assertNotEqual(data, None)
        self.assertIn("id", data)
        self.assertEqual(data["id"], notification.id)
        self.assertIn("user_id", data)
        self.assertEqual(data["user_id"], notification.user_id)
        self.assertIn("status", data)
        self.assertEqual(data["status"], notification.status)
        self.assertIn("created_date", data)
        self.assertEqual(data["created_date"], notification.created_date.isoformat())
        self.assertIn("modified_date", data)
        self.assertEqual(data["modified_date"], notification.modified_date.isoformat())

    def test_deserialize_a_notification(self):
        """It should de-serialize a Notification"""
        data = NotificationsFactory().serialize()
        notification = Notifications()
        notification.deserialize(data)
        self.assertNotEqual(notification, None)
        self.assertEqual(notification.id, None)
        self.assertEqual(notification.user_id, data["user_id"])
        self.assertEqual(notification.status, data["status"])
        self.assertEqual(notification.created_date, data["created_date"])
        self.assertEqual(notification.modified_date, data["modified_date"])

    def test_deserialize_missing_data(self):
        """It should not deserialize a Notification with missing data"""
        data = {}
        notification = Notifications()
        self.assertRaises(DataValidationError, notification.deserialize, data)

    def test_deserialize_bad_data(self):
        """It should not deserialize bad data"""
        data = "this is not a dictionary"
        notification = Notifications()
        self.assertRaises(DataValidationError, notification.deserialize, data)

    def test_find_notification(self):
        """It should Find a Notification by ID"""
        notifications = NotificationsFactory.create_batch(5)
        for notification in notifications:
            notification.create()
        logging.debug(notifications)
        # make sure they got saved
        self.assertEqual(len(Notifications.query.all()), 5)
        # find the 2nd notification in the list
        notification = Notifications.find(notifications[1].id)
        self.assertIsNot(notification, None)
        self.assertEqual(notification.id, notifications[1].id)
        self.assertEqual(notification.user_id, notifications[1].user_id)
        self.assertEqual(notification.status, notifications[1].status)

    def test_find_by_user_id(self):
        """It should Find a Notification by Notification Email"""
        notifications = NotificationsFactory.create_batch(10)
        for notification in notifications:
            notification.create()
        user_id = notifications[0].user_id
        count = len([notification for notification in notifications if notification.user_id == user_id])
        found = Notifications.find_by_user_id(user_id)
        self.assertEqual(found.count(), count)
        for notification in found:
            self.assertEqual(notification.user_id, user_id)


    def test_find_or_404_found(self):
        """It should Find or return 404 not found"""
        notifications = NotificationsFactory.create_batch(3)
        for notification in notifications:
            notification.create()

        notification = Notifications.find_or_404(notifications[1].id)
        self.assertIsNot(notification, None)
        self.assertEqual(notification.id, notifications[1].id)
        self.assertEqual(notification.user_id, notifications[1].user_id)

    