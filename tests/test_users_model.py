# Copyright 2016, 2021 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for User Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_users.py:TestUserModel

"""
import os
import logging
import unittest
from datetime import date
from werkzeug.exceptions import NotFound
from service.models.users import (Users, 
    DataValidationError,
    db)
from service import app
from tests.factories import UsersFactory
from flask import Flask
from service import config

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/testdb"
)


######################################################################
# U S E R   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestUserModel(unittest.TestCase):
    """Test Cases for User Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Users.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Users).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_user(self):
        """It should Create a user and assert that it exists"""
        user = Users(
            email="test@gmail.com",
            name="test",
        )
        self.assertTrue(user is not None)
        self.assertEqual(user.id, None)
        user.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(user.id)
        self.assertEqual(user.email, "test@gmail.com")


    def test_add_a_user(self):
        """It should Create a user and add it to the database"""
        users = Users.query.all()
        self.assertEqual(users, [])
        user = Users(
             email="test@gmail.com",
            name="test",
        )
        self.assertTrue(user is not None)
        self.assertEqual(user.id, None)
        user.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(user.id)
        users = Users.query.all()
        self.assertEqual(len(users), 1)

    def test_read_a_user(self):
        """It should Read a User"""
        user = UsersFactory()
        logging.debug(user)
        user.create()
        self.assertIsNotNone(user.id)
        # Read it back
        user = Users.find(user.id)
        self.assertIsNotNone(user)
        self.assertEqual(user.id, user.id)

    def test_update_a_user(self):
        """It should Update a User"""
        user = UsersFactory()
        logging.debug(user)
        user.id = None
        user.create()
        logging.debug(user)
        self.assertIsNotNone(user.id)
        # Change it an save it
        user.email = 'aaa@gmail.com'
        original_id = user.id
        user.update()
        self.assertEqual(user.id, original_id)
        self.assertEqual(user.email, 'aaa@gmail.com')
        # Fetch it back and make sure the id hasn't changed
        # but the data did change
        users = Users.query.all()
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].id, original_id)
        self.assertEqual(users[0].email, 'aaa@gmail.com')

    def test_update_no_id(self):
        """It should not Update a User with no id"""
        user = UsersFactory()
        logging.debug(user)
        user.id = None
        self.assertRaises(DataValidationError, user.update)

    def test_delete_a_user(self):
        """It should Delete a User"""
        user = UsersFactory()
        user.create()
        self.assertEqual(len(Users.query.all()), 1)
        # delete the user and make sure it isn't in the database
        user.delete()
        self.assertEqual(user.active, False)

    def test_list_all_users(self):
        """It should List all Users in the database"""
        users = Users.query.all()
        self.assertEqual(users, [])
        # Create 5 Users
        for _ in range(5):
            user = UsersFactory()
            user.create()
        # See if we get back 5 users
        users = Users.query.all()
        self.assertEqual(len(users), 5)

    def test_serialize_a_user(self):
        """It should serialize a User"""
        user = UsersFactory()
        data = user.serialize()
        self.assertNotEqual(data, None)
        self.assertIn("id", data)
        self.assertEqual(data["id"], user.id)
        self.assertIn("email", data)
        self.assertEqual(data["email"], user.email)
        self.assertIn("status", data)
        self.assertEqual(data["status"], user.status)
        self.assertIn("created_date", data)
        self.assertEqual(data["created_date"], user.created_date.isoformat())
        self.assertIn("modified_date", data)
        self.assertEqual(data["modified_date"], user.modified_date.isoformat())

    def test_deserialize_a_user(self):
        """It should de-serialize a User"""
        data = UsersFactory().serialize()
        user = Users()
        user.deserialize(data)
        self.assertNotEqual(user, None)
        self.assertEqual(user.id, None)
        self.assertEqual(user.email, data["email"])
        self.assertEqual(user.status, data["status"])
        self.assertEqual(user.created_date, data["created_date"])
        self.assertEqual(user.modified_date, data["modified_date"])

    def test_deserialize_missing_data(self):
        """It should not deserialize a User with missing data"""
        data = {}
        user = Users()
        self.assertRaises(DataValidationError, user.deserialize, data)

    def test_deserialize_bad_data(self):
        """It should not deserialize bad data"""
        data = "this is not a dictionary"
        user = Users()
        self.assertRaises(DataValidationError, user.deserialize, data)

    def test_find_user(self):
        """It should Find a User by ID"""
        users = UsersFactory.create_batch(5)
        for user in users:
            user.create()
        logging.debug(users)
        # make sure they got saved
        self.assertEqual(len(Users.query.all()), 5)
        # find the 2nd user in the list
        user = Users.find(users[1].id)
        self.assertIsNot(user, None)
        self.assertEqual(user.id, users[1].id)
        self.assertEqual(user.email, users[1].email)
        self.assertEqual(user.status, users[1].status)

    def test_find_by_email(self):
        """It should Find a User by User Email"""
        users = UsersFactory.create_batch(10)
        for user in users:
            user.create()
        email = users[0].email
        count = len([user for user in users if user.email == email])
        found = Users.find_by_email(email)
        self.assertEqual(len(found), count)
        for user in found:
            self.assertEqual(user.email, email)


    def test_find_or_404_found(self):
        """It should Find or return 404 not found"""
        users = UsersFactory.create_batch(3)
        for user in users:
            user.create()

        user = Users.find_or_404(users[1].id)
        self.assertIsNot(user, None)
        self.assertEqual(user.id, users[1].id)
        self.assertEqual(user.email, users[1].email)

    