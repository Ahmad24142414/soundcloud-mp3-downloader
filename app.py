"""
app.py - Main Flask Application for SoundCloud MP3 Downloader
===============================================================
Educational Project - Academic Demonstration

This is the main application file that:
- Initializes the Flask app and database
- Configures routes for public and admin sections
- Handles MP3 downloads using yt-dlp
- Manages user sessions and authentication

Ethical Note: This project demonstrates web development concepts
including Flask routing, authentication, and external tool integration.
Users should respect copyright laws and platform terms of service.

Deployment: Compatible with Gunicorn and Nginx for VPS deployment.
Run with: gunicorn -w 4 -b 0.0.0.0:8000 app:app
"""

import os
import re
import uuid
import subprocess
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, 
    url_for, flash, send_file, jsonify, session
)
from flask_login import (
    LoginManager, login_user, logout_user, 
    login_required, current_user
)

from models import (
    db, Admin, SiteSettings, DownloadLog,
    init_default_settings, create_default_admin
)
from translations import (
    TRANSLATIONS, SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE,
    get_all_translations, get_language_list
)

# =============================================================================
# APPLICATION CONFIGURATION
# =============================================================================

app = Flask(__name__)

# Secret key for session management (CHANGE IN PRODUCTION)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production-123')

# Database configuration - SQLite for easy academic use
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "soundcloud_downloader.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Download directory configuration
DOWNLOAD_FOLDER = os.path.join(basedir, 'downloads')
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'
login_manager.login_message = 'Please log in to access the admin panel.'


@login_manager.user_loader
def load_user(user_id):
    """
    Flask-Login user loader callback.
    Retrieves the admin user from the database by ID.
    """
    return Admin.query.get(int(user_id))


# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================

with app.app_context():
    # Create all database tables
    db.create_all()
    # Initialize default settings if not present
    init_default_settings()
    # Create default admin account if none exists
    create_default_admin()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_all_settings():
    """
    Retrieve all site settings as a dictionary.
    Used to pass settings to templates for rendering.
    
    Returns:
        dict: All site settings as key-value pairs
    """
    settings = {}
    all_settings = SiteSettings.query.all()
    for setting in all_settings:
        settings[setting.key] = setting.value
    return settings


def is_valid_soundcloud_url(url):
    """
    Validate that a URL is a legitimate SoundCloud URL.
    Prevents abuse by ensuring only SoundCloud links are processed.
    
    Args:
        url: URL string to validate
        
    Returns:
        bool: True if valid SoundCloud URL, False otherwise
    """
    # Pattern matches soundcloud.com URLs
    pattern = r'^https?://(www\.)?(soundcloud\.com|snd\.sc)/[\w\-\.]+(/[\w\-\.]+)?'
    return bool(re.match(pattern, url, re.IGNORECASE))


def sanitize_filename(filename):
    """
    Remove or replace characters that are unsafe for filenames.
    Ensures cross-platform compatibility.
    
    Args:
        filename: Original filename string
        
    Returns:
        str: Sanitized filename safe for all operating systems
    """
    # Remove or replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '')
    # Limit length and strip whitespace
    return filename[:200].strip()


def download_soundcloud_audio(url, log_entry):
    """
    Download audio from SoundCloud using yt-dlp.
    Converts to MP3 format at 192kbps quality.
    
    This function demonstrates integration with external tools
    for audio processing in a Flask application.
    
    Args:
        url: SoundCloud track URL
        log_entry: DownloadLog database entry for tracking
        
    Returns:
        tuple: (success: bool, filepath_or_error: str)
    """
    try:
        # Generate unique filename to prevent collisions
        unique_id = str(uuid.uuid4())[:8]
        output_template = os.path.join(DOWNLOAD_FOLDER, f'{unique_id}_%(title)s.%(ext)s')
        
        # yt-dlp command configuration
        # - Extract audio only (no video)
        # - Convert to MP3 format
        # - Set audio quality to 192kbps
        # - Use safe filename characters
        cmd = [
            'yt-dlp',
            '--extract-audio',
            '--audio-format', 'mp3',
            '--audio-quality', '192K',
            '--output', output_template,
            '--no-playlist',  # Only download single track
            '--restrict-filenames',  # Safe filename characters
            '--no-warnings',
            url
        ]
        
        # Execute yt-dlp command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            error_msg = result.stderr or 'Unknown error occurred'
            return False, error_msg
        
        # Find the downloaded file
        for filename in os.listdir(DOWNLOAD_FOLDER):
            if filename.startswith(unique_id) and filename.endswith('.mp3'):
                filepath = os.path.join(DOWNLOAD_FOLDER, filename)
                return True, filepath
        
        return False, 'Downloaded file not found'
        
    except subprocess.TimeoutExpired:
        return False, 'Download timed out. Please try again.'
    except FileNotFoundError:
        return False, 'yt-dlp is not installed. Please install it with: pip install yt-dlp'
    except Exception as e:
        return False, str(e)


