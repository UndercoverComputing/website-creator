# Website Creator

This project provides a web-based interface to create and manage up to 100 simple websites, each served on a unique port (8001–8100) by Apache2, running in a Docker container. The Flask-based UI allows users to create and delete websites, with ports and site names reused to avoid gaps in the sequence.

## Features
- **Web UI**: Accessible on port 80 (mapped to container port 8080), allows creating new websites with a "Create" button and deleting websites by entering their name (e.g., `site_1`).
- **Website Creation**: Each website is assigned a sequential name and port: `site_1` on port 8001, `site_2` on port 8002, ..., `site_100` on port 8100. Maximum 100 websites.
- **Port and Name Reuse**: When a site is deleted, its port and name are reused for the next site (e.g., if `site_4` on 8004 is deleted, the next site is `site_4` on 8004).
- **Apache2 Hosting**: Websites are served by Apache2 on unique ports in the range 8001–8100.
- **Persistence**: Website files and port tracking are stored on the host at `/opt/website-creator`, mounted to `/var/www/html` and `/app/ports.txt` in the container.
- **Manual IP Configuration**: Links to websites use a user-specified server IP, set via the `SERVER_IP` environment variable.
- **User Feedback**: Success/error messages for create/delete actions (e.g., "Created site_1 on port 8001", "Maximum number of websites (100) reached").
- **Autostart**: The container starts automatically on system boot and restarts unless explicitly stopped.
- **Resource Limits**: CPU and memory limits prevent system crashes on low-resource systems.

## Prerequisites
- **Docker**: Install Docker and Docker Compose V2 on your server.
- **Host Directory**: Create `/opt/website-creator` on the host for persistent storage.
- **Server IP**: Know your server's IP address (e.g., `192.168.0.22` for LAN or a public IP).
- **Git**: Required to clone the repository.
- **System Resources**: At least 2GB RAM and 1 CPU core; more recommended for stability.

## Setup Instructions for Fresh Debian Install

On a fresh Debian install (e.g., Debian 12), follow these steps to ensure a clean setup:

1. **Install Docker and Docker Compose V2**:
   ```bash
   sudo apt update
   sudo apt install -y docker.io docker-compose-v2
   sudo systemctl enable docker
   sudo systemctl start docker
   ```
   - Installs Docker and Docker Compose V2.
   - Enables Docker to start on boot.
   - Verify installation:
     ```bash
     docker --version
     docker compose version
     ```

2. **Clone the Repository**:
   ```bash
   git clone https://github.com/The-Dark-Mode/website-creator.git
   cd website-creator
   ```
   - Clones the project from GitHub and navigates to the project directory.
   - The repository contains all necessary files: `app/` (with `app.py`, `ports.txt`, `static/style.css`, `templates/index.html`), `Dockerfile`, `apache2.conf`, `entrypoint.sh`, and `docker-compose.yml`.

3. **Create Host Directory and Ports File**:
   ```bash
   sudo mkdir -p /opt/website-creator
   sudo rm -rf /opt/website-creator/ports.txt  # Remove if it exists as a directory
   echo -e "1\n" | sudo tee /opt/website-creator/ports.txt
   sudo chown -R www-data:www-data /opt/website-creator
   sudo chmod -R 755 /opt/website-creator
   ```
   - Creates `/opt/website-creator` for website files and `/app/ports.txt` for port tracking.
   - Initializes `ports.txt` with `1` (next site number) and no used ports.
   - Sets permissions for the container’s `www-data` user.

4. **Set SERVER_IP Environment Variable**:
   - Create a `.env` file in the `website-creator` directory:
     ```bash
     echo "SERVER_IP=192.168.0.22" > .env
     ```
   - Replace `192.168.0.22` with your server's LAN or public IP address. Find it with:
     ```bash
     ip addr show | grep inet
     ```
     or
     ```bash
     curl ifconfig.me  # For public IP
     ```

5. **Optimize System Resources**:
   - Increase file descriptor and socket limits to prevent networking issues:
     ```bash
     sudo sysctl -w fs.file-max=65535
     sudo sysctl -w net.core.somaxconn=65535
     echo "fs.file-max=65535" | sudo tee -a /etc/sysctl.conf
     echo "net.core.somaxconn=65535" | sudo tee -a /etc/sysctl.conf
     ```
   - Restart Docker to apply changes:
     ```bash
     sudo systemctl restart docker
     ```

