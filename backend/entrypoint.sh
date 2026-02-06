#!/bin/bash
set -e

echo "Starting Shark Fin Backend..."

# Wait a few seconds for PostgreSQL to be ready (docker-compose healthcheck handles this)
echo "Waiting for database..."
sleep 2

echo "Running database migrations..."

# Run database migrations automatically
alembic upgrade head

echo "Migrations complete - starting application..."

# Execute the CMD from Dockerfile (passed as arguments to this script)
exec "$@"
