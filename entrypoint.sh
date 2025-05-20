#!/bin/bash

echo "Starting entrypoint.sh"

# Fix permissions for Apache2 directories
echo "Fixing permissions for Apache2 directories..."
chown -R www-data:www-data /etc/apache2/sites-available /etc/apache2/sites-enabled
chmod -R 755 /etc/apache2/sites-available /etc/apache2/sites-enabled

# Ensure Apache2 configuration is valid
echo "Validating Apache2 configuration..."
apache2ctl configtest
if [ $? -ne 0 ]; then
    echo "Apache2 configuration test failed"
    cat /var/log/apache2/error.log
    exit 1
fi

# Start Apache2
echo "Starting Apache2..."
service apache2 start
if [ $? -ne 0 ]; then
    echo "Failed to start Apache2"
    cat /var/log/apache2/error.log
    exit 1
fi

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
if [ $? -ne 0 ]; then
    echo "Failed to start Flask app"
    exit 1
fi

echo "Both services started successfully"

# Keep container running
tail -f /var/log/apache2/access.log /var/log/apache2/error.log
