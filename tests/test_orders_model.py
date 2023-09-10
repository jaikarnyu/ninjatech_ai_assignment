"""
Test cases for Orders Model
"""
import os
import logging
import unittest
from datetime import date
from werkzeug.exceptions import NotFound
from service.models.orders import (Orders, 
    DataValidationError,
    db)
from service.models.users import Users
from service import app
from tests.factories import OrdersFactory, UsersFactory
from flask import Flask
from service import config

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/testdb"
)


######################################################################
# U S E R   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestOrderModel(unittest.TestCase):
    """Test Cases for Order Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Orders.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Orders).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_order(self):
        """It should Create a order and assert that it exists"""
        order = Orders(
            name="test"
        )
        self.assertTrue(order is not None)
        self.assertEqual(order.id, None)
        order.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(order.id)
        self.assertEqual(order.name, "test")


    def test_add_a_order(self):
        """It should Create a order and add it to the database"""
        data = UsersFactory().serialize()
        user = Users()
        user.deserialize(data)
        user.create()
        orders = Orders.query.all()
        self.assertEqual(orders, [])
        order = Orders(
            name="test",
            user_id = user.id

        )
        self.assertTrue(order is not None)
        self.assertEqual(order.id, None)
        order.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(order.id)
        orders = Orders.query.all()
        self.assertEqual(len(orders), 1)

    def test_read_a_order(self):
        """It should Read a Order"""
        order = OrdersFactory()
        logging.debug(order)
        order.create()
        self.assertIsNotNone(order.id)
        # Read it back
        order = Orders.find(order.id)
        self.assertIsNotNone(order)
        self.assertEqual(order.id, order.id)

    def test_update_a_order(self):
        """It should Update a Order"""
        order = OrdersFactory()
        logging.debug(order)
        order.id = None
        order.create()
        logging.debug(order)
        self.assertIsNotNone(order.id)
        # Change it an save it
        order.name = 'order-1'
        original_id = order.id
        order.update()
        self.assertEqual(order.id, original_id)
        self.assertEqual(order.name, 'order-1')
        # Fetch it back and make sure the id hasn't changed
        # but the data did change
        orders = Orders.query.all()
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0].id, original_id)
        self.assertEqual(orders[0].name, 'order-1')

    def test_update_no_id(self):
        """It should not Update a Order with no id"""
        order = OrdersFactory()
        logging.debug(order)
        order.id = None
        self.assertRaises(DataValidationError, order.update)

    def test_delete_a_order(self):
        """It should Delete a Order"""
        order = OrdersFactory()
        order.create()
        self.assertEqual(len(Orders.query.all()), 1)
        # delete the order and make sure it isn't in the database
        order.delete()
        self.assertEqual(order.active, False)

    def test_list_all_orders(self):
        """It should List all Orders in the database"""
        orders = Orders.query.all()
        self.assertEqual(orders, [])
        # Create 5 Orders
        for _ in range(5):
            order = OrdersFactory()
            order.create()
        # See if we get back 5 orders
        orders = Orders.query.all()
        self.assertEqual(len(orders), 5)

    def test_serialize_a_order(self):
        """It should serialize a Order"""
        order = OrdersFactory()
        data = order.serialize()
        self.assertNotEqual(data, None)
        self.assertIn("id", data)
        self.assertEqual(data["id"], order.id)
        self.assertIn("user_id", data)
        self.assertEqual(data["user_id"], order.user_id)
        self.assertIn("status", data)
        self.assertEqual(data["status"], order.status)
        self.assertIn("created_date", data)
        self.assertEqual(data["created_date"], order.created_date.isoformat())
        self.assertIn("modified_date", data)
        self.assertEqual(data["modified_date"], order.modified_date.isoformat())

    def test_deserialize_a_order(self):
        """It should de-serialize a Order"""
        data = OrdersFactory().serialize()
        order = Orders()
        order.deserialize(data)
        self.assertNotEqual(order, None)
        self.assertEqual(order.id, None)
        self.assertEqual(order.user_id, data["user_id"])
        self.assertEqual(order.status, data["status"])
        self.assertEqual(order.created_date, data["created_date"])
        self.assertEqual(order.modified_date, data["modified_date"])

    def test_deserialize_missing_data(self):
        """It should not deserialize a Order with missing data"""
        data = {}
        order = Orders()
        self.assertRaises(DataValidationError, order.deserialize, data)

    def test_deserialize_bad_data(self):
        """It should not deserialize bad data"""
        data = "this is not a dictionary"
        order = Orders()
        self.assertRaises(DataValidationError, order.deserialize, data)

    def test_find_order(self):
        """It should Find a Order by ID"""
        orders = OrdersFactory.create_batch(5)
        for order in orders:
            order.create()
        logging.debug(orders)
        # make sure they got saved
        self.assertEqual(len(Orders.query.all()), 5)
        # find the 2nd order in the list
        order = Orders.find(orders[1].id)
        self.assertIsNot(order, None)
        self.assertEqual(order.id, orders[1].id)
        self.assertEqual(order.user_id, orders[1].user_id)
        self.assertEqual(order.status, orders[1].status)

    def test_find_by_user_id(self):
        """It should Find a Order by Order user_id"""
        orders = OrdersFactory.create_batch(10)
        for order in orders:
            order.create()
        user_id = orders[0].user_id
        count = len([order for order in orders if order.user_id == user_id])
        found = Orders.find_by_user_id(user_id)
        self.assertEqual(found.count(), count)
        for order in found:
            self.assertEqual(order.user_id, user_id)


    def test_find_or_404_found(self):
        """It should Find or return 404 not found"""
        orders = OrdersFactory.create_batch(3)
        for order in orders:
            order.create()

        order = Orders.find_or_404(orders[1].id)
        self.assertIsNot(order, None)
        self.assertEqual(order.id, orders[1].id)
        self.assertEqual(order.user_id, orders[1].user_id)

    