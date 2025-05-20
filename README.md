# Website Creator

This project provides a web-based interface to create and manage simple websites, each served on a unique port (8000–9000) by Apache2, running in a Docker container. The Flask-based UI allows users to create and delete websites, with ports reused to avoid gaps in the sequence.

## Features
- **Web UI**: Accessible on port 80, allows creating new websites with a "Create" button and deleting websites by entering their name (e.g., `site_1`).
- **Website Creation**: Each website is assigned a sequential name (`site_1`, `site_2`, etc.) and a port (e.g., `site_1` on port 8001).
- **Port Reuse**: Deleted ports are reused, ensuring no gaps (e.g., if `site_4` on port 8004 is deleted, the next site reuses 8004).
- **Apache2 Hosting**: Websites are served by Apache2 on unique ports in the range 8000–9000.
- **Persistence**: Website files are stored on the host at `/opt/website-creator`, mounted to `/var/www/html` in the container.
- **Manual IP Configuration**: Links to websites use a user-specified server IP, set via the `SERVER_IP` environment variable.
- **User Feedback**: Success/error messages for create/delete actions (e.g., "Created site_1 on port 8001", "Invalid site name").

## Prerequisites
- **Docker**: Install Docker and Docker Compose on your server.
- **Host Directory**: Create `/opt/website-creator` on the host for persistent storage.
- **Server IP**: Know your server's IP address (e.g., `192.168.1.100` for LAN or a public IP).

## Setup Instructions

1. **Clone or Create Project Directory**:
   - Create a directory named `website-creator` and place all project files (`app/`, `Dockerfile`, `apache2.conf`, `entrypoint.sh`, `docker-compose.yml`) in it.
   - Ensure the `app/` directory contains `app.py`, `ports.txt`, `static/style.css`, and `templates/index.html`.

2. **Create Host Directory**:
   ```bash
   sudo mkdir -p /opt/website-creator
   sudo chown -R $(whoami):$(whoami) /opt/website-creator
   ```
   - This directory stores website files and persists across container restarts.

3. **Set SERVER_IP Environment Variable**:
   - Create a `.env` file in the `website-creator` directory:
     ```bash
     echo "SERVER_IP=<your-server-ip>" > website-creator/.env
     ```
     Example: `SERVER_IP=192.168.1.100`
   - Replace `<your-server-ip>` with your server's LAN or public IP address (e.g., find with `ip addr show` or `curl ifconfig.me`).

4. **Build and Run with Docker Compose**:
   ```bash
   cd website-creator
   docker-compose up --build -d
   ```
   - Builds the Docker image and starts the container.
   - Maps ports: 80 (Flask UI), 5000 (Apache2 default), 8000–9000 (websites).
   - Mounts `/opt/website-creator` to `/var/www/html`.

5. **Alternative: Run with Docker**:
   If you prefer not to use Docker Compose:
   ```bash
   docker build -t website-creator .
   docker run -d -p 80:80 -p 5000:5000 -p 8000-9000:8000-9000 -v /opt/website-creator:/var/www/html -e SERVER_IP=<your-server-ip> website-creator
   ```
   Example: `-e SERVER_IP=192.168.1.100`

6. **Access the Web UI**:
   - Open a browser and navigate to `http://<your-server-ip>:80`.
   - Click "Create New Website" to generate a new site (e.g., `site_1` on `http://<your-server-ip>:8001`).
   - To delete a site, enter its name (e.g., `site_1`) in the delete form and click "Delete".
   - Check success/error messages below the form.

## Updating the Application

To apply changes to the code or configuration:
1. **Stop and Remove Containers**:
   ```bash
   cd website-creator
   docker-compose down
   ```
   Or, if using `docker run`:
   ```bash
   docker ps -q --filter ancestor=website-creator | xargs -r docker stop
   docker ps -a -q --filter ancestor=website-creator | xargs -r docker rm
   ```

2. **Remove the Image**:
   ```bash
   docker rmi website-creator
   ```

3. **Rebuild and Restart**:
   - Follow step 4 or 5 from the setup instructions above.

## Environment Variables
- **SERVER_IP** (Required):
  - The IP address of the server hosting the container (e.g., `192.168.1.100` or a public IP).
  - Used for generating website links in the UI (e.g., `http://<SERVER_IP>:8001` for `site_1`).
  - Set in `.env` file or via `-e SERVER_IP=<ip>` in `docker run`.
  - Example: `SERVER_IP=192.168.1.100`
- **DEBIAN_FRONTEND** (Optional, default: `noninteractive`):
  - Prevents interactive prompts during package installation in the Docker image.

## Notes
- **Port Usage**:
  - Port 80: Flask web UI.
  - Port 5000: Apache2 default site (serves `/var/www/html` if accessed directly).
  - Ports 8000–9000: Individual websites (e.g., `site_1` on 8001, `site_75` on 8075).
- **Port Reuse**: When a site is deleted, its port is freed and reused for the next site, starting from the lowest available port (e.g., if `site_4` on 8004 is deleted, the next site uses 8004).
- **Persistence**: Website files are stored in `/opt/website-creator` on the host. For `ports.txt` persistence, add to `docker-compose.yml`:
  ```yaml
  volumes:
    - /opt/website-creator:/var/www/html
    - /opt/website-creator/ports.txt:/app/ports.txt
  ```
  Create `/opt/website-creator/ports.txt` with:
  ```
  1
  ```
- **Security**: For production, add authentication to the Flask UI, enable HTTPS, and restrict firewall access to ports 80, 5000, and 8000–9000.
- **Permissions**: After creating/deleting websites, adjust host permissions if needed:
  ```bash
  sudo chown -R $(whoami):$(whoami) /opt/website-creator
  ```

## Troubleshooting
- **SERVER_IP Error**: If the UI fails with a "SERVER_IP must be set" error, ensure `SERVER_IP` is defined in `.env` or the `docker run` command.
- **Website Not Accessible**: Check Apache2 logs:
  ```bash
  docker exec <container-id> cat /var/log/apache2/error.log
  ```
- **Port Conflicts**: Ensure ports 80, 5000, and 8000–9000 are free on the host:
  ```bash
  netstat -tuln | grep -E '80|5000|8000:9000'
  ```
- **Permission Issues**: If Apache2 can’t access `/var/www/html`, run:
  ```bash
  sudo chmod -R 755 /opt/website-creator
  sudo chown -R www-data:www-data /opt/website-creator
  ```
- **Delete Errors**: Ensure the site name is correct (e.g., `site_1`) and exists in the UI list.
