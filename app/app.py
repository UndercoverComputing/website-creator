from flask import Flask, render_template, request, redirect, url_for, flash
import os
import subprocess
import shutil
import logging
import time

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Required for flash messages

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directory for websites and port tracking
WEBSITES_DIR = "/var/www/html"
PORTS_FILE = "/app/ports.txt"
VHOSTS_DIR = "/etc/apache2/sites-available"
MAX_WEBSITES = 100  # Limit to 100 websites (ports 8001-8100)

# Require SERVER_IP environment variable
SERVER_IP = os.environ.get('SERVER_IP')
if not SERVER_IP:
    raise ValueError("SERVER_IP environment variable must be set")

# Initialize ports file if it doesn't exist
if not os.path.exists(PORTS_FILE):
    with open(PORTS_FILE, 'w') as f:
        f.write("1\n")  # Next site number
        f.write("")     # No used ports initially

def get_next_site_and_port():
    try:
        with open(PORTS_FILE, 'r') as f:
            lines = f.readlines()
            next_site_num = int(lines[0].strip())
            used_ports = []
            if len(lines) > 1 and lines[1].strip():
                used_ports = [int(p) for p in lines[1].strip().split(",") if p]
        
        # Check for gaps in site numbers
        existing_sites = []
        for f in os.listdir(VHOSTS_DIR):
            if f.startswith('site_') and f.endswith('.conf'):
                site_num = int(f.replace('site_', '').replace('.conf', ''))
                existing_sites.append(site_num)
        existing_sites.sort()
        
        # Check if maximum website limit is reached
        if len(existing_sites) >= MAX_WEBSITES:
            flash(f"Maximum number of websites ({MAX_WEBSITES}) reached", "error")
            logger.error(f"Maximum number of websites ({MAX_WEBSITES}) reached")
            return None, None, None, None
        
        # Find the first missing site number
        site_num = None
        for i in range(1, next_site_num):
            if i not in existing_sites:
                site_num = i
                break
        if site_num is None:
            site_num = next_site_num
        
        # Assign port as 8000 + site_num
        port = 8000 + site_num
        if port > 8100:  # Matches docker-compose.yml port range
            flash("No more ports available (8001-8100 used)", "error")
            logger.error("Port limit exceeded: 8001-8100 already used")
            return None, None, None, None
        
        if port in used_ports:
            # Check if port is actually in use by a valid site
            if os.path.exists(os.path.join(VHOSTS_DIR, f"site_{site_num}.conf")):
                flash(f"Port {port} is already in use by site_{site_num}", "error")
                logger.error(f"Port {port} already in use by site_{site_num}")
                return None, None, None, None
            else:
                # Port is in ports.txt but no site exists; allow reuse
                used_ports.remove(port)
                logger.info(f"Removed stale port {port} from used_ports")
        
        return site_num, port, used_ports, next_site_num
    except Exception as e:
        logger.error(f"Error in get_next_site_and_port: {str(e)}")
        flash(f"Error reading ports file: {str(e)}", "error")
        return None, None, None, None

def update_ports_file(next_site_num, used_ports):
    try:
        with open(PORTS_FILE, 'w') as f:
            f.write(f"{next_site_num}\n")
            f.write(",".join(map(str, sorted(used_ports))) if used_ports else "")
    except Exception as e:
        logger.error(f"Error updating ports file: {str(e)}")
        raise

def reload_apache():
    try:
        result = subprocess.run(['service', 'apache2', 'reload'], capture_output=True, text=True, check=True)
        logger.info(f"Apache2 reload: {result.stdout}")
        time.sleep(1)  # Brief delay to allow Apache2 to stabilize
    except subprocess.CalledProcessError as e:
        logger.error(f"Apache2 reload failed: {e.stderr}")
        raise

@app.route('/')
def index():
    websites = []
    try:
        for f in os.listdir(VHOSTS_DIR):
            if f.startswith('site_') and f.endswith('.conf'):
                site_name = f.replace('.conf', '')
                vhost_file = os.path.join(VHOSTS_DIR, f)
                try:
                    with open(vhost_file, 'r') as cf:
                        for line in cf:
                            if line.strip().startswith('Listen'):
                                port = line.strip().split()[1]
                                websites.append((site_name, port))
                                break
                except Exception as e:
                    logger.error(f"Error reading {vhost_file}: {str(e)}")
                    flash(f"Error reading config for {site_name}", "error")
        websites.sort(key=lambda x: int(x[0].replace('site_', '')))
    except Exception as e:
        logger.error(f"Error listing websites in {VHOSTS_DIR}: {str(e)}")
        flash("Error listing websites", "error")
    return render_template('index.html', websites=websites, server_ip=SERVER_IP)

