#!/bin/sh
set -e

if [ "$DEV" = "true" ]; then
  echo "[nginx] Running in DEVELOPMENT mode"
  cp /etc/nginx/templates/nginx.dev.conf   /etc/nginx/nginx.conf
  cp /etc/nginx/templates/default.dev.conf /etc/nginx/conf.d/default.conf
else
  echo "[nginx] Running in PRODUCTION mode (SSL)"
  cp /etc/nginx/templates/nginx.prod.conf  /etc/nginx/nginx.conf
  cp /etc/nginx/templates/security.prod.conf /etc/nginx/snippets/security.conf

  DOMAIN="${DOMAIN:-localhost}"
  CERT_DIR="/etc/nginx/ssl/live/${DOMAIN}"

  # Bootstrap: generate a temporary self-signed cert so nginx can start
  # and serve the ACME challenge. Certbot will replace it with a real one.
  if [ ! -f "${CERT_DIR}/fullchain.pem" ]; then
    echo "[nginx] No SSL certificate found — generating temporary self-signed cert..."
    mkdir -p "${CERT_DIR}"
    openssl req -x509 -nodes -days 1 -newkey rsa:2048 \
      -keyout "${CERT_DIR}/privkey.pem" \
      -out    "${CERT_DIR}/fullchain.pem" \
      -subj   "/CN=${DOMAIN}" 2>/dev/null
  fi

  sed -i "s/\${DOMAIN}/$DOMAIN/g" /etc/nginx/nginx.conf
fi

exec nginx -g "daemon off;"
