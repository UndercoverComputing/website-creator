# Website Creator

This project provides a web-based interface to create and manage simple websites, each served on a unique port (8001–9000) by Apache2, running in a Docker container. The Flask-based UI allows users to create and delete websites, with ports and site names reused to avoid gaps in the sequence.

## Features
- **Web UI**: Accessible on port 80 (mapped to container port 8080), allows creating new websites with a "Create" button and deleting websites by entering their name (e.g., `site_1`).
- **Website Creation**: Each website is assigned a sequential name and port: `site_1` on port 8001, `site_2` on port 8002, ..., `site_43` on port 8043, etc.
- **Port and Name Reuse**: When a site is deleted, its port and name are reused for the next site (e.g., if `site_4` on 8004 is deleted, the next site is `site_4` on 8004).
- **Apache2 Hosting**: Websites are served by Apache2 on unique ports in the range 8001–9000.
- **Persistence**: Website files and port tracking are stored on the host at `/opt/website-creator`, mounted to `/var/www/html` and `/app/ports.txt` in the container.
- **Manual IP Configuration**: Links to websites use a user-specified server IP, set via the `SERVER_IP` environment variable.
- **User Feedback**: Success/error messages for create/delete actions (e.g., "Created site_1 on port 8001", "Invalid site name").
- **Autostart**: The container starts automatically on system boot and restarts unless explicitly stopped.

## Prerequisites
- **Docker**: Install Docker and Docker Compose on your server.
- **Host Directory**: Create `/opt/website-creator` on the host for persistent storage.
- **Server IP**: Know your server's IP address (e.g., `192.168.0.22` for LAN or a public IP).
- **Git**: Required to clone the repository.

## Setup Instructions

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/The-Dark-Mode/website-creator.git
   cd website-creator
   ```
   - Clones the project from GitHub and navigates to the project directory.
   - The repository contains all necessary files: `app/` (with `app.py`, `ports.txt`, `static/style.css`, `templates/index.html`), `Dockerfile`, `apache2.conf`, `entrypoint.sh`, and `docker-compose.yml`.

2. **Create Host Directory and Ports File**:
   ```bash
   sudo mkdir -p /opt/website-creator
   sudo rm -rf /opt/website-creator/ports.txt  # Remove if it exists as a directory
   echo -e "1\n" | sudo tee /opt/website-creator/ports.txt
   sudo chown -R www-data:www-data /opt/website-creator
   sudo chmod -R 755 /opt/website-creator
   ```
   - Creates `/opt/website-creator` for website files and `/opt/website-creator/ports.txt` for port tracking.
   - Initializes `ports.txt` with `1` (next site number) and no used ports.
   - Sets permissions for the container’s `www-data` user.

3. **Set SERVER_IP Environment Variable**:
   - Create a `.env` file in the `website-creator` directory:
     ```bash
     echo "SERVER_IP=<your-server-ip>" > .env
     ```
     Example: `SERVER_IP=192.168.0.22`
   - Replace `<your-server-ip>` with your server's LAN or public IP address. Find it with:
     ```bash
     ip addr show | grep inet
     ```
     or
     ```bash
     curl ifconfig.me  # For public IP
     ```

4. **Enable Docker on System Startup**:
   - Ensure the Docker service starts when the server boots:
     ```bash
     sudo systemctl enable docker
     sudo systemctl enable containerd
     ```
   - Verify Docker is enabled:
     ```bash
     sudo systemctl is-enabled docker
     ```
     Should output `enabled`.

5. **Build and Run with Docker Compose**:
   ```bash
   docker-compose up --build -d
   ```
   - Builds the Docker image and starts the container named `website-creator`.
   - Maps ports: 80 (Flask UI, container port 8080), 5000 (Apache2 default), 8000–9000 (websites).
   - Mounts `/opt/website-creator` to `/var/www/html` and `/app/ports.txt`.
   - The `restart: unless-stopped` policy ensures the container restarts on crashes or reboots unless explicitly stopped.

6. **Alternative: Run with Docker**:
   If you prefer not to use Docker Compose:
   ```bash
   docker build -t website-creator .
   docker run -d --name website-creator --restart unless-stopped -p 80:8080 -p 5000:5000 -p 8000-9000:8000-9000 -v /opt/website-creator:/var/www/html -v /opt/website-creator/ports.txt:/app/ports.txt -e SERVER_IP=<your-server-ip> website-creator
   ```
   Example: `-e SERVER_IP=192.168.0.22`

7. **Access the Web UI**:
   - Open a browser and navigate to `http://<your-server-ip>:80`.
   - Click "Create New Website" to generate a new site (e.g., `site_1` on `http://<your-server-ip>:8001`).
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
   docker-compose down
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
   - Follow step 5 or 6 from the setup instructions above.

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
  docker-compose down
  docker-compose up -d
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
  - Used for generating website links in the UI (e.g., `http://<SERVER_IP>:8001` for `site_1`).
  - Set in `.env` file or via `-e SERVER_IP=<ip>` in `docker run`.
  - Example: `SERVER_IP=192.168.0.22`
