from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import base64
import json
from flask import send_file, request
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature
import os
import secrets
import zipfile
import io
import traceback
from io import BytesIO



app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

CLIENT_KEYS_DIR = 'keys/client_keys'
AIRPLANE_KEYS_DIR = 'keys/airplane_keys'
AIRPLANE_TRUSTED_CLIENTS_DIR = 'keys/airplane_trusted_clients'
CLIENT_TRUSTED_AIRPLANES_DIR = 'keys/client_trusted_airplanes'

for directory in [
    CLIENT_KEYS_DIR,
    AIRPLANE_KEYS_DIR,
    AIRPLANE_TRUSTED_CLIENTS_DIR,
    CLIENT_TRUSTED_AIRPLANES_DIR,
]:
    os.makedirs(directory, exist_ok=True)

def save_key_pair(name):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    priv_path = os.path.join(CLIENT_KEYS_DIR, f'{name}_private_key.pem')
    pub_path = os.path.join(CLIENT_KEYS_DIR, f'{name}_public_key.pem')

    # Save private key
    with open(priv_path, 'wb') as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    # Save public key
    public_key = private_key.public_key()
    with open(pub_path, 'wb') as f:
        f.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode('utf-8')

@app.route('/generate-key/client', methods=['POST'])
def generate_client_key():
    data = request.get_json() or {}
    name = data.get('name')
    if not name:
        return jsonify({"error": "Missing 'name' parameter"}), 400

    # Sanitize name (basic)
    name = ''.join(c for c in name if c.isalnum() or c in ('_', '-')).strip()
    if not name:
        return jsonify({"error": "Invalid 'name' parameter"}), 400

    priv_path = os.path.join(CLIENT_KEYS_DIR, f'{name}_private_key.pem')

    if os.path.exists(priv_path):
        return jsonify({"error": f"Key for '{name}' already exists."}), 400

    pub_key_pem = save_key_pair(name)
    return jsonify({"public_key_pem": pub_key_pem})


@app.route('/retrieve-key/client/<name>', methods=['GET'])
def retrieve_client_key(name): #return the public client key tied to the current name. 
    safe_name = ''.join(c for c in name if c.isalnum() or c in ('_', '-')).strip() #sanitization
    if not name:
        return jsonify({"error": "Invalid 'name' parameter"}), 400
    
    pub_path = os.path.join(CLIENT_KEYS_DIR, f'{safe_name}_public_key.pem')
    if not os.path.exists(pub_path):
        return jsonify({"error": f"Public key for '{safe_name}' not found"}), 404

    with open(pub_path, 'r') as f:
        public_key_pem = f.read()

    return jsonify({"public_key_pem": public_key_pem})

def load_private_key(name):
    path = os.path.join(CLIENT_KEYS_DIR, f"{name}_private_key.pem")
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)

def load_public_key_from_pem(pem_str):
    return serialization.load_pem_public_key(pem_str.encode())

