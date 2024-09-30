from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import cv2
from pyzbar.pyzbar import decode
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///qr_codes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class QRCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(200), nullable=False)

# Ensure the static/uploads directory exists
os.makedirs('static/uploads', exist_ok=True)

# Create the database tables within the application context
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    qr_codes = QRCode.query.all()
    return render_template('index.html', qr_codes=qr_codes)

@app.route('/scan', methods=['POST'])
def scan_qr_code():
    if 'qrImage' not in request.files:
        return 'No file part', 400

    file = request.files['qrImage']
    if file.filename == '':
        return 'No selected file', 400

    if file:
        file_path = f'static/uploads/{file.filename}'
        file.save(file_path)

        img = cv2.imread(file_path)
        decoded_objects = decode(img)
        for obj in decoded_objects:
            qr_data = obj.data.decode('utf-8')
            new_qr_code = QRCode(data=qr_data)
            db.session.add(new_qr_code)
            db.session.commit()

        return redirect(url_for('index'))

    return 'File not processed', 400

if __name__ == '__main__':
    app.run(debug=True)