- **DEBIAN_FRONTEND** (Optional, default: `noninteractive`):
  - Prevents interactive prompts during package installation in the Docker image.

## Notes
- **Container Name**: The container is named `website-creator` (set in `docker-compose.yml`). If using `docker run`, the `--name website-creator` flag ensures the same name.
- **Port Usage**:
  - Host port 80: Flask web UI (mapped to container port 8080).
  - Port 5000: Apache2 default site (serves `/var/www/html` if accessed directly).
  - Ports 8001–9000: Individual websites (e.g., `site_1` on 8001, `site_2` on 8002).
- **Port and Name Reuse**: When a site is deleted, its port and name are reused for the next site (e.g., if `site_4` on 8004 is deleted, the next site is `site_4` on 8004).
- **Persistence**: Website files and `ports.txt` are stored in `/opt/website-creator` on the host. Ensure `/opt/website-creator/ports.txt` exists as a file before running the container.
- **Ports File Format**: `ports.txt` has two lines:
  - First line: Next site number (e.g., `2` for `site_2` if no gaps).
  - Second line: Comma-separated used ports (e.g., `8001,8002`) or empty if no ports are used.
- **Security**: For production, add authentication to the Flask UI, enable HTTPS, and restrict firewall access to ports 80, 5000, and 8000–9000.
- **Permissions**: After creating/deleting websites, adjust host permissions if needed:
  ```bash
  sudo chown -R www-data:www-data /opt/website-creator
  sudo chmod -R 755 /opt/website-creator
  ```

## Troubleshooting
- **Websites Not Listed in UI**:
  - Check if virtual host files exist:
    ```bash
    docker exec website-creator ls /etc/apache2/sites-available
    ```
    Should list `site_1.conf`, `site_2.conf`, etc.
  - Verify Flask can read virtual host files:
    ```bash
    docker exec website-creator cat /etc/apache2/sites-available/site_1.conf
    ```
    If permission denied, fix permissions:
    ```bash
    docker exec website-creator chmod -R 644 /etc/apache2/sites-available
    docker exec website-creator chown -R www-data:www-data /etc/apache2/sites-available
    ```
  - Check Flask logs for errors:
    ```bash
    docker logs website-creator | grep ERROR
    ```
- **Websites Only Accessible via Port 5000**:
  - Verify virtual host sites are enabled:
    ```bash
    docker exec website-creator ls /etc/apache2/sites-enabled
    ```
    Should list `site_1.conf`, etc. If empty, enable manually:
    ```bash
    docker exec website-creator a2ensite site_1
    docker exec website-creator service apache2 reload
    ```
  - Check Apache2 configuration:
    ```bash
    docker exec website-creator apache2ctl configtest
    ```
    If errors, inspect:
    ```bash
    docker exec website-creator cat /var/log/apache2/error.log
    ```
  - Verify port mappings:
    ```bash
    docker port website-creator
    ```
    Should show `80->8080`, `5000->5000`, `8000-9000->8000-9000`.
  - Test website ports directly:
    ```bash
    curl http://192.168.0.22:8001
    ```
    Should return `site_1`’s `index.html`. If it fails, check Apache2 logs:
    ```bash
    docker exec website-creator cat /var/log/apache2/error.log
    ```
