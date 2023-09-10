
"""
Test Factory to make fake objects for testing
"""
from datetime import date, datetime

import factory
from factory.fuzzy import FuzzyChoice, FuzzyDate
from service.models.users import Users, UserStatus
from service.models.orders import Orders, OrderStatus
from service.models.notifications import Notifications, NotificationType, NotificationStatus



class UsersFactory(factory.Factory):
    """Creates fake users"""

    class Meta:  # pylint: disable=too-few-public-methods
        """Maps factory to data model"""

        model = Users

    id = factory.Sequence(lambda n: n)
    name = factory.Faker("name")
    email = factory.Faker("email")
    created_date = datetime.utcnow()
    modified_date = datetime.utcnow()
    status = UserStatus.CREATION_REQUEST_RECEIVED.value
    active = True

data = UsersFactory().serialize()
user = Users()
user.deserialize(data)
user.create()

class OrdersFactory(factory.Factory):
    """Creates fake Orders"""

    class Meta:  # pylint: disable=too-few-public-methods
        """Maps factory to data model"""

        model = Orders

    id = factory.Sequence(lambda n: n)
    name = factory.Faker("name")
    user_id = user.id
    created_date = datetime.utcnow()
    modified_date = datetime.utcnow()
    status = UserStatus.CREATION_REQUEST_RECEIVED.value
    send_notification = True
    active = True
    created_date = datetime.utcnow()
    modified_date = datetime.utcnow()


class NotificationsFactory(factory.Factory):
    """Creates fake notifications"""

    class Meta:  # pylint: disable=too-few-public-methods
        """Maps factory to data model"""

        model = Notifications

    id = factory.Sequence(lambda n: n)
    user_id = user.id
    created_date = datetime.utcnow()
    modified_date = datetime.utcnow()
    status = NotificationStatus.CREATION_REQUEST_RECEIVED.value
    active = True
    created_date = datetime.utcnow()
    modified_date = datetime.utcnow()
    notification_type = NotificationType.EMAIL.value
    notification = factory.Faker("name")
    