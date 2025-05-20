FROM ubuntu:20.04

# Set environment variables to avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install Apache2, Python, and dependencies
RUN apt-get update && apt-get install -y \
    apache2 \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install Flask
RUN pip3 install flask

# Copy application files
COPY app /app
COPY apache2.conf /etc/apache2/sites-available/000-default.conf
COPY entrypoint.sh /entrypoint.sh

# Create and set permissions for websites directory
RUN mkdir -p /var/www/html && \
    chown -R www-data:www-data /var/www/html && \
    chmod -R 755 /var/www/html

# Enable Apache2 modules
RUN a2enmod rewrite

# Expose Flask port and website ports
EXPOSE 80 5000 8000-9000

# Make entrypoint executable
RUN chmod +x /entrypoint.sh

# Start services
CMD ["/entrypoint.sh"]