# =============================================================================
# PUBLIC ROUTES
# =============================================================================

@app.route('/')
def index():
    """
    Homepage Route
    --------------
    Renders the SEO-optimized public homepage.
    All content is loaded from the database for easy management.
    Supports multiple languages via ?lang= parameter.
    """
    settings = get_all_settings()
    
    # Handle language selection
    lang = request.args.get('lang', '')
    if lang and lang in SUPPORTED_LANGUAGES:
        session['language'] = lang
    elif 'language' not in session:
        session['language'] = DEFAULT_LANGUAGE
    
    current_lang = session.get('language', DEFAULT_LANGUAGE)
    translations = get_all_translations(current_lang)
    languages = get_language_list()
    
    # Merge translations with admin settings (admin settings override translations)
    # This allows admin to customize text while keeping translation as fallback
    merged_translations = translations.copy()
    
    # Map database setting keys to translation keys
    setting_to_translation = {
        'site_title': 'site_title',
        'site_subtitle': 'site_subtitle',
        'meta_title': 'site_title',
        'meta_description': 'site_subtitle',
        'hero_heading': 'hero_heading',
        'hero_description': 'hero_description',
        'how_it_works_title': 'how_it_works',
        'step_1_title': 'step_1_title',
        'step_1_desc': 'step_1_desc',
        'step_2_title': 'step_2_title',
        'step_2_desc': 'step_2_desc',
        'step_3_title': 'step_3_title',
        'step_3_desc': 'step_3_desc',
        'disclaimer_text': 'disclaimer',
        'footer_text': 'footer_text',
    }
    
    # Only override if we're in English (admin settings are in English)
    # For other languages, use translations
    if current_lang == 'en':
        for db_key, trans_key in setting_to_translation.items():
            if db_key in settings and settings[db_key]:
                merged_translations[trans_key] = settings[db_key]
    
    return render_template(
        'index.html',
        settings=settings,
        t=merged_translations,
        current_lang=current_lang,
        languages=languages
    )


@app.route('/download', methods=['POST'])
def download():
    """
    Download Route
    --------------
    Handles MP3 download requests from the frontend.
    
    Process:
    1. Validate the SoundCloud URL
    2. Check if downloader is enabled
    3. Create download log entry
    4. Execute yt-dlp to download audio
    5. Return the MP3 file to the user
    
    Returns:
        MP3 file download or JSON error response
    """
    settings = get_all_settings()
    
    # Check if downloader feature is enabled
    if settings.get('downloader_enabled', 'true').lower() != 'true':
        return jsonify({
            'success': False,
            'error': 'The download feature is currently disabled.'
        }), 503
    
    # Get URL from request
    url = request.form.get('url', '').strip()
    
    if not url:
        return jsonify({
            'success': False,
            'error': 'Please provide a SoundCloud URL.'
        }), 400
    
    # Validate URL format
    if not is_valid_soundcloud_url(url):
        return jsonify({
            'success': False,
            'error': 'Please provide a valid SoundCloud URL.'
        }), 400
    
    # Create download log entry
    log_entry = DownloadLog(
        url=url,
        ip_address=request.remote_addr,
        status='pending'
    )
    db.session.add(log_entry)
    db.session.commit()
    
    # Attempt download
    success, result = download_soundcloud_audio(url, log_entry)
    
    if success:
        # Update log with success
        filename = os.path.basename(result)
        log_entry.mark_success(filename)
        
        # Send file to user
        return send_file(
            result,
            as_attachment=True,
            download_name=filename
        )
    else:
        # Update log with failure
        log_entry.mark_failed(result)
        
        return jsonify({
            'success': False,
            'error': result
        }), 500


@app.route('/robots.txt')
def robots_txt():
    """
    Robots.txt Route
    ----------------
    Generates robots.txt for search engine crawlers.
    Allows indexing of public pages, blocks admin area.
    
    Technical SEO implementation.
    """
    content = """User-agent: *
Allow: /
Disallow: /admin
Disallow: /admin/
Disallow: /downloads/

Sitemap: /sitemap.xml
"""
    return content, 200, {'Content-Type': 'text/plain'}


@app.route('/sitemap.xml')
def sitemap_xml():
    """
    Sitemap.xml Route
    -----------------
    Generates XML sitemap for search engine optimization.
    Lists all public pages with priority and change frequency.
    
    Technical SEO implementation.
    """
    # Get the base URL (production should use actual domain)
    base_url = request.url_root.rstrip('/')
    
    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>{base_url}/</loc>
        <changefreq>weekly</changefreq>
        <priority>1.0</priority>
    </url>
