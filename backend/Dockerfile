# Base stage with common dependencies
FROM python:3.11-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Development stage - includes hot reload
FROM base AS dev

COPY . .

EXPOSE 5499
ARG APP_VERSION=development
ENV APP_VERSION=${APP_VERSION}

# Use bash entrypoint to run migrations before starting server
ENTRYPOINT ["/bin/bash", "./entrypoint.sh"]

# Run with reload for development
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5499", "--reload"]

# Production stage - optimized for deployment
FROM base AS production

# Copy application code
COPY . .

# Create non-root user for security
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --ingroup appgroup appuser && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 5499
ARG APP_VERSION=development
ENV APP_VERSION=${APP_VERSION}

# Use bash entrypoint to run migrations before starting server
ENTRYPOINT ["/bin/bash", "./entrypoint.sh"]

# Run without reload, with multiple workers for production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5499", "--workers", "4"]
