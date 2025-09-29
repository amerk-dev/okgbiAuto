#!/bin/sh

# Get credentials from environment variables
USERNAME=${NGINX_BASIC_AUTH_USER:-admin}
PASSWORD=${NGINX_BASIC_AUTH_PASSWORD:-admin}

# Install apache2-utils if htpasswd is not available
if ! command -v htpasswd >/dev/null 2>&1; then
    echo "Installing apache2-utils for htpasswd..."
    apk add --no-cache apache2-utils
fi

# Generate htpasswd file
htpasswd -bc /etc/nginx/.htpasswd "$USERNAME" "$PASSWORD"

echo "Generated .htpasswd file with username: $USERNAME"