6. **Build and Run with Docker Compose**:
   ```bash
   docker compose up --build -d
   ```
   - Builds the Docker image and starts the container named `website-creator`.
   - Maps ports: 80 (Flask UI, container port 8080), 5000 (Apache2 default), 8000–8100 (websites).
   - Mounts `/opt/website-creator` to `/var/www/html` and `/app/ports.txt`.
   - Sets CPU/memory limits (0.5 CPU, 512MB RAM) to prevent system crashes.
   - The `restart: unless-stopped` policy ensures the container restarts on crashes or reboots unless explicitly stopped.

7. **Alternative: Run with Docker**:
   If you prefer not to use Docker Compose:
   ```bash
   docker build -t website-creator .
   docker run -d --name website-creator --restart unless-stopped --cpus="0.5" --memory="512m" -p 80:8080 -p 5000:5000 -p 8000-8100:8000-8100 -v /opt/website-creator:/var/www/html -v /opt/website-creator/ports.txt:/app/ports.txt -e SERVER_IP=192.168.0.22 website-creator
   ```

8. **Access the Web UI**:
   - Open a browser and navigate to `http://192.168.0.22:80`.
   - Click "Create New Website" to generate a new site (e.g., `site_1` on `http://192.168.0.22:8001`). Maximum 100 websites.
   - To delete a site, enter its name (e.g., `site_1`) in the delete form and click "Delete".
   - Check success/error messages below the form.

## Updating the Application

To apply changes to the code or configuration:
1. **Pull Latest Changes**:
   ```bash
   cd website-creator
   git pull origin main
   ```

2. **Stop and Remove Containers**:
   ```bash
   docker compose down
   ```
   Or, if using `docker run`:
   ```bash
   docker stop website-creator
   docker rm website-creator
   ```

3. **Remove the Image**:
   ```bash
   docker rmi website-creator
   ```

4. **Ensure Ports File Exists**:
   - If `/opt/website-creator/ports.txt` is missing or incorrect, recreate it:
     ```bash
     sudo rm -rf /opt/website-creator/ports.txt
     echo -e "1\n" | sudo tee /opt/website-creator/ports.txt
     sudo chown www-data:www-data /opt/website-creator/ports.txt
     sudo chmod 644 /opt/website-creator/ports.txt
     ```

5. **Rebuild and Restart**:
   - Follow step 6 or 7 from the setup instructions above.

## Managing Autostart
- **Check Container Restart Policy**:
  ```bash
  docker inspect website-creator | grep -i restart
  ```
  Should show `"RestartPolicy": { "Name": "unless-stopped" }`.
- **Disable Autostart**:
  To prevent the container from restarting on boot:
  ```bash
  docker update --restart=no website-creator
  ```
  Or edit `docker-compose.yml` to remove `restart: unless-stopped` and redeploy:
  ```bash
  docker compose down
  docker compose up -d
  ```
- **Stop Container Without Restarting**:
  ```bash
  docker stop website-creator
  ```
  The container will not restart until you run `docker start website-creator` or reboot the server.
- **Verify Docker Runs on Boot**:
  Reboot the server and check if the container is running:
  ```bash
  sudo reboot
  # After reboot
  docker ps
  ```
  Should list `website-creator` as running.

## Environment Variables
- **SERVER_IP** (Required):
  - The IP address of the server hosting the container (e.g., `192.168.0.22` or a public IP).
  - Used for generating website links in the UI (e.g., `http://192.168.0.22:8001` for `site_1`).
  - Set in `.env` file or via `-e SERVER_IP=<ip>` in `docker run`.
  - Example: `SERVER_IP=192.168.0.22`
- **DEBIAN_FRONTEND** (Optional, default: `noninteractive`):
  - Prevents interactive prompts during package installation in the Docker image.

