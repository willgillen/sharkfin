FROM node:20-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci || npm install

# Development image
FROM base AS dev
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

EXPOSE 5400
ENV PORT 5400
ENV HOSTNAME "0.0.0.0"
ARG APP_VERSION=development
ENV APP_VERSION=${APP_VERSION}

ENTRYPOINT ["/bin/sh", "./entrypoint.sh"]
CMD ["npm", "run", "dev"]

# Production builder
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED 1

RUN npm run build

# Production image
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY entrypoint.sh ./

USER nextjs

EXPOSE 5400
ENV PORT 5400
ENV HOSTNAME "0.0.0.0"
ARG APP_VERSION=development
ENV APP_VERSION=${APP_VERSION}

ENTRYPOINT ["/bin/sh", "./entrypoint.sh"]
CMD ["node", "server.js"]
