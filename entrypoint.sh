#!/bin/bash

echo "Starting entrypoint.sh"

# Fix permissions for Apache2 directories
echo "Fixing permissions for Apache2 directories..."
chown -R www-data:www-data /etc/apache2/sites-available /etc/apache2/sites-enabled
chmod -R 755 /etc/apache2/sites-available /etc/apache2/sites-enabled
chown -R www-data:www-data /var/www/html
chmod -R 755 /var/www/html

# Ensure Apache2 configuration is valid
echo "Validating Apache2 configuration..."
apache2ctl configtest
if [ $? -ne 0 ]; then
    echo "Apache2 configuration test failed"
    cat /var/log/apache2/error.log
    exit 1
fi

# Start Apache2 in the foreground to handle shutdown signals
echo "Starting Apache2 in foreground..."
/usr/sbin/apache2ctl -D FOREGROUND &
APACHE_PID=$!

# Enable all virtual host sites
echo "Enabling all virtual host sites..."
for site in /etc/apache2/sites-available/site_*.conf; do
    if [ -f "$site" ]; then
        site_name=$(basename "$site" .conf)
        a2ensite "$site_name" || {
            echo "Failed to enable $site_name"
            cat /var/log/apache2/error.log
            exit 1
        }
    fi
done

# Reload Apache2
echo "Reloading Apache2..."
service apache2 reload
if [ $? -ne 0 ]; then
    echo "Failed to reload Apache2"
    cat /var/log/apache2/error.log
    exit 1
fi

# Start Flask app
echo "Starting Flask app..."
python3 /app/app.py &
FLASK_PID=$!

# Trap SIGTERM to gracefully shut down Apache2 and Flask
trap 'echo "Stopping services..."; kill -TERM $APACHE_PID $FLASK_PID; wait $APACHE_PID $FLASK_PID; exit 0' SIGTERM

# Wait for processes to keep container running
wait $APACHE_PID $FLASK_PID