@app.route('/encrypt-software', methods=['POST'])
def encrypt_software():
    try:
        software_file = request.files.get('file')
        airplane_key_name = request.form.get('airplane_key_name', '').strip()
        client_key_name = request.form.get('client_key_name', '').strip()

        if not software_file or not airplane_key_name or not client_key_name:
            return jsonify({'error': 'Missing required fields'}), 400

        airplane_key_path = os.path.join(CLIENT_TRUSTED_AIRPLANES_DIR, f"{airplane_key_name}_public_key.pem")
        if not os.path.exists(airplane_key_path):
            return jsonify({'error': f'Airplane public key "{airplane_key_name}" not found'}), 404

        with open(airplane_key_path, "rb") as f:
            airplane_public_key = serialization.load_pem_public_key(f.read())

        client_key_path = os.path.join(CLIENT_KEYS_DIR, f"{client_key_name}_private_key.pem")
        if not os.path.exists(client_key_path):
            return jsonify({'error': f'Client private key "{client_key_name}" not found'}), 404

        with open(client_key_path, 'rb') as f:
            client_private_key = serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())

        software_data = software_file.read()
        original_filename = software_file.filename

        # AES-GCM encryption
        aes_key = os.urandom(32)
        nonce = os.urandom(12)

        encryptor = Cipher(
            algorithms.AES(aes_key),
            modes.GCM(nonce),
            backend=default_backend()
        ).encryptor()

        ciphertext = encryptor.update(software_data) + encryptor.finalize()
        tag = encryptor.tag

        # Final format: nonce + ciphertext + tag
        full_encrypted_software = nonce + ciphertext + tag

        # Encrypt AES key with airplane's public RSA key
        encrypted_aes_key = airplane_public_key.encrypt(
            aes_key,
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        # Sign the original software file
        signature = client_private_key.sign(
            software_data,
            asym_padding.PSS(
                mgf=asym_padding.MGF1(hashes.SHA256()),
                salt_length=asym_padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        # Package into ZIP
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zipf:
            zipf.writestr("encrypted_software.bin", full_encrypted_software)
            zipf.writestr("signature.sig", signature)
            zipf.writestr("encrypted_key.bin", encrypted_aes_key)
            zipf.writestr("metadata.txt", original_filename)

        zip_buffer.seek(0)
        return send_file(
            zip_buffer,
            mimetype="application/zip",
            as_attachment=True,
            download_name="encrypted_package.zip"
        )

    except Exception as e:
        return jsonify({'error': f'Encryption failed: {str(e)}'}), 500


@app.route('/list-client-keys', methods=['GET'])
def list_client_keys():
    try:
        files = os.listdir(CLIENT_KEYS_DIR)
        # client keys named like {name}_private.pem, we want just the {name}
        keys = []
        for f in files:
            if f.endswith('_private_key.pem'):
                keys.append(f[:-16])  # strip "_private.pem"
        return jsonify({"keys": keys})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/list-airplane-keys', methods=['GET'])
def list_airplane_keys():
    try:
        files = os.listdir(CLIENT_TRUSTED_AIRPLANES_DIR)
        keys = [
            f[:-15] for f in files if f.endswith('_public_key.pem')
        ]
        return jsonify({"keys": keys})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/list-a-airplane-keys', methods=['GET'])
def list_a_airplane_keys():
    try:
        files = os.listdir(AIRPLANE_KEYS_DIR)
        # client keys named like {name}_private.pem, we want just the {name}
        keys = []
        for f in files:
            if f.endswith('_private_key.pem'):
                keys.append(f[:-16])  # strip "_private.pem"
        return jsonify({"keys": keys})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/list-a-client-keys', methods=['GET'])
def list_a_client_keys():
    try:
        files = os.listdir(AIRPLANE_TRUSTED_CLIENTS_DIR)
        keys = [
            f[:-15] for f in files if f.endswith('_public_key.pem')
        ]
        return jsonify({"keys": keys})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/save-airplane-key', methods=['POST'])
def save_airplane_key():
    data = request.get_json() or {}
    key_name = data.get('name', '').strip()
    public_key_pem = data.get('public_key_pem', '').strip()

    if not key_name or not public_key_pem:
        return jsonify({'error': 'Missing "name" or "public_key_pem"'}), 400

    # Basic sanitize name: alphanumeric + _ and -
    safe_name = ''.join(c for c in key_name if c.isalnum() or c in ('_', '-')).strip()
    if not safe_name:
        return jsonify({'error': 'Invalid key name'}), 400

    os.makedirs(CLIENT_TRUSTED_AIRPLANES_DIR, exist_ok=True)
    path = os.path.join(CLIENT_TRUSTED_AIRPLANES_DIR, f"{safe_name}_public_key.pem")


    if os.path.exists(path):
        return jsonify({'error': 'Key name already exists'}), 409

    try:
        with open(path, 'w') as f:
            f.write(public_key_pem)
        return jsonify({'message': f'Airplane public key saved as {safe_name}.pem'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/generate-airplane-key', methods=['POST'])
def generate_airplane_key():
    data = request.get_json()
    if not data or 'airplane_name' not in data:
        return jsonify({'error': 'Missing airplane_name'}), 400

    airplane_name = data['airplane_name']
    sanitized_name = ''.join(c for c in airplane_name if c.isalnum() or c in ('_', '-')).strip()

    private_key_path = os.path.join(AIRPLANE_KEYS_DIR, f"{sanitized_name}_private_key.pem")
    public_key_path = os.path.join(AIRPLANE_KEYS_DIR, f"{sanitized_name}_public_key.pem")

    if os.path.exists(private_key_path) or os.path.exists(public_key_path):
        return jsonify({'error': f"Keys already exist for airplane '{airplane_name}'"}), 400

    # Generate private key
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    # Save private key
    with open(private_key_path, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    # Save public key
    public_key = private_key.public_key()
    with open(public_key_path, "wb") as f:
        f.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )

    # Prepare public key string to return
    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')

    return jsonify({
        'message': f"Airplane key pair generated for '{airplane_name}'.",
        'public_key_pem': public_key_pem
    }), 200


@app.route('/retrieve-airplane-public-key/<airplane_name>', methods=['GET'])
def retrieve_airplane_public_key(airplane_name):
    sanitized_name = ''.join(c for c in airplane_name if c.isalnum() or c in ('_', '-')).strip()
    public_key_path = os.path.join(AIRPLANE_KEYS_DIR, f"{sanitized_name}_public_key.pem")

    if not os.path.exists(public_key_path):
        return jsonify({'error': f"Public key for airplane '{airplane_name}' not found."}), 404

    try:
        with open(public_key_path, 'r') as f:
            public_key_pem = f.read()
        return jsonify({'public_key_pem': public_key_pem}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/store-client-key', methods=['POST'])
def store_client_key():
    data = request.get_json()
    key_name = data.get('key_name')
    public_key_pem = data.get('public_key')

    if not key_name or not public_key_pem:
        return jsonify({'error': 'Missing key_name or public_key'}), 400

    try:
        # Validate that it's a proper public key
        serialization.load_pem_public_key(public_key_pem.encode(), backend=default_backend())
    except Exception:
        return jsonify({'error': 'Invalid public key format'}), 400

    key_path = os.path.join(AIRPLANE_TRUSTED_CLIENTS_DIR, f"{key_name}_public_key.pem")
    if os.path.exists(key_path):
        return jsonify({'error': 'Key with this name already exists'}), 400

    with open(key_path, 'w') as f:
        f.write(public_key_pem)

    return jsonify({'message': f"Client public key '{key_name}' saved successfully"})

@app.route('/decrypt-software', methods=['POST'])
def decrypt_software():
    try:
        package_file = request.files.get('file')
        airplane_key_name = request.form.get('airplane_key_name', '').strip()
        client_key_name = request.form.get('client_key_name', '').strip()

        if not package_file or not airplane_key_name or not client_key_name:
            return jsonify({'error': 'Missing required fields'}), 400

        airplane_key_path = os.path.join(AIRPLANE_TRUSTED_CLIENTS_DIR, f"{client_key_name}_public_key.pem")
        if not os.path.exists(airplane_key_path):
            return jsonify({'error': f'Client public key "{client_key_name}" not found'}), 404

        with open(airplane_key_path, "rb") as f:
            client_public_key = serialization.load_pem_public_key(f.read())

        airplane_key_path = os.path.join(AIRPLANE_KEYS_DIR, f"{airplane_key_name}_private_key.pem")
        if not os.path.exists(airplane_key_path):
            return jsonify({'error': f'Airplane private key "{airplane_key_name}" not found'}), 404

        with open(airplane_key_path, "rb") as f:
            airplane_private_key = serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())

        zip_data = package_file.read()

        zip_buffer = BytesIO(zip_data)
        with zipfile.ZipFile(zip_buffer, 'r') as zipf:
            encrypted_software = zipf.read("encrypted_software.bin")
            signature = zipf.read("signature.sig")
            encrypted_aes_key = zipf.read("encrypted_key.bin")
            original_filename = zipf.read("metadata.txt").decode()

        # Decrypt AES key
        aes_key = airplane_private_key.decrypt(
            encrypted_aes_key,
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        # Parse AES-GCM fields
        nonce = encrypted_software[:12]
        tag = encrypted_software[-16:]
        ciphertext = encrypted_software[12:-16]

        decryptor = Cipher(
            algorithms.AES(aes_key),
            modes.GCM(nonce, tag),
            backend=default_backend()
        ).decryptor()

        decrypted_software = decryptor.update(ciphertext) + decryptor.finalize()

        # Verify signature
        try:
            client_public_key.verify(
                signature,
                decrypted_software,
                asym_padding.PSS(
                    mgf=asym_padding.MGF1(hashes.SHA256()),
                    salt_length=asym_padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
        except Exception:
            return jsonify({'error': 'Signature verification failed'}), 400

        # Return the decrypted file with correct name
        return send_file(
            BytesIO(decrypted_software),
            mimetype="application/octet-stream",
            as_attachment=True,
            download_name=original_filename
        )

    except Exception as e:
        return jsonify({'error': f'Failed to decrypt software: {str(e)}'}), 500

if __name__ == "__main__":
    app.run(debug=False , port=5000)