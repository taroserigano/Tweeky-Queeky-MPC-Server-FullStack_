#!/bin/sh

# Default values if not set
BACKEND_HOST=${BACKEND_HOST:-fastapi-backend}
BACKEND_PORT=${BACKEND_PORT:-5000}

# Substitute environment variables in nginx config
envsubst '${BACKEND_HOST} ${BACKEND_PORT}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

# Start nginx
nginx -g 'daemon off;'
