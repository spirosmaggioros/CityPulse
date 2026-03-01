#!/usr/bin/env bash
# ── init-ssl.sh ──
# Bootstrap the first SSL certificate via certbot.
# Run ONCE before starting production: ./init-ssl.sh
#
# Prerequisites:
#   - DNS for $DOMAIN must point to this server
#   - Port 80 must be reachable from the internet
#   - .env must have DOMAIN and CERTBOT_EMAIL set, DEV=false

set -euo pipefail

# Load vars from .env
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

DOMAIN="${DOMAIN:?Set DOMAIN in .env}"
EMAIL="${CERTBOT_EMAIL:?Set CERTBOT_EMAIL in .env}"
DATA_DIR="./data/certbot"

echo "==> Requesting certificate for ${DOMAIN}..."

# Ensure dirs exist
mkdir -p "${DATA_DIR}/conf" "${DATA_DIR}/www"

# Start nginx in dev mode temporarily (HTTP only) so certbot can reach /.well-known
echo "[1/3] Starting nginx (HTTP only) for ACME challenge..."
DEV=true docker compose up -d nginx

echo "[2/3] Running certbot..."
docker compose run --rm certbot \
  certbot certonly \
    --webroot \
    -w /var/www/certbot \
    -d "${DOMAIN}" \
    --email "${EMAIL}" \
    --agree-tos \
    --no-eff-email \
    --force-renewal

echo "[3/3] Restarting nginx in production mode with SSL..."
docker compose down nginx
DEV=false docker compose up -d nginx certbot

echo "==> Done! SSL is active for ${DOMAIN}"
