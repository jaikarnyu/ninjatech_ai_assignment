"""
Global Configuration for Application
"""
import os
import json
import logging

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


CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379")


CELERY_CONFIG = {
    "broker_url": CELERY_BROKER_URL,
    "broker_transport_options": {
        "queue_name_prefix": f"celery-{env}-",
    },
}
