# Attempt to stop any running Flask and Celery processes
pkill -f gunicorn
pkill -f celery

# Give the processes some time to stop
sleep 5

# Start gunicorn
gunicorn service:app --log-level=info --timeout=1000 --bind 0.0.0.0:8000 &

# Start celery worker
celery -A service.celery worker --queues save_firmware_events_to_db  --loglevel=warning --concurrency 1

# This command will prevent the script from exiting, and thus the container from stopping
tail -f /dev/null