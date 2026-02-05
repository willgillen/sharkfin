# Shark Fin Deployment Guide

This guide covers deploying Shark Fin to various environments using Docker.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Docker Images](#docker-images)
- [Environment Configuration](#environment-configuration)
- [Deployment Options](#deployment-options)
  - [Docker Compose (Recommended)](#docker-compose-recommended)
  - [Individual Containers](#individual-containers)
  - [Kubernetes](#kubernetes)
- [Database Management](#database-management)
- [SSL/TLS Configuration](#ssltls-configuration)
- [Monitoring and Health Checks](#monitoring-and-health-checks)
- [Backup and Recovery](#backup-and-recovery)
- [Upgrading](#upgrading)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Docker Engine 20.10+ or Docker Desktop
- Docker Compose v2.0+ (included with Docker Desktop)
- At least 2GB RAM available for containers
- 10GB disk space for images and data

## Quick Start

1. **Pull the latest images:**

   ```bash
   docker pull ghcr.io/willgillen/sharkfin/backend:latest
   docker pull ghcr.io/willgillen/sharkfin/frontend:latest
   ```

2. **Create your environment file:**

   ```bash
   curl -O https://raw.githubusercontent.com/willgillen/sharkfin/main/.env.example
   mv .env.example .env
   ```

3. **Configure the environment:**

   Edit `.env` and set secure values:

   ```bash
   # Required - Set strong passwords!
   POSTGRES_PASSWORD=your_secure_database_password
   SECRET_KEY=your_secure_secret_key_min_32_chars

   # Optional - Customize if needed
   FRONTEND_PORT=3000
   SHARK_FIN_VERSION=latest
   ```

4. **Download and start the stack:**

   ```bash
   curl -O https://raw.githubusercontent.com/willgillen/sharkfin/main/docker-compose.prod.yml
   docker compose -f docker-compose.prod.yml up -d
   ```

5. **Access Shark Fin:**

   Open `http://localhost:3000` in your browser.

## Docker Images

Shark Fin publishes Docker images to GitHub Container Registry (ghcr.io):

| Image | Description | Tags |
|-------|-------------|------|
| `ghcr.io/willgillen/sharkfin/backend` | FastAPI backend | `latest`, `v1.0.0`, `1.0`, `1` |
| `ghcr.io/willgillen/sharkfin/frontend` | Next.js frontend | `latest`, `v1.0.0`, `1.0`, `1` |

### Supported Architectures

- `linux/amd64` (x86_64)
- `linux/arm64` (Apple Silicon, ARM servers)

### Version Tags

- `latest` - Most recent stable release
- `v1.2.3` - Specific version (recommended for production)
- `1.2` - Latest patch for minor version
- `1` - Latest minor/patch for major version

## Environment Configuration

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `POSTGRES_USER` | Database username | `sharkfin` |
| `POSTGRES_PASSWORD` | Database password | `secure_password_here` |
| `POSTGRES_DB` | Database name | `shark_fin` |
| `SECRET_KEY` | JWT signing key (min 32 chars) | `your-super-secret-key-at-least-32-chars` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SHARK_FIN_VERSION` | Image version tag | `latest` |
| `FRONTEND_PORT` | Port to expose frontend | `3000` |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry | `30` |
| `NEXT_PUBLIC_API_URL` | Backend URL for frontend | `http://localhost:8000` |

### Generating a Secure Secret Key

```bash
# Using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Using OpenSSL
openssl rand -base64 32
```

## Deployment Options

### Docker Compose (Recommended)

The simplest way to deploy Shark Fin is using the production Docker Compose file:

```bash
# Download the production compose file
curl -O https://raw.githubusercontent.com/willgillen/sharkfin/main/docker-compose.prod.yml

# Start all services
docker compose -f docker-compose.prod.yml up -d

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Stop services
docker compose -f docker-compose.prod.yml down
```

### Individual Containers

For more control, you can run containers individually:

```bash
# Create a network
docker network create shark-fin

# Start PostgreSQL
docker run -d \
  --name shark-fin-db \
  --network shark-fin \
  -e POSTGRES_USER=sharkfin \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=shark_fin \
  -v shark-fin-postgres:/var/lib/postgresql/data \
  postgres:15-alpine

# Start Redis
docker run -d \
  --name shark-fin-redis \
  --network shark-fin \
  -v shark-fin-redis:/data \
  redis:7-alpine redis-server --appendonly yes

# Start Backend
docker run -d \
  --name shark-fin-backend \
  --network shark-fin \
  -e DATABASE_URL=postgresql://sharkfin:your_password@shark-fin-db:5432/shark_fin \
  -e REDIS_URL=redis://shark-fin-redis:6379 \
  -e SECRET_KEY=your_secret_key \
  ghcr.io/willgillen/sharkfin/backend:latest

# Start Frontend
docker run -d \
  --name shark-fin-frontend \
  --network shark-fin \
  -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://shark-fin-backend:8000 \
  ghcr.io/willgillen/sharkfin/frontend:latest
```

### Kubernetes

For Kubernetes deployments, create the following resources:

**namespace.yaml:**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: shark-fin
```

**secrets.yaml:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: shark-fin-secrets
  namespace: shark-fin
type: Opaque
stringData:
  postgres-password: "your_secure_password"
  secret-key: "your_jwt_secret_key"
```

**deployment.yaml (Backend):**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: shark-fin
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: ghcr.io/willgillen/sharkfin/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          value: "postgresql://sharkfin:$(POSTGRES_PASSWORD)@postgres:5432/shark_fin"
        - name: REDIS_URL
          value: "redis://redis:6379"
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: shark-fin-secrets
              key: secret-key
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

See the [examples/kubernetes](../examples/kubernetes) directory for complete Kubernetes manifests.

## Database Management

### Running Migrations

Migrations run automatically when the backend container starts. To run manually:

```bash
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### Creating Backups

**Using the backup service:**

```bash
docker compose -f docker-compose.prod.yml --profile backup run db-backup
```

**Manual backup:**

```bash
docker compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U sharkfin -Fc shark_fin > backup_$(date +%Y%m%d).dump
```

### Restoring from Backup

```bash
docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_restore -U sharkfin -d shark_fin --clean < backup.dump
```

## SSL/TLS Configuration

For production, you should use HTTPS. Here are common approaches:

### Using a Reverse Proxy (Recommended)

Use nginx, Traefik, or Caddy in front of Shark Fin:

**Example with Traefik:**

```yaml
# Add to docker-compose.prod.yml
services:
  traefik:
    image: traefik:v2.10
    command:
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
      - "--certificatesresolvers.letsencrypt.acme.email=your@email.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - letsencrypt:/letsencrypt
    networks:
      - shark-fin-external

  frontend:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.sharkfin.rule=Host(`sharkfin.yourdomain.com`)"
      - "traefik.http.routers.sharkfin.entrypoints=websecure"
      - "traefik.http.routers.sharkfin.tls.certresolver=letsencrypt"
```

### Using Cloudflare Tunnel

For easy HTTPS without opening ports:

1. Install cloudflared on your server
2. Create a tunnel: `cloudflared tunnel create shark-fin`
3. Configure the tunnel to point to `http://localhost:3000`

## Monitoring and Health Checks

### Health Endpoints

- **Backend:** `http://localhost:8000/health`
- **Frontend:** `http://localhost:3000` (responds with 200)

### Monitoring with Docker

```bash
# View container health status
docker compose -f docker-compose.prod.yml ps

# View container resource usage
docker stats

# View logs
docker compose -f docker-compose.prod.yml logs -f --tail=100
```

### Recommended Monitoring Stack

For production monitoring, consider adding:

- **Prometheus** - Metrics collection
- **Grafana** - Visualization
- **Loki** - Log aggregation

## Backup and Recovery

### Automated Backups

Add a cron job for regular backups:

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * cd /path/to/shark-fin && docker compose -f docker-compose.prod.yml --profile backup run --rm db-backup
```

### Backup Retention

Implement a rotation script to keep only recent backups:

```bash
#!/bin/bash
# keep-backups.sh - Keep last 7 daily backups
BACKUP_DIR=/path/to/backups
find $BACKUP_DIR -name "shark_fin_*.dump" -mtime +7 -delete
```

## Upgrading

### Standard Upgrade

```bash
# Pull new images
docker compose -f docker-compose.prod.yml pull

# Restart with new images
docker compose -f docker-compose.prod.yml up -d
```

### Upgrading to Specific Version

```bash
# Set version in .env
echo "SHARK_FIN_VERSION=v1.2.0" >> .env

# Pull and restart
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

### Rolling Back

```bash
# Set previous version
export SHARK_FIN_VERSION=v1.1.0

# Restart with old version
docker compose -f docker-compose.prod.yml up -d
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose -f docker-compose.prod.yml logs backend

# Common issues:
# - Database not ready: Wait for postgres healthcheck
# - Missing env vars: Check .env file
# - Port conflict: Change FRONTEND_PORT in .env
```

### Database Connection Issues

```bash
# Test database connectivity
docker compose -f docker-compose.prod.yml exec backend python -c "
from app.core.database import engine
engine.connect()
print('Database connected successfully')
"
```

### Frontend Can't Reach Backend

- Verify `NEXT_PUBLIC_API_URL` is set correctly
- Check that backend container is healthy
- Ensure containers are on the same network

### Performance Issues

```bash
# Check container resources
docker stats

# Increase resources in docker-compose.prod.yml:
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

### Reset Everything

```bash
# Stop and remove all containers, volumes, and networks
docker compose -f docker-compose.prod.yml down -v

# Start fresh
docker compose -f docker-compose.prod.yml up -d
```

---

## Support

- **Documentation:** [GitHub Wiki](https://github.com/willgillen/sharkfin/wiki)
- **Issues:** [GitHub Issues](https://github.com/willgillen/sharkfin/issues)
- **Discussions:** [GitHub Discussions](https://github.com/willgillen/sharkfin/discussions)
