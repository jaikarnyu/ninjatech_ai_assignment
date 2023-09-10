"""
Global Configuration for Application
"""
import os
import json
import logging
from kombu.utils.url import safequote


# Get environment
env = os.getenv("ENV", "dev")

# Get configuration from environment
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@postgres:5432/postgres"
)

# Configure SQLAlchemy
SQLALCHEMY_DATABASE_URI = DATABASE_URI

# Secret for session management
SECRET_KEY = os.getenv("SECRET_KEY", "sup3r-s3cr3t")
LOGGING_LEVEL = logging.INFO


# AWS Credentials
AWS_ACCESS_KEY = os.getenv("aws_access_key_id", "AKIAUXHD6LSDRNOOLW7Z")
AWS_SECRET_KEY = os.getenv(
    "aws_secret_access_key", "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"
)

aws_access_key = safequote(AWS_ACCESS_KEY)
aws_secret_key = safequote(AWS_SECRET_KEY)

CELERY_BROKER_URL = os.getenv(
    "CELERY_BROKER_URL", f"sqs://{aws_access_key}:{aws_secret_key}@"
)

CELERY_CONFIG = {
    "broker_url": CELERY_BROKER_URL,
    "broker_transport_options": {
        "queue_name_prefix": f"celery-{env}-",
    },
}

CELERY_NOTIFICATIONS_QUEUE = os.getenv(
    "CELERY_NOTIFICATIONS_QUEUE", "notifications-queue"
)