</urlset>"""
    return sitemap, 200, {'Content-Type': 'application/xml'}


# =============================================================================
# ADMIN AUTHENTICATION ROUTES
# =============================================================================

@app.route('/admin', methods=['GET', 'POST'])
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """
    Admin Login Route
    -----------------
    Handles admin authentication with username/password.
    Uses Flask-Login for session management.
    """
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Find admin by username
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and admin.check_password(password):
            # Successful login
            login_user(admin)
            admin.last_login = datetime.utcnow()
            db.session.commit()
            flash('Welcome back!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('admin_login.html')


@app.route('/admin/logout')
@login_required
def admin_logout():
    """
    Admin Logout Route
    ------------------
    Ends the admin session and redirects to login.
    """
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin_login'))


# =============================================================================
# ADMIN DASHBOARD ROUTES
# =============================================================================

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """
    Admin Dashboard Route
    ---------------------
    Main admin panel overview with statistics.
    Shows recent downloads and system status.
    """
    # Get statistics
    total_downloads = DownloadLog.query.count()
    successful_downloads = DownloadLog.query.filter_by(status='success').count()
    failed_downloads = DownloadLog.query.filter_by(status='failed').count()
    
    # Get recent downloads
    recent_logs = DownloadLog.query.order_by(
        DownloadLog.created_at.desc()
    ).limit(10).all()
    
    settings = get_all_settings()
    
    return render_template(
        'admin_dashboard.html',
        total_downloads=total_downloads,
        successful_downloads=successful_downloads,
        failed_downloads=failed_downloads,
        recent_logs=recent_logs,
        settings=settings
    )


@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    """
    Admin Settings Route
    --------------------
    Manage SEO settings, site content, and feature toggles.
    All changes are stored in the database.
    """
    if request.method == 'POST':
        # Update all settings from form
        settings_to_update = [
            'meta_title', 'meta_description', 'meta_keywords',
            'site_title', 'site_subtitle', 'hero_heading', 'hero_description',
            'downloader_enabled', 'disclaimer_text', 'footer_text',
            'how_it_works_title', 'step_1_title', 'step_1_desc',
            'step_2_title', 'step_2_desc', 'step_3_title', 'step_3_desc'
        ]
        
        for key in settings_to_update:
            value = request.form.get(key, '')
            SiteSettings.set_setting(key, value)
        
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('admin_settings'))
    
    settings = get_all_settings()
    return render_template('admin_settings.html', settings=settings)


@app.route('/admin/logs')
@login_required
def admin_logs():
    """
    Admin Logs Route
    ----------------
    View all download logs with filtering options.
    Helps monitor usage and debug issues.
    """
    # Get filter parameters
    status_filter = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Build query
    query = DownloadLog.query.order_by(DownloadLog.created_at.desc())
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    # Paginate results
    logs = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template(
        'admin_logs.html',
        logs=logs,
        status_filter=status_filter
    )


@app.route('/admin/logs/clear', methods=['POST'])
@login_required
def admin_clear_logs():
    """
    Clear Download Logs
    -------------------
    Delete all download logs from the database.
    Use with caution - this action cannot be undone.
    """
    DownloadLog.query.delete()
    db.session.commit()
    flash('All download logs have been cleared.', 'success')
    return redirect(url_for('admin_logs'))


@app.route('/admin/password', methods=['GET', 'POST'])
@login_required
def admin_change_password():
    """
    Change Admin Password
    ---------------------
    Allows admin to update their password.
    Requires current password for verification.
    """
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not current_user.check_password(current_password):
            flash('Current password is incorrect.', 'error')
        elif len(new_password) < 6:
            flash('New password must be at least 6 characters.', 'error')
        elif new_password != confirm_password:
            flash('New passwords do not match.', 'error')
        else:
            current_user.set_password(new_password)
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
    
    return render_template('admin_password.html')


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors with custom page."""
    settings = get_all_settings()
    return render_template('404.html', settings=settings), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors with custom page."""
    db.session.rollback()
    settings = get_all_settings()
    return render_template('500.html', settings=settings), 500


# =============================================================================
# CLEANUP UTILITY
# =============================================================================

def cleanup_old_downloads(max_age_hours=24):
    """
    Remove old downloaded files to save disk space.
    Should be called periodically via cron job or scheduled task.
    
    Args:
        max_age_hours: Maximum age of files to keep (default 24 hours)
    """
    import time
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    for filename in os.listdir(DOWNLOAD_FOLDER):
        filepath = os.path.join(DOWNLOAD_FOLDER, filename)
        if os.path.isfile(filepath):
            file_age = current_time - os.path.getmtime(filepath)
            if file_age > max_age_seconds:
                os.remove(filepath)


# =============================================================================
# APPLICATION ENTRY POINT
# =============================================================================

if __name__ == '__main__':
    # Development server
    # For production, use: gunicorn -w 4 -b 0.0.0.0:8000 app:app
    app.run(debug=True, host='0.0.0.0', port=5000)