## Notes
- **Container Name**: The container is named `website-creator` (set in `docker-compose.yml`). If using `docker run`, the `--name website-creator` flag ensures the same name.
- **Port Usage**:
  - Host port 80: Flask web UI (mapped to container port 8080).
  - Port 5000: Apache2 default site (serves `/var/www/html` if accessed directly).
  - Ports 8001–8100: Individual websites (e.g., `site_1` on 8001, `site_2` on 8002). Maximum 100 websites.
- **Port and Name Reuse**: When a site is deleted, its port and name are reused for the next site (e.g., if `site_4` on 8004 is deleted, the next site is `site_4` on 8004).
- **Persistence**: Website files and `ports.txt` are stored in `/opt/website-creator` on the host. Ensure `/opt/website-creator/ports.txt` exists as a file before running the container.
- **Ports File Format**: `ports.txt` has two lines:
  - First line: Next site number (e.g., `2` for `site_2` if no gaps).
  - Second line: Comma-separated used ports (e.g., `8001,8002`) or empty if no ports are used.
- **Website Limit**: The application is limited to 100 websites (ports 8001–8100). Attempting to create more will show an error: "Maximum number of websites (100) reached".
- **Security**: For production, add authentication to the Flask UI, enable HTTPS, and restrict firewall access to ports 80, 5000, and 8000–8100.
- **Resource Limits**: The container is limited to 0.5 CPU cores and 512MB RAM to prevent system crashes on low-memory systems (e.g., 2GB RAM).
- **Fresh Install Notes**: On a fresh Debian install, ensure Docker and Docker Compose V2 are installed, and system resource limits (file descriptors, sockets) are increased to avoid networking issues.
- **Permissions**: After creating/deleting websites, adjust host permissions if needed:
  ```bash
  sudo chown -R www-data:www-data /opt/website-creator
  sudo chmod -R 755 /opt/website-creator
  ```

## Troubleshooting
- **Networking Errors (e.g., "failed to start userland proxy")**:
  - Verify no processes are using ports 80, 5000, or 8000–8100:
    ```bash
    sudo netstat -tuln | grep -E '80|5000|8[0-1][0-9]{2}'
    ```
    If a port (e.g., 8670) is in use, identify and stop the process:
    ```bash
    sudo lsof -i :8670
    sudo kill -9 <pid>
    ```
  - Clear stale Docker networks and containers:
    ```bash
    docker compose down
    docker rm -f website-creator
    docker network ls
    docker network rm website-creator_default
    ```
  - Check system resource limits (file descriptors, sockets):
    ```bash
    ulimit -n
    ```
    If low (e.g., <4096), increase:
    ```bash
    sudo sysctl -w fs.file-max=65535
    sudo sysctl -w net.core.somaxconn=65535
    echo "fs.file-max=65535" | sudo tee -a /etc/sysctl.conf
    echo "net.core.somaxconn=65535" | sudo tee -a /etc/sysctl.conf
    ```
  - Restart Docker daemon:
    ```bash
    sudo systemctl restart docker
    ```
  - Check Docker daemon logs for networking issues:
    ```bash
    sudo journalctl -u docker
    ```
  - Try a narrower port range (e.g., `8000-8020:8000-8020`) in `docker-compose.yml` and update `app.py` to match (change `port > 8100` to `port > 8020` and `MAX_WEBSITES = 20`):
    ```bash
    nano docker-compose.yml
    nano app/app.py
    docker compose down
    docker compose up --build -d
    ```
- **System Crashes (High RAM/CPU Usage)**:
  - Check resource usage during site creation:
    ```bash
    top
    ```
    Look for `apache2`, `python3` (Flask), or `docker` processes consuming excessive CPU/memory.
  - Verify container resource limits:
    ```bash
    docker inspect website-creator | grep -i -E 'cpulimit|memorylimit'
    ```
    Should show `Cpus: 0.5`, `Memory: 536870912` (512MB).
  - Reduce load by limiting simultaneous site creations (wait a few seconds between clicks).
  - If crashes persist, lower limits in `docker-compose.yml` (e.g., `cpus: '0.3'`, `memory: 256M`) and redeploy:
    ```bash
    docker compose down
    docker compose up -d
    ```
  - Check for other running containers or services:
    ```bash
    docker ps
    sudo systemctl list-units --type=service --state=running
    ```
    Stop unnecessary services:
    ```bash
    sudo systemctl stop <service-name>
    ```
