

"""
Orders API Service Test Suite

"""

import os
import logging
from unittest import TestCase

# from unittest.mock import MagicMock, patch
from urllib.parse import quote_plus
from service import app
from service.common import status
from service.models.orders import db, init_db, Orders, OrderStatus
from tests.factories import OrdersFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/testdb"
)
BASE_URL = "/api/orders"


######################################################################
#  T E S T   W E B B O T   S E R V I C E
######################################################################
class TestOrdersService(TestCase):
    """Orders Server Tests"""

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
        db.session.query(Orders).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    def _create_orders(self, count):
        """Factory method to create orders in bulk"""
        orders = []
        for _ in range(count):
            test_orders = OrdersFactory()
            app.logger.info(test_orders.serialize())
            response = self.client.post(BASE_URL, json=test_orders.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test orders",
            )
            new_orders = response.get_json()
            test_orders.id = new_orders["id"]
            orders.append(test_orders)
        return orders

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

    def test_get_orders_list(self):
        """It should Get a list of Orderss"""
        self._create_orders(5)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 5)

    def test_get_orders(self):
        """It should Get a single Orders"""
        # get the id of a orders
        test_orders = self._create_orders(1)[0]
        response = self.client.get(f"{BASE_URL}/{test_orders.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["user_id"], test_orders.user_id)

    def test_get_orders_not_found(self):
        """It should not Get a Orders thats not found"""
        response = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        logging.debug("Response data = %s", data)
        self.assertIn("was not found", data["message"])

    def test_create_orders(self):
        """It should Create a new Orders"""
        test_orders = OrdersFactory()
        logging.debug("Test Orders: %s", test_orders.serialize())
        response = self.client.post(BASE_URL, json=test_orders.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check the data is correct
        new_orders = response.get_json()
        self.assertEqual(new_orders["user_id"], test_orders.user_id)
        self.assertEqual(new_orders["name"], test_orders.name)
        
        # Check that the location header was correct
        location = BASE_URL + "/" + str(new_orders["id"])
        response = self.client.get(location)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_orders = response.get_json()
        self.assertEqual(new_orders["user_id"], test_orders.user_id)
        self.assertEqual(new_orders["name"], test_orders.name)
      
    def test_update_orders(self):
        """It should Update an existing Orders"""
        # create a orders to update
        test_orders = OrdersFactory()
        response = self.client.post(BASE_URL, json=test_orders.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # update the orders
        new_orders = response.get_json()
        logging.debug(new_orders)
        new_orders["name"] = '2'
        response = self.client.put(f"{BASE_URL}/{new_orders['id']}", json=new_orders)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_orders = response.get_json()
        self.assertEqual(updated_orders["name"], '2')

    def test_delete_orders(self):
        """It should Delete a Orders"""
        test_orders = self._create_orders(1)[0]
        response = self.client.delete(f"{BASE_URL}/{test_orders.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.data), 0)
        # make sure they are deleted
        response = self.client.get(f"{BASE_URL}/{test_orders.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    ######################################################################
    #  T E S T   S A D   P A T H S
    ######################################################################

    def test_create_orders_no_data(self):
        """It should not Create a Orders with missing data"""
        response = self.client.post(BASE_URL, json={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_orders_no_content_type(self):
        """It should not Create a Orders with no content type"""
        response = self.client.post(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_orders_bad_name(self):
        """It should not Create a Orders with bad available data"""
        test_orders = OrdersFactory()
        logging.debug(test_orders)
        # change available to a string
        test_orders.user_id = "1"
        response = self.client.post(BASE_URL, json=test_orders.serialize())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
