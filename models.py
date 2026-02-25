"""
models.py - Database Models for SoundCloud MP3 Downloader
===========================================================
Educational Project - Academic Demonstration

This module defines the SQLite database schema using SQLAlchemy ORM.
Contains models for:
- Admin users (authentication)
- Site settings (SEO and content management)
- Download logs (tracking download history)

Ethical Note: This project is designed for educational purposes to
demonstrate web development concepts including database design,
ORM usage, and content management systems.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import bcrypt

# Initialize SQLAlchemy instance
# This will be bound to the Flask app in app.py
db = SQLAlchemy()


class Admin(UserMixin, db.Model):
    """
    Admin User Model
    ----------------
    Stores administrator credentials for the admin panel.
    Uses bcrypt for secure password hashing.
    
    Attributes:
        id: Primary key
        username: Unique admin username
        password_hash: Bcrypt hashed password
        created_at: Account creation timestamp
        last_login: Last successful login timestamp
    """
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        """
        Hash and store the password using bcrypt.
        Bcrypt automatically handles salt generation.
        
        Args:
            password: Plain text password to hash
        """
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'), 
            bcrypt.gensalt()
        ).decode('utf-8')
    
    def check_password(self, password):
        """
        Verify a password against the stored hash.
        
        Args:
            password: Plain text password to verify
            
        Returns:
            bool: True if password matches, False otherwise
        """
        return bcrypt.checkpw(
            password.encode('utf-8'), 
            self.password_hash.encode('utf-8')
        )
    
    def __repr__(self):
        return f'<Admin {self.username}>'


class SiteSettings(db.Model):
    """
    Site Settings Model
    -------------------
    Stores all configurable site content and SEO settings.
    Uses key-value pairs for flexibility in adding new settings.
    
    This model allows admins to update SEO content from the dashboard
    without modifying template files directly.
    
    Attributes:
        id: Primary key
        key: Setting identifier (e.g., 'meta_title', 'meta_description')
        value: Setting value (text content)
        updated_at: Last modification timestamp
    """
    __tablename__ = 'site_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def get_setting(key, default=''):
        """
        Retrieve a setting value by key.
        
        Args:
            key: Setting key to look up
            default: Default value if key doesn't exist
            
        Returns:
            str: Setting value or default
        """
        setting = SiteSettings.query.filter_by(key=key).first()
        return setting.value if setting else default
    
    @staticmethod
    def set_setting(key, value):
        """
        Create or update a setting.
        
        Args:
            key: Setting key
            value: Setting value
        """
        setting = SiteSettings.query.filter_by(key=key).first()
        if setting:
            setting.value = value
        else:
            setting = SiteSettings(key=key, value=value)
            db.session.add(setting)
        db.session.commit()
    
    def __repr__(self):
        return f'<SiteSettings {self.key}>'


class DownloadLog(db.Model):
    """
    Download Log Model
    ------------------
    Tracks all download attempts for monitoring and analytics.
    Stores the requested URL, status, and timing information.
    
    This helps administrators:
    - Monitor usage patterns
    - Debug failed downloads
    - Track system health
    
    Attributes:
        id: Primary key
        url: SoundCloud URL that was requested
        status: Download status ('success', 'failed', 'pending')
        error_message: Error details if download failed
        filename: Generated filename for successful downloads
        ip_address: Client IP (for rate limiting/security)
        created_at: Request timestamp
        completed_at: Download completion timestamp
    """
    __tablename__ = 'download_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, success, failed
    error_message = db.Column(db.Text)
    filename = db.Column(db.String(255))
    ip_address = db.Column(db.String(45))  # IPv6 compatible
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def mark_success(self, filename):
        """
        Mark download as successful.
        
        Args:
            filename: Name of the downloaded file
        """
        self.status = 'success'
        self.filename = filename
        self.completed_at = datetime.utcnow()
        db.session.commit()
    
    def mark_failed(self, error_message):
        """
        Mark download as failed with error details.
        
        Args:
            error_message: Description of what went wrong
        """
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
        db.session.commit()
    
    def __repr__(self):
        return f'<DownloadLog {self.id} - {self.status}>'


def init_default_settings():
    """
    Initialize default site settings if they don't exist.
    Called during application startup to ensure all required
    settings are available.
    
    Default settings include:
    - SEO meta tags
    - Site content
    - Feature toggles
    - Legal disclaimer
    """
    default_settings = {
        # SEO Settings
        'meta_title': 'SoundCloud MP3 Downloader - Free Audio Download Tool',
        'meta_description': 'Download SoundCloud tracks as MP3 files. Free, fast, and easy to use audio downloader for educational purposes.',
        'meta_keywords': 'soundcloud downloader, mp3 download, audio converter, free music download, soundcloud to mp3',
        
        # Homepage Content
        'site_title': 'SoundCloud MP3 Downloader',
        'site_subtitle': 'Download your favorite SoundCloud tracks as high-quality MP3 files',
        'hero_heading': 'Download SoundCloud Tracks as MP3',
        'hero_description': 'Simply paste the SoundCloud URL below and click download. Our tool will convert the audio to MP3 format.',
        
        # Feature Toggle
        'downloader_enabled': 'true',
        
        # Legal Disclaimer
        'disclaimer_text': 'This tool is provided for educational and personal use only. Users are responsible for respecting copyright laws, platform terms of service, and intellectual property rights. We do not host or store any copyrighted content.',
        
        # Footer Content
        'footer_text': '© 2024 SoundCloud MP3 Downloader - Educational Project',
        
        # How It Works Section
        'how_it_works_title': 'How It Works',
        'step_1_title': 'Copy URL',
        'step_1_desc': 'Find the SoundCloud track you want and copy its URL from your browser.',
        'step_2_title': 'Paste & Download',
        'step_2_desc': 'Paste the URL in the input field above and click the download button.',
        'step_3_title': 'Enjoy',
        'step_3_desc': 'Your MP3 file will be ready for download in seconds.',
    }
    
    for key, value in default_settings.items():
        existing = SiteSettings.query.filter_by(key=key).first()
        if not existing:
            setting = SiteSettings(key=key, value=value)
            db.session.add(setting)
    
    db.session.commit()


def create_default_admin():
    """
    Create a default admin account if none exists.
    
    Default credentials (CHANGE IN PRODUCTION):
    - Username: admin
    - Password: admin123
    
    Security Note: This is for initial setup only.
    Administrators should change the password immediately
    after first login.
    """
    if Admin.query.count() == 0:
        admin = Admin(username='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Default admin created - Username: admin, Password: admin123")
