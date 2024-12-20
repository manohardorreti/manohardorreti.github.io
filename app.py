from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import os
import qrcode
from io import BytesIO

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

file_data = {}

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files or 'key' not in request.form:
        return jsonify({'status': 'error', 'message': 'Missing file or security key'}), 400

    file = request.files['file']
    security_key = request.form['key']

    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No file selected'}), 400

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    file_url = f"http://localhost:5000/download/{file.filename}"
    qr_data = f"{file_url}?key_required=True"
    file_data[file.filename] = security_key

    qr_img = qrcode.make(qr_data)
    buffer = BytesIO()
    qr_img.save(buffer, format="PNG")
    buffer.seek(0)
    return send_file(buffer, mimetype='image/png')

@app.route('/download/<filename>', methods=['POST'])
def download_file(filename):
    user_key = request.form.get('key')
    actual_key = file_data.get(filename)

    if user_key == actual_key:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        return send_file(file_path, as_attachment=True)
    return 'Invalid security key!', 403

if __name__ == '__main__':
    app.run(debug=True)
