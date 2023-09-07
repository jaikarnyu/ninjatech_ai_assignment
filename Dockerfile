FROM python:3.9-slim

# Add any tools that are needed beyond Python 3.9
RUN apt-get update && \
    apt-get install -y sudo vim make git zip tree curl wget jq procps && \
    apt-get autoremove -y && \
    apt-get clean -y

# Added libraries for PostgreSQL before pip install
RUN apt-get update && apt-get install -y gcc libpq-dev

# Create working folder and install dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install -U pip wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy the application contents
COPY service/ ./service/

# Switch to a non-root user
RUN useradd --uid 1000 vagrant && chown -R vagrant /app
USER vagrant

# Expose any ports the app is expecting in the environment
ENV FLASK_APP=service:app
ENV PORT 8000
EXPOSE $PORT


ENV GUNICORN_BIND 0.0.0.0:$PORT
ENTRYPOINT ["sh", "startup.sh"]