- **Container Not Starting on Boot**:
  - Verify Docker is enabled:
    ```bash
    sudo systemctl is-enabled docker
    ```
    If `disabled`, enable it:
    ```bash
    sudo systemctl enable docker
    sudo systemctl enable containerd
    ```
  - Check container restart policy:
    ```bash
    docker inspect website-creator | grep -i restart
    ```
    Should show `"unless-stopped"`.
  - Ensure `docker-compose.yml` is in the correct directory and run:
    ```bash
    cd ~/website-creator
    docker-compose up -d
    ```
- **Incorrect Site Name or Port**:
  - If sites are created with wrong names or ports, check `ports.txt`:
    ```bash
    cat /opt/website-creator/ports.txt
    ```
    It should start with `1` for a fresh setup and list correct ports (e.g., `8001` for `site_1`). Fix it:
    ```bash
    sudo rm -rf /opt/website-creator/ports.txt
    echo -e "1\n" | sudo tee /opt/website-creator/ports.txt
    sudo chown www-data:www-data /opt/website-creator/ports.txt
    sudo chmod 644 /opt/website-creator/ports.txt
    docker restart website-creator
    ```
  - Verify virtual host files:
    ```bash
    docker exec website-creator ls /etc/apache2/sites-available
    ```
    Ensure files match expected names (e.g., `site_1.conf`) and ports.
- **Internal Server Error on Create**:
  - Check logs for `IndexError` or issues with `ports.txt`:
    ```bash
    docker logs website-creator
    ```
    If you see `IndexError: list index out of range`, the `ports.txt` file is malformed. Verify its content:
    ```bash
    cat /opt/website-creator/ports.txt
    ```
    It should have two lines, e.g.:
    ```
    2
    8001
    ```
    If it’s only one line, fix it as above.
  - Test the create function manually:
    ```bash
    docker exec -it website-creator python3 /app/app.py
    ```
- **Unable to Connect to Website**:
  - Check container logs for errors:
    ```bash
    docker logs website-creator
    ```
    If you see "Address already in use" or "Port 8080 is in use", check for conflicting processes:
    ```bash
    docker exec website-creator netstat -tuln | grep 8080
    docker exec website-creator ps aux | grep -E 'flask|apache2'
    ```
  - Verify Flask and Apache2 are running:
    ```bash
    docker exec -it website-creator /bin/bash
    ps aux | grep flask
    ps aux | grep apache2
    ```
  - Ensure host port 80 is open:
    ```bash
    netstat -tuln | grep 80
    sudo lsof -i :80
    ```
    If blocked, allow it:
    ```bash
    sudo ufw allow 80
    ```
  - Verify `.env` file has a valid `SERVER_IP`:
    ```bash
    cat .env
    ```
- **No Logs Output**: If `docker logs website-creator` is empty, the entrypoint script may have failed. Run it manually:
  ```bash
  docker exec -it website-creator /bin/bash
  /entrypoint.sh
  ```
- **SERVER_IP Error**: If the UI fails with a "SERVER_IP must be set" error, ensure `SERVER_IP` is defined in `.env` or the `docker run` command.
- **Apache2 Warning**: If logs show "Could not reliably determine the server's fully qualified domain name, using 172.x.x.x", this is harmless and unrelated to `SERVER_IP`. It’s suppressed by `ServerName localhost` in `apache2.conf`.
- **Port Conflicts**: Ensure ports 80, 5000, and 8000–9000 are free on the host:
  ```bash
  netstat -tuln | grep -E '80|5000|8000:9000'
  ```
- **Permission Issues**: If Apache2 or Flask can’t access `/var/www/html` or `/app/ports.txt`, run:
  ```bash
  sudo chmod -R 755 /opt/website-creator
  sudo chown -R www-data:www-data /opt/website-creator
  ```
- **Ports File Issue**: If `/opt/website-creator/ports.txt` is a directory or malformed, recreate it:
  ```bash
  sudo rm -rf /opt/website-creator/ports.txt
  echo -e "1\n" | sudo tee /opt/website-creator/ports.txt
  sudo chown www-data:www-data /opt/website-creator/ports.txt
  sudo chmod 644 /opt/website-creator/ports.txt
  ```
- **Delete Errors**: Ensure the site name is correct (e.g., `site_1`) and exists in the UI list.
