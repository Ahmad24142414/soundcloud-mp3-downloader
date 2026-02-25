"""
gunicorn_config.py - Gunicorn Configuration for Production Deployment
======================================================================
Educational Project - VPS Deployment Configuration

This configuration file sets up Gunicorn for production use.
Use with: gunicorn -c gunicorn_config.py app:app

For Nginx reverse proxy setup, see the deployment instructions in README.md
"""

import multiprocessing
import os

# =============================================================================
# Server Socket
# =============================================================================

# Bind to all interfaces on port 8000
# Nginx will proxy requests to this port
bind = os.environ.get('GUNICORN_BIND', '0.0.0.0:8000')

# Number of pending connections (queue size)
backlog = 2048

# =============================================================================
# Worker Processes
# =============================================================================

# Number of worker processes
# Recommended formula: (2 x $num_cores) + 1
workers = os.environ.get('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1)

# Worker class - sync workers are suitable for this application
worker_class = 'sync'

# Maximum requests per worker before restart (prevents memory leaks)
max_requests = 1000
max_requests_jitter = 50

# Worker timeout (seconds) - increase for slow downloads
timeout = 300

# Keep-alive connections timeout
keepalive = 5

# =============================================================================
# Security
# =============================================================================

# Limit request line size (prevent attacks)
limit_request_line = 4094

# Limit request fields
limit_request_fields = 100

# Limit request field size
limit_request_field_size = 8190

# =============================================================================
# Server Mechanics
# =============================================================================

# Daemonize the Gunicorn process (set to False if using systemd)
daemon = False

# PID file location
pidfile = None

# User and group to run workers as (uncomment and set for production)
# user = 'www-data'
# group = 'www-data'

# Umask for file permissions
umask = 0

# Working directory
chdir = os.path.dirname(os.path.abspath(__file__))

# =============================================================================
# Logging
# =============================================================================

# Access log file (- for stdout)
accesslog = '-'

# Error log file (- for stderr)
errorlog = '-'

# Log level
loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info')

# Access log format
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# =============================================================================
# Process Naming
# =============================================================================

# Process name prefix
proc_name = 'soundcloud-downloader'

# =============================================================================
# Hooks (Optional)
# =============================================================================

def on_starting(server):
    """Called just before the master process is initialized."""
    print("Starting SoundCloud Downloader Server...")

def on_exit(server):
    """Called just before exiting Gunicorn."""
    print("Shutting down SoundCloud Downloader Server...")

def worker_int(worker):
    """Called when a worker receives SIGINT or SIGQUIT."""
    print(f"Worker {worker.pid} received interrupt signal")
