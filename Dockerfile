# ============= Stage 1: Build React app with Node.js =============
FROM node:25-alpine3.22 AS builder

WORKDIR /app/frontend

# Copy frontend files
COPY frontend/package*.json ./
RUN npm ci

COPY frontend/src ./src
COPY frontend/public ./public
COPY frontend/index.html .
COPY frontend/.env .
COPY frontend/vite.config.js .
COPY frontend/eslint.config.js .

# Build for production - output goes to ./dist
RUN npm run build

# Verify the build output
RUN ls -la dist/

# ============= Stage 2: Final Nginx image =============
FROM nginx:1.29.5-alpine

# DEV=true → development config, DEV=false → production with SSL
ARG DEV=true
ENV DEV=${DEV}

# Create a non-root user for running nginx
RUN addgroup -g 1001 -S www && \
    adduser -S -u 1001 -G www www

# Copy built app from builder
COPY --from=builder /app/frontend/dist /usr/share/nginx/html

# Copy ALL nginx config variants into /etc/nginx/templates (not conf.d, to avoid
# auto-include and to survive container restarts)
RUN mkdir -p /etc/nginx/templates
COPY nginx/nginx.conf        /etc/nginx/templates/nginx.dev.conf
COPY nginx/nginx.prod.conf   /etc/nginx/templates/nginx.prod.conf
COPY nginx/default.dev.conf  /etc/nginx/templates/default.dev.conf
COPY nginx/default.prod.conf /etc/nginx/templates/default.prod.conf

# Remove the base-image default server block so it doesn't conflict
RUN rm -f /etc/nginx/conf.d/default.conf

# Create directories and set permissions
RUN mkdir -p /var/run/nginx /var/www/certbot && \
    chmod -R 555 /usr/share/nginx/html && \
    chmod -R 755 /var/cache/nginx && \
    chmod -R 755 /var/log/nginx

# Entrypoint selects the right config based on $DEV
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost/ || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]
