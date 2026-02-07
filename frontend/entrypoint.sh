#!/bin/bash
set -e

echo "========================================="
echo "🦈 Shark Fin Frontend"
echo "Version: ${APP_VERSION:-development}"
echo "Port: ${PORT:-5400}"
echo "========================================="

# Execute the CMD from Dockerfile (passed as arguments to this script)
exec "$@"
