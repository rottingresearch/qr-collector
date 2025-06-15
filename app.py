import os
from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Update the database URI to use PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL')

if not app.config['SQLALCHEMY_DATABASE_URI']:
    raise RuntimeError("DATABASE_URL environment variable is not set.")

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


# Create the database tables within the application context
with app.app_context():
    db.create_all()


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

    sanitized_filename = secure_filename(file.filename)
    file_path = f'static/uploads/{sanitized_filename}'
    file.save(file_path)

    # Process the uploaded file to extract QR code data
    # (Assume you have logic here to extract `qr_data` from the image)
    qr_data = "extracted_data_from_image"
    # Replace with actual extraction logic

    # Check if the QR code already exists
    existing_qr_code = QRCode.query.filter_by(data=qr_data).first()
    if existing_qr_code:
        return 'QR code already exists', 400

    new_qr_code = QRCode(data=qr_data)
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
            return 'QR code already exists', 400

        new_qr_code = QRCode(url=url)
        db.session.add(new_qr_code)
        db.session.commit()
        return redirect(url_for('stored_qr_codes'))
    return 'No QR code data found', 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
