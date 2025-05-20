#!/bin/bash

echo "Starting entrypoint.sh"

# Start Apache2 in the foreground
echo "Starting Apache2..."
service apache2 start
if [ $? -ne 0 ]; then
    echo "Failed to start Apache2"
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
