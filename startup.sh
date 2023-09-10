# Attempt to stop any running Flask and Celery processes
pkill -f gunicorn
pkill -f celery

# Give the processes some time to stop
sleep 5

SERVICE_TYPE=${SERVICE_TYPE:-all}
WORKER_CONCURRENCY=${WORKER_CONCURRENCY:-1}

# Start the gunicorn server for api if service type is 'api' or 'all'
if [ "$SERVICE_TYPE" = "api" ] || [ "$SERVICE_TYPE" = "all" ]; then
    gunicorn service:app --workers=$WORKER_CONCURRENCY --log-level=info --timeout=1000 --bind 0.0.0.0:8080 &
fi

# Start the celery worker for context queue if service type is 'context' or 'all'
if [ "$SERVICE_TYPE" = "notification" ] || [ "$SERVICE_TYPE" = "all" ]; then
    celery -A service.celery worker --queues notification --loglevel=warning --concurrency $WORKER_CONCURRENCY &
fi


# This command will prevent the script from exiting, and thus the container from stopping
tail -f /dev/null