from .. import app, celery  # Import Flask application
import traceback
from datetime import datetime


@celery.task(bind=True, name="save_firmware_events_to_db")
def send_notification(
    self, user_id, notification_type, notification, timestamp=datetime.utcnow()
):
    """
    Sends a notification to the user
    """
    try:
        app.logger.info(
            f"Saving notification to database for user_id: {user_id} notification_type: {notification_type} notification: {notification}"
        )
        from service.models.notifications import (
            Notifications,
            NotificationType,
            NotificationStatus,
        )

        # Check if notification already exists in database
        notification = (
            Notifications.query.filter_by(
                user_id=user_id, notification=notification, created_date=timestamp
            )
            .order_by(Notifications.created_date.desc())
            .first()
        )
        if notification:
            app.logger.info("Notification already exists in database")
            return True

        # Create notification
        notification = Notifications(
            user_id=user_id,
            notification_type=notification_type,
            notification=notification,
            created_date=timestamp,
        )
        notification.create()
        app.logger.info("Saved notification events to database")

        # Send notification
        if notification_type == NotificationType.EMAIL.value:
            status = send_email(user_id, notification)
            if status:
                notification.status = NotificationStatus.SUCCESS.value
                notification.update()
                app.logger.info("Email sent successfully")
            else:
                notification.status = NotificationStatus.FAILED.value
                notification.update()
                app.logger.error("Email failed to send for user_id: %s" % user_id)
                raise Exception("Email failed to send for user_id: %s" % user_id)
        else:
            app.logger.error(
                "Notification type %s is not supported" % notification_type
            )
            notification.status = NotificationStatus.FAILED.value
            notification.update()
        return True
    except Exception as e:
        app.logger.error("Error saving firmware events to database: %s" % e)
        app.logger.error(traceback.format_exc())
        # If the task failed after 3 retries, send a message to the dead letter queue
        if self.request.retries == 3:
            app.logger.error("Sending message to dead letter queue")
            # TODO Dead letter queue implementation
        else:
            # If the task failed before 3 retries, retry the task after 2**self.request.retries seconds
            raise self.retry(countdown=2**self.request.retries, exc=e)


def send_email(user_id, message):
    """
    Send an email to the user

    :param email: str
    :type message: str
    """
    from service.models.users import Users

    try:
        user = Users.find(user_id)
        app.logger.info(f"'Sending email to {user.email} with message {message}'")
        # TODO Send email
        return True
    except Exception as e:
        app.logger.error("Error sending email: %s" % e)
        app.logger.error(traceback.format_exc())
        return False
