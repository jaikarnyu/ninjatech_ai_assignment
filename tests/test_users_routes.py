

"""
Users API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
  codecov --token=$CODECOV_TOKEN

  While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_service.py:TestUsersService
"""

import os
import logging
from unittest import TestCase

# from unittest.mock import MagicMock, patch
from urllib.parse import quote_plus
from service import app
from service.common import status
from service.models.users import db, init_db, Users, UserStatus
from tests.factories import UsersFactory

# Disable all but critical errors during normal test run
# uncomment for debugging failing tests
# logging.disable(logging.CRITICAL)

# DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///../db/test.db')
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/testdb"
)
BASE_URL = "/api/users"


######################################################################
#  T E S T   W E B B O T   S E R V I C E
######################################################################
class TestUsersService(TestCase):
    """Users Server Tests"""

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
        db.session.query(Users).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    def _create_users(self, count):
        """Factory method to create users in bulk"""
        users = []
        for _ in range(count):
            test_users = UsersFactory()
            app.logger.info(test_users.serialize())
            response = self.client.post(BASE_URL, json=test_users.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test users",
            )
            new_users = response.get_json()
            test_users.id = new_users["id"]
            users.append(test_users)
        return users

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

    def test_get_users_list(self):
        """It should Get a list of Userss"""
        self._create_users(5)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 5)

    def test_get_users(self):
        """It should Get a single Users"""
        # get the id of a users
        test_users = self._create_users(1)[0]
        response = self.client.get(f"{BASE_URL}/{test_users.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["email"], test_users.email)

    def test_get_users_not_found(self):
        """It should not Get a Users thats not found"""
        response = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        logging.debug("Response data = %s", data)
        self.assertIn("was not found", data["message"])

    def test_create_users(self):
        """It should Create a new Users"""
        test_users = UsersFactory()
        logging.debug("Test Users: %s", test_users.serialize())
        response = self.client.post(BASE_URL, json=test_users.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check the data is correct
        new_users = response.get_json()
        self.assertEqual(new_users["email"], test_users.email)
        self.assertEqual(new_users["name"], test_users.name)
        
        # Check that the location header was correct
        location = BASE_URL + "/" + str(new_users["id"])
        response = self.client.get(location)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_users = response.get_json()
        self.assertEqual(new_users["email"], test_users.email)
        self.assertEqual(new_users["name"], test_users.name)
      
    def test_update_users(self):
        """It should Update an existing Users"""
        # create a users to update
        test_users = UsersFactory()
        response = self.client.post(BASE_URL, json=test_users.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # update the users
        new_users = response.get_json()
        logging.debug(new_users)
        new_users["name"] = '2'
        response = self.client.put(f"{BASE_URL}/{new_users['id']}", json=new_users)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_users = response.get_json()
        self.assertEqual(updated_users["name"], '2')

    def test_delete_users(self):
        """It should Delete a Users"""
        test_users = self._create_users(1)[0]
        response = self.client.delete(f"{BASE_URL}/{test_users.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.data), 0)
        # make sure they are deleted
        response = self.client.get(f"{BASE_URL}/{test_users.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    ######################################################################
    #  T E S T   S A D   P A T H S
    ######################################################################

    def test_create_users_no_data(self):
        """It should not Create a Users with missing data"""
        response = self.client.post(BASE_URL, json={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_users_no_content_type(self):
        """It should not Create a Users with no content type"""
        response = self.client.post(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_users_bad_name(self):
        """It should not Create a Users with bad available data"""
        test_users = UsersFactory()
        logging.debug(test_users)
        # change available to a string
        test_users.email = 1
        response = self.client.post(BASE_URL, json=test_users.serialize())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