@app.route('/create', methods=['POST'])
def create_website():
    site_num, port, used_ports, next_site_num = get_next_site_and_port()
    if site_num is None or port is None or used_ports is None or next_site_num is None:
        return redirect(url_for('index'))
    
    website_name = f"site_{site_num}"
    website_path = os.path.join(WEBSITES_DIR, website_name)
    vhost_file = os.path.join(VHOSTS_DIR, f"{website_name}.conf")
    
    try:
        # Create website directory
        os.makedirs(website_path, exist_ok=True)
        
        # Create index.html
        with open(os.path.join(website_path, 'index.html'), 'w') as f:
            f.write(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{website_name}</title>
            </head>
            <body>
                <h1>Welcome to {website_name}</h1>
                <p>This is website #{site_num} running on port {port}.</p>
            </body>
            </html>
            """)
        
        # Set permissions
        subprocess.run(['chown', '-R', 'www-data:www-data', website_path], check=True)
        subprocess.run(['chmod', '-R', '755', website_path], check=True)
        
        # Create virtual host configuration
        vhost_config = f"""
Listen {port}
<VirtualHost *:{port}>
    ServerAdmin webmaster@localhost
    DocumentRoot {website_path}
    ErrorLog ${{APACHE_LOG_DIR}}/error_{website_name}.log
    CustomLog ${{APACHE_LOG_DIR}}/access_{website_name}.log combined
    <Directory {website_path}>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>
</VirtualHost>
        """
        with open(vhost_file, 'w') as f:
            f.write(vhost_config)
        
        # Set permissions for vhost file
        subprocess.run(['chown', 'www-data:www-data', vhost_file], check=True)
        subprocess.run(['chmod', '644', vhost_file], check=True)
        
        # Enable the site
        result = subprocess.run(['a2ensite', website_name], capture_output=True, text=True, check=True)
        logger.info(f"a2ensite {website_name}: {result.stdout}")
        
        # Reload Apache
        reload_apache()
        
        # Update ports file only after successful creation
        used_ports.append(port)
        new_next_site_num = max(next_site_num, site_num + 1)
        update_ports_file(new_next_site_num, used_ports)
        
        flash(f"Created {website_name} on port {port}", "success")
    except subprocess.CalledProcessError as e:
        logger.error(f"Subprocess error creating {website_name}: {e.stderr}")
        flash(f"Error creating {website_name}: {e.stderr}", "error")
        # Clean up partial creation
        if os.path.exists(vhost_file):
            os.remove(vhost_file)
        if os.path.exists(website_path):
            shutil.rmtree(website_path)
    except Exception as e:
        logger.error(f"Error creating {website_name}: {str(e)}")
        flash(f"Error creating {website_name}: {str(e)}", "error")
        # Clean up partial creation
        if os.path.exists(vhost_file):
            os.remove(vhost_file)
        if os.path.exists(website_path):
            shutil.rmtree(website_path)
    
    return redirect(url_for('index'))

@app.route('/delete', methods=['POST'])
def delete_website():
    website_name = request.form.get('website_name')
    if not website_name or not website_name.startswith('site_'):
        flash("Invalid site name. Must start with 'site_' (e.g., site_1)", "error")
        return redirect(url_for('index'))
    
    vhost_file = os.path.join(VHOSTS_DIR, f"{website_name}.conf")
    website_path = os.path.join(WEBSITES_DIR, website_name)
    
    if not os.path.exists(vhost_file):
        flash(f"Site {website_name} does not exist", "error")
        return redirect(url_for('index'))
    
    try:
        # Get port from virtual host file
        port = None
        with open(vhost_file, 'r') as f:
            for line in f:
                if line.strip().startswith('Listen'):
                    port = int(line.strip().split()[1])
                    break
        if port is None:
            flash(f"Could not determine port for {website_name}", "error")
            return redirect(url_for('index'))
        
        # Disable and remove virtual host
        result = subprocess.run(['a2dissite', website_name, '--force'], capture_output=True, text=True, check=True)
        logger.info(f"a2dissite {website_name}: {result.stdout}")
        os.remove(vhost_file)
        
        # Remove website directory
        if os.path.exists(website_path):
            shutil.rmtree(website_path)
        
        # Update ports file
        with open(PORTS_FILE, 'r') as f:
            lines = f.readlines()
            next_site_num = int(lines[0].strip())
            used_ports = []
            if len(lines) > 1 and lines[1].strip():
                used_ports = [int(p) for p in lines[1].strip().split(",") if p]
        
        if port in used_ports:
            used_ports.remove(port)
        
        site_num = int(website_name.replace('site_', ''))
        if site_num == next_site_num - 1:
            next_site_num = max(1, site_num)
        
        update_ports_file(next_site_num, used_ports)
        
        # Reload Apache
        reload_apache()
        
        flash(f"Deleted {website_name} and freed port {port}", "success")
    except subprocess.CalledProcessError as e:
        logger.error(f"Subprocess error deleting {website_name}: {e.stderr}")
        flash(f"Error deleting {website_name}: {e.stderr}", "error")
    except Exception as e:
        logger.error(f"Error deleting {website_name}: {str(e)}")
        flash(f"Error deleting {website_name}: {str(e)}", "error")
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, threaded=False)  # Disable threading to reduce CPU usage