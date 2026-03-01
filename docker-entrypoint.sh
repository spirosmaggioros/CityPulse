#!/bin/sh
set -e

if [ "$DEV" = "true" ]; then
  echo "[nginx] Running in DEVELOPMENT mode"
  cp /etc/nginx/templates/nginx.dev.conf   /etc/nginx/nginx.conf
  cp /etc/nginx/templates/default.dev.conf /etc/nginx/conf.d/default.conf
else
  echo "[nginx] Running in PRODUCTION mode (SSL)"
  cp /etc/nginx/templates/nginx.prod.conf  /etc/nginx/nginx.conf
  DOMAIN="${DOMAIN:-localhost}"
  sed "s/\${DOMAIN}/$DOMAIN/g" /etc/nginx/templates/default.prod.conf \
    > /etc/nginx/conf.d/default.conf
fi

exec nginx -g "daemon off;"
