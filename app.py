import os
from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///qr_codes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Ensure the static/uploads directory exists
os.makedirs('static/uploads', exist_ok=True)


# Create the database tables within the application context
with app.app_context():
    db.create_all()


class QRCode(db.Model):
    """Model for storing QR Codes."""
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(200), nullable=False)


# Ensure the static/uploads directory exists
os.makedirs('static/uploads', exist_ok=True)


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

    # Process the uploaded file (existing functionality)
    # ...


@app.route('/process_qr_code')
def process_qr_code():
    """Processes QR Code to Database."""
    data = request.args.get('data')
    if data:
        new_qr_code = QRCode(data=data)
        db.session.add(new_qr_code)
        db.session.commit()
        return redirect(url_for('stored_qr_codes'))
    return 'No QR code data found', 400


if __name__ == '__main__':
    app.run(debug=False)
