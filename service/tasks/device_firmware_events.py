from .. import app, celery  # Import Flask application
import traceback
from datetime import datetime


@celery.task(bind=True, name="save_firmware_events_to_db")
def save_firmware_events_to_db(self, device_id, timestamp, version):
    """
    Save firmware events to database
    """
    try:
        app.logger.info(
            "Saving firmware events to database for device_id: %s, timestamp: %s, version: %s"
            % (device_id, timestamp, version)
        )
        from service.models.device_firmware_events import (
            DeviceFirmwareEvents,
            DeviceFirmwareEventStatus,
        )

        # Check if the firmware update event already exists
        device_firmware_events = (
            DeviceFirmwareEvents.query.filter_by(
                device_id=device_id, version=version, created_date=timestamp
            )
            .order_by(DeviceFirmwareEvents.created_date.desc())
            .first()
        )
        if device_firmware_events:
            app.logger.info("Firmware events already exists in database")
            return True

        device_firmware_events = DeviceFirmwareEvents()
        device_firmware_events.device_id = device_id
        device_firmware_events.version = version
        device_firmware_events.status = DeviceFirmwareEventStatus.SUCCESS.value
        device_firmware_events.created_date = timestamp
        device_firmware_events.create()
        app.logger.info("Saved firmware events to database")
        return True
    except Exception as e:
        app.logger.error("Error saving firmware events to database: %s" % e)
        app.logger.error(traceback.format_exc())
        # If the task failed after 3 retries, send a message to the dead letter queue
        if self.request.retries == 3:
            app.logger.error("Sending message to dead letter queue")
        else:
            # If the task failed before 3 retries, retry the task after 2**self.request.retries seconds
            raise self.retry(countdown=2**self.request.retries, exc=e)
