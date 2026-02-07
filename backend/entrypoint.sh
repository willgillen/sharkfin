#!/bin/bash
set -e

echo "========================================="
echo "🦈 Shark Fin Backend"
echo "Version: ${APP_VERSION:-development}"
echo "========================================="

# Wait for PostgreSQL to be ready
echo "Waiting for database..."

# Extract database connection details from DATABASE_URL
# Format: postgresql://user:password@host:port/database
DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')

# Default to common values if extraction fails
DB_HOST=${DB_HOST:-postgres}
DB_PORT=${DB_PORT:-5432}

echo "Checking connection to $DB_HOST:$DB_PORT..."

# Wait up to 60 seconds for PostgreSQL to be available
MAX_RETRIES=30
RETRY_COUNT=0

until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U sharkfin > /dev/null 2>&1; do
  RETRY_COUNT=$((RETRY_COUNT + 1))
  if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
    echo "ERROR: Database not ready after $MAX_RETRIES attempts"
    exit 1
  fi
  echo "Database not ready yet (attempt $RETRY_COUNT/$MAX_RETRIES)..."
  sleep 2
done

echo "Database is ready! Running migrations..."

# Run database migrations automatically
alembic upgrade head

echo "Migrations complete - starting application..."

# Execute the CMD from Dockerfile (passed as arguments to this script)
exec "$@"
