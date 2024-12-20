from flask import Flask, render_template, request, send_file, jsonify, url_for
import os
import qrcode
from io import BytesIO
import socket
import requests  # To fetch ngrok's public URL



# Function to get the ngrok public URL
def get_ngrok_url():
    try:
        response = requests.get("http://localhost:4040/api/tunnels")
        data = response.json()
        public_url = data['tunnels'][0]['public_url']
        return public_url
    except Exception as e:
        print("Error fetching ngrok URL:", e)
        return None

# Flask setup
app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# A dictionary to store file metadata for security key validation
file_data = {}

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    print("Received upload request...")
    if 'file' not in request.files or 'key' not in request.form:
        print("Missing file or security key.")
        return jsonify({'status': 'error', 'message': 'Missing file or security key'}), 400

    file = request.files['file']
    security_key = request.form['key']

    if file.filename == '':
        print("No file selected.")
        return jsonify({'status': 'error', 'message': 'No file selected'}), 400

    # Save the file
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)
    print(f"File saved at {file_path}")

    # Get ngrok public URL
    ngrok_url = get_ngrok_url()
    if not ngrok_url:
        print("Failed to get ngrok URL.")
        return jsonify({'status': 'error', 'message': 'Could not fetch ngrok URL'}), 500

    print(f"Ngrok URL: {ngrok_url}")
    
    # Generate file download link
    file_url = f"{ngrok_url}/download/{file.filename}"
    qr_data = f"{file_url}?key_required=True"

    file_data[file.filename] = security_key

    # Generate QR code
    qr_img = qrcode.make(qr_data)
    buffer = BytesIO()
    qr_img.save(buffer, format="PNG")
    buffer.seek(0)

    print("QR Code generated and sent to client.")
    return send_file(buffer, mimetype='image/png')


@app.route('/download/<filename>', methods=['GET', 'POST'])
def download_file(filename):
    if request.method == 'POST':
        # Check if key is provided
        if 'key' not in request.form:
            return 'Security key is required!', 400

        user_key = request.form['key']
        actual_key = file_data.get(filename)

        if user_key == actual_key:
            # Send the file to the user
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            return send_file(file_path, as_attachment=True)
        else:
            return 'Invalid security key!', 403

    # Render a key entry form
    return f'''
    <h3>Enter Security Key for {filename}</h3>
    <form method="post">
        <input type="password" name="key" placeholder="Security Key" required />
        <button type="submit">Download</button>
    </form>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
