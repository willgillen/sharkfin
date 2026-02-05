# Deploying Shark Fin on CasaOS

This guide covers deploying Shark Fin to [CasaOS](https://casaos.zimaspace.com/), a simple, elegant open-source personal cloud system that simplifies Docker management.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Method 1: Custom Install via UI](#method-1-custom-install-via-ui)
- [Method 2: Command Line Installation](#method-2-command-line-installation)
- [Configuration](#configuration)
- [Accessing Shark Fin](#accessing-shark-fin)
- [Updating](#updating)
- [Backup](#backup)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- CasaOS v0.4.4 or later (for native Docker Compose support)
- At least 2GB RAM available
- 10GB free disk space
- Access to CasaOS dashboard

## Quick Start

The fastest way to deploy Shark Fin on CasaOS:

1. Download the CasaOS-compatible compose file (see below)
2. Use Custom Install in the CasaOS App Store
3. Configure your environment variables
4. Launch and access at `http://your-casaos-ip:3000`

## Method 1: Custom Install via UI

This is the recommended method for CasaOS users.

### Step 1: Download the Compose File

Save the following as `docker-compose.yml` on your computer:

```yaml
# Shark Fin - CasaOS Compatible Docker Compose
# For use with CasaOS Custom Install feature

name: shark-fin

services:
  postgres:
    image: postgres:15-alpine
    container_name: shark-fin-db
    restart: unless-stopped
    environment:
      POSTGRES_USER: sharkfin
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-changeme_secure_password}
      POSTGRES_DB: shark_fin
    volumes:
      - /DATA/AppData/shark-fin/postgres:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sharkfin"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - shark-fin
    x-casaos:
      envs:
        - container: POSTGRES_PASSWORD
          description:
            en_us: Database password (change this!)

  redis:
    image: redis:7-alpine
    container_name: shark-fin-redis
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - /DATA/AppData/shark-fin/redis:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - shark-fin

  backend:
    image: ghcr.io/willgillen/sharkfin/backend:latest
    container_name: shark-fin-backend
    restart: unless-stopped
    environment:
      DATABASE_URL: postgresql://sharkfin:${POSTGRES_PASSWORD:-changeme_secure_password}@postgres:5432/shark_fin
      REDIS_URL: redis://redis:6379
      SECRET_KEY: ${SECRET_KEY:-please_change_this_to_a_secure_random_string}
      ALGORITHM: HS256
      ACCESS_TOKEN_EXPIRE_MINUTES: 30
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - shark-fin
    x-casaos:
      envs:
        - container: SECRET_KEY
          description:
            en_us: JWT signing key (min 32 characters, keep secret!)

  frontend:
    image: ghcr.io/willgillen/sharkfin/frontend:latest
    container_name: shark-fin-frontend
    restart: unless-stopped
    environment:
      NEXT_PUBLIC_API_URL: http://backend:8000
    ports:
      - target: 3000
        published: "3000"
        protocol: tcp
    depends_on:
      - backend
    networks:
      - shark-fin
    x-casaos:
      ports:
        - container: "3000"
          description:
            en_us: Web UI Port

networks:
  shark-fin:
    driver: bridge

x-casaos:
  architectures:
    - amd64
    - arm64
  main: frontend
  author: Will Gillen
  category: Finance
  description:
    en_us: |
      Shark Fin is an open-source, self-hosted financial planning and budgeting
      application. Track your accounts, categorize transactions, create budgets,
      and gain insights into your spending patterns.

      Features:
      - Multi-account tracking (checking, savings, credit cards)
      - Automatic transaction categorization
      - Budget creation and monitoring
      - Financial reports and analytics
      - CSV/OFX import support
      - Payee management with merchant recognition
  developer: Will Gillen
  icon: https://raw.githubusercontent.com/willgillen/sharkfin/main/frontend/public/sharkfin_logo.png
  tagline:
    en_us: Personal finance tracking and budgeting
  title:
    en_us: Shark Fin
  index: /
  port_map: "3000"
```

### Step 2: Upload via CasaOS UI

1. Open your CasaOS dashboard in a web browser
2. Click on **App Store** in the sidebar
3. Click the **Custom Install** button (top right corner)
4. Select **Import** and upload your `docker-compose.yml` file
5. Review the configuration and click **Install**

### Step 3: Configure Environment Variables

Before starting, configure these important variables:

| Variable | Description | Action |
|----------|-------------|--------|
| `POSTGRES_PASSWORD` | Database password | **Change to a secure password** |
| `SECRET_KEY` | JWT signing key | **Change to a random 32+ character string** |

To generate a secure secret key, run this in any terminal:
```bash
openssl rand -base64 32
```

### Step 4: Start the Application

Click **Start** in CasaOS to launch all containers.

## Method 2: Command Line Installation

If you prefer command-line installation:

### Step 1: Create Directory Structure

```bash
# SSH into your CasaOS server
ssh user@your-casaos-ip

# Create app directories
mkdir -p /DATA/AppData/shark-fin/postgres
mkdir -p /DATA/AppData/shark-fin/redis
```

### Step 2: Create Compose File

```bash
# Navigate to app directory
cd /DATA/AppData/shark-fin

# Create docker-compose.yml
nano docker-compose.yml
```

Paste the compose file content from Method 1 above.

### Step 3: Create Environment File

```bash
nano .env
```

Add your configuration:
```bash
POSTGRES_PASSWORD=your_secure_database_password
SECRET_KEY=your_secure_secret_key_at_least_32_chars
```

### Step 4: Start Services

```bash
docker compose up -d
```

### Step 5: Verify Installation

```bash
# Check container status
docker compose ps

# View logs
docker compose logs -f
```

## Configuration

### Data Storage

CasaOS stores application data in `/DATA/AppData/`. Shark Fin uses:

| Path | Contents |
|------|----------|
| `/DATA/AppData/shark-fin/postgres` | PostgreSQL database files |
| `/DATA/AppData/shark-fin/redis` | Redis persistence data |

### Port Configuration

| Service | Internal Port | External Port |
|---------|---------------|---------------|
| Frontend (Web UI) | 3000 | 3000 |
| Backend API | 8000 | Not exposed (internal) |
| PostgreSQL | 5432 | Not exposed (internal) |
| Redis | 6379 | Not exposed (internal) |

To change the external port, modify the `published` value in the frontend service:

```yaml
ports:
  - target: 3000
    published: "8080"  # Change to your preferred port
    protocol: tcp
```

### Resource Limits (Optional)

For systems with limited resources, add memory limits:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```

## Accessing Shark Fin

After installation:

1. **Web Interface**: `http://your-casaos-ip:3000`
2. **Create Account**: Click "Sign up" to create your first user
3. **Start Adding Data**: Add accounts and import transactions

### Finding Your CasaOS IP

In CasaOS dashboard, your IP is shown in the top bar, or run:
```bash
hostname -I
```

## Updating

### Via CasaOS UI

1. Go to your installed apps
2. Right-click on Shark Fin
3. Select **Recreate**
4. CasaOS will pull the latest images

### Via Command Line

```bash
cd /DATA/AppData/shark-fin

# Pull latest images
docker compose pull

# Restart with new images
docker compose up -d
```

### Updating to Specific Version

Edit `docker-compose.yml` and change the image tags:

```yaml
backend:
  image: ghcr.io/willgillen/sharkfin/backend:v1.1.0

frontend:
  image: ghcr.io/willgillen/sharkfin/frontend:v1.1.0
```

Then recreate the containers.

## Backup

### Database Backup

```bash
# Create backup directory
mkdir -p /DATA/AppData/shark-fin/backups

# Backup database
docker exec shark-fin-db pg_dump -U sharkfin -Fc shark_fin > \
  /DATA/AppData/shark-fin/backups/shark_fin_$(date +%Y%m%d).dump
```

### Full Data Backup

Back up the entire AppData directory:

```bash
# Stop services first (optional but recommended)
cd /DATA/AppData/shark-fin && docker compose stop

# Create backup archive
tar -czvf /DATA/Backups/shark-fin-backup-$(date +%Y%m%d).tar.gz \
  /DATA/AppData/shark-fin/

# Restart services
docker compose start
```

### Restore from Backup

```bash
# Restore database
docker exec -i shark-fin-db pg_restore -U sharkfin -d shark_fin --clean < \
  /DATA/AppData/shark-fin/backups/shark_fin_20240101.dump
```

## Troubleshooting

### Container Won't Start

Check logs for errors:
```bash
docker logs shark-fin-backend
docker logs shark-fin-frontend
docker logs shark-fin-db
```

### Database Connection Issues

Ensure PostgreSQL is healthy:
```bash
docker exec shark-fin-db pg_isready -U sharkfin
```

### Frontend Can't Reach Backend

Verify network connectivity:
```bash
docker network inspect shark-fin_shark-fin
```

All containers should be on the same network.

### Permission Issues

If you encounter permission errors with volumes:
```bash
# Fix ownership
sudo chown -R 1000:1000 /DATA/AppData/shark-fin/
```

### Reset Everything

To start fresh:
```bash
cd /DATA/AppData/shark-fin

# Stop and remove everything
docker compose down -v

# Remove data (WARNING: deletes all data!)
rm -rf postgres/* redis/*

# Start fresh
docker compose up -d
```

### Viewing Logs in CasaOS

1. Click on the Shark Fin app in your dashboard
2. Click the **Logs** tab to view container output

## Accessing from Outside Your Network

To access Shark Fin from outside your home network:

### Option 1: Cloudflare Tunnel (Recommended)

1. Install cloudflared on your CasaOS server
2. Create a tunnel pointing to `http://localhost:3000`
3. Access via your Cloudflare domain

### Option 2: Reverse Proxy

Use CasaOS's built-in nginx or install Traefik/Caddy to handle SSL.

### Option 3: Port Forwarding

Forward port 3000 on your router (not recommended for security reasons).

---

## Resources

- [Shark Fin GitHub](https://github.com/willgillen/sharkfin)
- [CasaOS Documentation](https://wiki.casaos.io/)
- [CasaOS GitHub](https://github.com/IceWhaleTech/CasaOS)
- [Main Deployment Guide](DEPLOYMENT.md)

---

*Last Updated: February 2026*