- **Maximum Website Limit Reached**:
  - If you see "Maximum number of websites (100) reached", delete existing sites to free up ports:
    ```bash
    curl -X POST -d "website_name=site_100" http://192.168.0.22:80/delete
    ```
    Or use the UI to delete sites.
  - Verify available ports:
    ```bash
    cat /opt/website-creator/ports.txt
    docker exec website-creator ls /etc/apache2/sites-available
    ```
- **Slow `docker stop website-creator`**:
  - Increase Docker stop timeout:
    ```bash
    docker stop --time=30 website-creator
    ```
    Uses 30 seconds instead of the default 10 seconds.
  - Check if Apache2 or Flask is hanging:
    ```bash
    docker logs website-creator
    docker exec website-creator ps aux | grep -E 'apache2|python3'
    ```
    If processes persist, manually kill:
    ```bash
    docker exec website-creator pkill -TERM apache2
    docker exec website-creator pkill -TERM python3
    ```
  - Verify graceful shutdown in logs:
    ```bash
    docker logs website-creator | grep "Stopping services"
    ```
  - If slow shutdown persists, check Apache2 connections:
    ```bash
    docker exec website-creator netstat -tuln | grep -E '5000|8001'
    ```
    Close lingering connections:
    ```bash
    docker exec website-creator apache2ctl graceful-stop
    ```
- **Intermittent Site Creation Failures**:
  - Check logs for errors:
    ```bash
    docker logs website-creator | grep ERROR
    ```
  - Verify `ports.txt` consistency:
    ```bash
    cat /opt/website-creator/ports.txt
    ```
    If incorrect (e.g., lists ports without corresponding sites), reset:
    ```bash
    sudo rm -rf /opt/website-creator/ports.txt
    echo -e "1\n" | sudo tee /opt/website-creator/ports.txt
    sudo chown www-data:www-data /opt/website-creator/ports.txt
    sudo chmod 644 /opt/website-creator/ports.txt
    docker restart website-creator
    ```
  - Check virtual host files:
    ```bash
    docker exec website-creator ls /etc/apache2/sites-available
    ```
    Should list `site_1.conf`, etc. If missing, check permissions:
    ```bash
    docker exec website-creator ls -l /etc/apache2/sites-available
    ```
    Fix if needed:
    ```bash
    docker exec website-creator chown -R www-data:www-data /etc/apache2/sites-available
    docker exec website-creator chmod -R 644 /etc/apache2/sites-available
    ```
- **Websites Not Listed in UI**:
  - Verify virtual host files:
    ```bash
    docker exec website-creator ls /etc/apache2/sites-available
    ```
    Should list `site_1.conf`, etc.
  - Check Flask logs:
    ```bash
    docker logs website-creator | grep ERROR
    ```
- **Websites Only Accessible via Port 5000**:
  - Verify virtual host sites are enabled:
    ```bash
    docker exec website-creator ls /etc/apache2/sites-enabled
    ```
    Enable manually if needed:
    ```bash
    docker exec website-creator a2ensite site_1
    docker exec website-creator service apache2 reload
    ```
  - Test website ports:
    ```bash
    curl http://192.168.0.22:8001
    ```
    Should return `site_1`’s `index.html`.
- **Container Not Starting on Boot**:
  - Verify Docker is enabled:
    ```bash
    sudo systemctl is-enabled docker
    ```
    Enable if needed:
    ```bash
    sudo systemctl enable docker
    sudo systemctl enable containerd
    ```
- **Port Conflicts**:
  - Check host and container ports:
    ```bash
    sudo netstat -tuln | grep -E '80|5000|8[0-1][0-9]{2}'
    docker exec website-creator netstat -tuln
    ```
    Resolve conflicts:
    ```bash
    sudo lsof -i :8001
    sudo kill <pid>
    ```
- **Permission Issues**:
  - Fix permissions:
    ```bash
    sudo chown -R www-data:www-data /opt/website-creator
    sudo chmod -R 755 /opt/website-creator
    ```