# SoundCloud MP3 Downloader

> **Educational Project** - Academic Demonstration of Web Development Concepts

A Flask-based web application that demonstrates backend automation using yt-dlp, content management via admin panel, and SEO implementation.

## Features

### User Side
- SEO-optimized public homepage
- SoundCloud track URL input
- MP3 download using yt-dlp
- Loading indicator during processing
- Clear error handling
- Mobile-responsive design

### Admin Panel
- Secure login authentication
- Dashboard with download statistics
- SEO meta tags management
- Content management (titles, descriptions)
- Feature toggle (enable/disable downloader)
- Download logs viewer
- Password management

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3 + Flask |
| Database | SQLite |
| Audio Processing | yt-dlp + FFmpeg |
| Frontend | HTML, CSS, JavaScript |
| Production Server | Gunicorn + Nginx |

## Project Structure

```
soundcloud-downloader-3d/
├── app.py                  # Main Flask application
├── models.py               # Database models (SQLAlchemy)
├── requirements.txt        # Python dependencies
├── gunicorn_config.py      # Production server config
├── README.md               # This file
│
├── templates/              # HTML templates
│   ├── index.html          # Public homepage
│   ├── admin_login.html    # Admin login page
│   ├── admin_dashboard.html # Admin dashboard
│   ├── admin_settings.html # Settings management
│   ├── admin_logs.html     # Download logs viewer
│   ├── admin_password.html # Password change page
│   ├── 404.html            # Error page
│   └── 500.html            # Error page
│
├── static/                 # Static assets
│   └── css/
│       ├── style.css       # Public styles
│       └── admin.css       # Admin panel styles
│
└── downloads/              # Downloaded files (auto-created)
```

## Installation

### Prerequisites

1. **Python 3.8+**
2. **FFmpeg** - Required for audio processing
3. **yt-dlp** - Included in requirements.txt

### Local Development Setup

```bash
# Clone or navigate to the project directory
cd soundcloud-downloader-3d

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server
python app.py
```

The application will be available at `http://localhost:5000`

### Default Admin Credentials

- **Username:** `admin`
- **Password:** `admin123`

> ⚠️ **Important:** Change the default password immediately after first login!

## Production Deployment (VPS)

### 1. Install System Dependencies

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv ffmpeg nginx

# CentOS/RHEL
sudo yum install python3 python3-pip ffmpeg nginx
```

### 2. Setup Application

```bash
# Create application directory
sudo mkdir -p /var/www/soundcloud-downloader
cd /var/www/soundcloud-downloader

# Copy project files
# Upload your project files here

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
# Create environment file
sudo nano /var/www/soundcloud-downloader/.env

# Add these variables:
SECRET_KEY=your-very-secure-secret-key-change-this
GUNICORN_WORKERS=4
GUNICORN_BIND=127.0.0.1:8000
```

### 4. Create Systemd Service

```bash
sudo nano /etc/systemd/system/soundcloud-downloader.service
```

```ini
[Unit]
Description=SoundCloud MP3 Downloader
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/soundcloud-downloader
Environment="PATH=/var/www/soundcloud-downloader/venv/bin"
EnvironmentFile=/var/www/soundcloud-downloader/.env
ExecStart=/var/www/soundcloud-downloader/venv/bin/gunicorn -c gunicorn_config.py app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable soundcloud-downloader
sudo systemctl start soundcloud-downloader
```

### 5. Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/soundcloud-downloader
```

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL Configuration (use Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy settings
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
    }

    # Static files
    location /static/ {
        alias /var/www/soundcloud-downloader/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Block admin from external access (optional)
    # location /admin {
    #     allow 192.168.1.0/24;  # Your IP range
    #     deny all;
    #     proxy_pass http://127.0.0.1:8000;
    # }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/soundcloud-downloader /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. SSL Certificate (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

## Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | SEO-optimized homepage |
| `/download` | POST | Process MP3 download |
| `/robots.txt` | GET | Robots file for SEO |
| `/sitemap.xml` | GET | XML sitemap for SEO |
| `/admin` | GET/POST | Admin login |
| `/admin/dashboard` | GET | Admin dashboard |
| `/admin/settings` | GET/POST | Manage site settings |
| `/admin/logs` | GET | View download logs |
| `/admin/password` | GET/POST | Change password |
| `/admin/logout` | GET | Logout |

## SEO Features

- Dynamic meta title, description, keywords
- Open Graph tags for social sharing
- Semantic HTML structure (H1, H2, H3)
- robots.txt generation
- XML sitemap generation
- Mobile-friendly responsive design
- Fast page load optimization

## Security Considerations

1. **Change default admin credentials** immediately
2. **Use a strong SECRET_KEY** in production
3. **Enable HTTPS** with SSL certificate
4. **Regular updates** to yt-dlp and dependencies
5. **Monitor download logs** for abuse

## Legal Disclaimer

⚠️ **This tool is provided for educational and personal use only.**

Users are responsible for:
- Respecting copyright laws
- Following SoundCloud's Terms of Service
- Ensuring they have rights to download content
- Complying with local laws and regulations

This project is intended as an academic demonstration of web development concepts including:
- Flask web framework
- Database design with SQLAlchemy
- Authentication and session management
- Content management systems
- SEO implementation

## Troubleshooting

### yt-dlp not found
```bash
pip install --upgrade yt-dlp
```

### FFmpeg not found
```bash
# Windows: Download from https://ffmpeg.org/download.html
# Ubuntu/Debian:
sudo apt install ffmpeg
# Mac:
brew install ffmpeg
```

### Permission denied on downloads folder
```bash
sudo chown -R www-data:www-data /var/www/soundcloud-downloader/downloads
sudo chmod 755 /var/www/soundcloud-downloader/downloads
```

## Contributing

This is an educational project. Feel free to fork and modify for learning purposes.

## License

MIT License - Free for educational use.

---

**Educational Project** - Built for academic demonstration purposes.
