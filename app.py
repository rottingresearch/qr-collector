import os
import mimetypes
import threading
import time
import requests
from datetime import datetime, timedelta
from flask import Flask, request, render_template, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Configure MIME types for static files
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/css', '.css')

# Update the database URI to use PostgreSQL in production, SQLite for local development
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL', 'sqlite:///qr_codes.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Ensure the static/uploads directory exists
os.makedirs('static/uploads', exist_ok=True)


class QRCode(db.Model):
    """Model for storing QR Codes."""
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(
        db.DateTime, nullable=False, server_default=db.func.now()
    )
    last_checked = db.Column(db.DateTime, nullable=True)
    link_died = db.Column(db.DateTime, nullable=True)


# Create the database tables within the application context
with app.app_context():
    db.create_all()


def check_url_status(url):
    """Check if a URL is alive using requests."""
    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        # Consider 2xx and 3xx status codes as alive
        return response.status_code < 400
    except Exception as e:
        try:
            # If HEAD fails, try GET request
            response = requests.get(url, timeout=10, allow_redirects=True)
            return response.status_code < 400
        except Exception as e2:
            print(f"Error checking URL {url}: {e2}")
            return False


def check_all_urls():
    """Check all URLs in the database for dead links."""
    with app.app_context():
        # Get all QR codes that haven't been checked today or aren't dead yet
        today = datetime.now().date()
        qr_codes = QRCode.query.filter(
            db.or_(
                QRCode.last_checked.is_(None),
                db.func.date(QRCode.last_checked) < today,
                db.and_(
                    QRCode.link_died.is_(None),
                    db.func.date(QRCode.last_checked) < today
                )
            )
        ).all()
        
        for qr_code in qr_codes:
            # Skip if already marked as dead
            if qr_code.link_died:
                continue
                
            print(f"Checking URL: {qr_code.url}")
            is_alive = check_url_status(qr_code.url)
            
            # Update last_checked timestamp
            qr_code.last_checked = datetime.now()
            
            # If URL is dead and not already marked, mark it as dead
            if not is_alive and not qr_code.link_died:
                qr_code.link_died = datetime.now()
                print(f"URL marked as dead: {qr_code.url}")
            elif is_alive:
                print(f"URL is alive: {qr_code.url}")
            
            db.session.commit()


def start_daily_url_checker():
    """Start the daily URL checker to run at midnight server time."""
    def daily_checker():
        # Check if we should run an immediate check on startup
        # (if no URLs have been checked today)
        should_check_now = False
        try:
            with app.app_context():
                today = datetime.now().date()
                unchecked_count = QRCode.query.filter(
                    db.or_(
                        QRCode.last_checked.is_(None),
                        db.func.date(QRCode.last_checked) < today
                    )
                ).count()
                if unchecked_count > 0:
                    should_check_now = True
        except Exception:
            pass  # Skip startup check if there's an error
        
        if should_check_now:
            print("Running initial URL check on startup...")
            check_all_urls()
            print("Initial URL check completed.")
        
        while True:
            # Calculate seconds until next midnight
            now = datetime.now()
            midnight = (now + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            seconds_until_midnight = (midnight - now).total_seconds()
            
            midnight_str = midnight.strftime('%Y-%m-%d %H:%M:%S')
            print(f"Next URL check scheduled for midnight: {midnight_str}")
            print(f"Sleeping for {seconds_until_midnight:.0f} seconds...")
            
            # Sleep until midnight
            time.sleep(seconds_until_midnight)
            
            # Run the check at midnight
            print("Starting daily URL check at midnight...")
            check_all_urls()
            print("Daily URL check completed.")
    
    # Start the checker in a daemon thread
    checker_thread = threading.Thread(target=daily_checker, daemon=True)
    checker_thread.start()
    print("Daily URL checker started - will run at midnight server time.")


@app.route('/')
def index():
    """Displays the main page."""
    return render_template('index.html')


@app.route('/stored_qr_codes')
def stored_qr_codes():
    """Displays stored QR Codes."""
    qr_codes = QRCode.query.all()
    return render_template('stored_qr_codes.html', qr_codes=qr_codes)


@app.route('/scan', methods=['POST'])
def scan_qr_code():
    """Scans QR Code from uploaded image."""
    if 'qrImage' not in request.files:
        return 'No file part', 400

    file = request.files['qrImage']
    if file.filename == '':
        return 'No selected file', 400

    from werkzeug.utils import secure_filename
    base_path = os.path.abspath('static/uploads')
    filename = secure_filename(file.filename)
    file_path = os.path.join(base_path, filename)
    if not os.path.commonpath([base_path, os.path.abspath(file_path)]) == base_path:
        return 'Invalid file path', 400
    file.save(file_path)

    # Process the uploaded file to extract QR code data
    # (Assume you have logic here to extract `qr_data` from the image)
    qr_data = "extracted_data_from_image"
    # Replace with actual extraction logic

    # Check if the QR code already exists
    existing_qr_code = QRCode.query.filter_by(url=qr_data).first()
    if existing_qr_code:
        return 'QR code already exists', 400

    new_qr_code = QRCode(url=qr_data)
    db.session.add(new_qr_code)
    db.session.commit()

    return redirect(url_for('stored_qr_codes'))


@app.route('/process_qr_code')
def process_qr_code():
    """Processes QR Code to Database."""
    url = request.args.get('data')
    if url:
        # Check if the QR code already exists
        existing_qr_code = QRCode.query.filter_by(url=url).first()
        if existing_qr_code:
            # Check if request expects JSON (AJAX request)
            if request.headers.get('Accept') == 'application/json':
                return jsonify({'status': 'duplicate', 'message': 'QR code already exists'}), 200
            else:
                return redirect(url_for('index', duplicate='true'))

        new_qr_code = QRCode(url=url)
        db.session.add(new_qr_code)
        db.session.commit()
        
        # Check if request expects JSON (AJAX request)
        if request.headers.get('Accept') == 'application/json':
            return jsonify({'status': 'success', 'message': 'QR code saved successfully'}), 200
        else:
            return redirect(url_for('stored_qr_codes'))
    
    if request.headers.get('Accept') == 'application/json':
        return jsonify({'status': 'error', 'message': 'No QR code data found'}), 400
    else:
        return 'No QR code data found', 400


@app.route('/check_urls', methods=['POST'])
def manual_check_urls():
    """Manually trigger URL checking."""
    try:
        check_all_urls()
        return 'URL check completed', 200
    except Exception as e:
        logging.error(f"Error checking URLs: {e}", exc_info=True)
        return 'An internal error occurred while checking URLs.', 500


if __name__ == '__main__':
    # Start the daily URL checker
    start_daily_url_checker()
    app.run(host='0.0.0.0', port=5001)
