import os
import json
from flask import Flask, Response, current_app, render_template, request, jsonify, redirect, url_for, session, flash
import typing as t
from werkzeug.security import generate_password_hash, check_password_hash
from utils import load_users, save_users, load_ledger, save_ledger
import time  # <-- Add this at the top
from web3 import Web3
import werkzeug

from flask_cors import CORS

from flask import Flask, render_template, request, redirect, url_for, flash, session
import random
import smtplib
import ssl
import json
from email.message import EmailMessage

OTP_EMAIL = "plentera24@gmail.com"
OTP_PASSWORD = "ajyhlbaqbdbcctuw"  # Use App Password if 2FA is enabled

def send_otp(email, otp):
    msg = EmailMessage()
    msg.set_content(f"Your Plantera OTP is: {otp}")
    msg['Subject'] = "Plantera Account OTP Verification"
    msg['From'] = OTP_EMAIL
    msg['To'] = email

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(OTP_EMAIL, OTP_PASSWORD)
        server.send_message(msg)





# Import your blockchain logic
from aqi_token.contract import get_token_balance, send_tokens, contract, w3, public_address, private_key
from routes.sensor_data import sensor_bp

app = Flask(__name__)
CORS(app)
app.secret_key = 'super_secret_key_bro'  # 🔐 Required for session and flash

# Register blueprint
app.register_blueprint(sensor_bp)

# Token reward amount in wei (assuming 18 decimals)
TOKEN_REWARD_AMOUNT = w3.to_wei(1, 'ether')


# 📄 File paths
USERS_FILE = 'users.json'
LEDGER_FILE = 'token_ledger.json'
BLOCKCHAIN_FILE = 'data/blockchain.json'  # Path to your blockchain file


# 🚪 Home route (redirects to login/dashboard)
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/index')
def index():
    return render_template('index.html')    



@app.route("/send_otp", methods=["POST"])
def send_otp_route():
    email = request.form.get("email")
    otp = str(random.randint(100000, 999999))
    session["otp"] = otp
    session["email_for_otp"] = email

    try:
        send_otp(email, otp)
        return "OTP Sent"
    except Exception as e:
        return f"Failed to send OTP: {str(e)}"


# Load blockchain
def load_blockchain():
    if not os.path.exists(BLOCKCHAIN_FILE):
        return []
    with open(BLOCKCHAIN_FILE, 'r') as f:
        return json.load(f)

# Save blockchain
def save_blockchain(chain):
    with open(BLOCKCHAIN_FILE, 'w') as f:
        json.dump(chain, f, indent=4)

# Create new block
def create_block(data, chain):
    return {
        'index': len(chain) + 1,
        'timestamp': time.time(),
        'transactions': [data],  # <-- wrap in transactions
        'previous_hash': chain[-1]['hash'] if chain else '0' * 64,
        'hash': Web3.keccak(text=str(time.time())).hex()
    }


# Load ABI and Contract
from aqi_token.aqi_token_config import contract_address, contract_abi


w3 = Web3(Web3.HTTPProvider("https://data-seed-prebsc-1-s1.binance.org:8545"))

# from aqi_token_config import contract_address, contract_abi


contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# ✅ Replace with your real sender address and private key (only for testnet)
admin_wallet = "0xB70cE2ECAA7bAc6Ef7245DF471A9Cb98c94909F3"
admin_private_key = "bfa9c044cadf852a18bf71109f7cee51392cc9e930d3a7191cc10a5748d3b826"

contract = w3.eth.contract(address=contract_address, abi=contract_abi)

@app.route("/submit_data", methods=["POST"])
def submit_data():
    data = request.get_json()
    
    # Correct keys from ESP32 JSON
    wallet = data.get("wallet_address")
    sensor_id = data.get("deviceId")

    if not wallet:
        return jsonify({"status": "error", "message": "No wallet address provided"}), 400

    # Register sensor ID to wallet
    update_sensor_registry(wallet, sensor_id)

    try:
        nonce = w3.eth.get_transaction_count(admin_wallet)

        # Call transfer()
        tx = contract.functions.transfer(
            wallet,  # ✅ correct recipient address
            w3.to_wei(1, 'ether')  # 1 AQI token (if token has 18 decimals)
        ).build_transaction({
            'from': admin_wallet,
            'nonce': nonce,
            'gas': 200000,
            'gasPrice': w3.to_wei('5', 'gwei')
        })

        # Sign the transaction with admin's private key
        signed_tx = w3.eth.account.sign_transaction(tx, admin_private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        return jsonify({
            "status": "success",
            "tx_hash": tx_hash.hex()
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500



@app.route("/app")
def serve_react():
    return send_from_directory("frontend", "index.html")

@app.route("/app/<path:path>")
def serve_react_static(path):
    return send_from_directory("frontend", path)

def send_from_directory(
    directory: os.PathLike[str] | str,
    path: os.PathLike[str] | str,
    **kwargs: t.Any,
) -> Response:
    """Send a file from within a directory using :func:`send_file`.

    .. code-block:: python

        @app.route("/uploads/<path:name>")
        def download_file(name):
            return send_from_directory(
                app.config['UPLOAD_FOLDER'], name, as_attachment=True
            )

    This is a secure way to serve files from a folder, such as static
    files or uploads. Uses :func:`~werkzeug.security.safe_join` to
    ensure the path coming from the client is not maliciously crafted to
    point outside the specified directory.

    If the final path does not point to an existing regular file,
    raises a 404 :exc:`~werkzeug.exceptions.NotFound` error.

    :param directory: The directory that ``path`` must be located under,
        relative to the current application's root path. This *must not*
        be a value provided by the client, otherwise it becomes insecure.
    :param path: The path to the file to send, relative to
        ``directory``.
    :param kwargs: Arguments to pass to :func:`send_file`.

    .. versionchanged:: 2.0
        ``path`` replaces the ``filename`` parameter.

    .. versionadded:: 2.0
        Moved the implementation to Werkzeug. This is now a wrapper to
        pass some Flask-specific arguments.

    .. versionadded:: 0.5
    """
    return werkzeug.utils.send_from_directory(  # type: ignore[return-value]
        directory, path, **_prepare_send_file_kwargs(**kwargs)
    )

def _prepare_send_file_kwargs(**kwargs: t.Any) -> dict[str, t.Any]:
    if kwargs.get("max_age") is None:
        kwargs["max_age"] = current_app.get_send_file_max_age

    kwargs.update(
        environ=request.environ,
        use_x_sendfile=current_app.config["USE_X_SENDFILE"],
        response_class=current_app.response_class,
        _root_path=current_app.root_path,  # type: ignore
    )
    return kwargs


@app.route('/token_balance/<wallet_address>')
def token_balance(wallet_address):
    try:
        balance = get_token_balance(wallet_address)
        return render_template('token_balance.html', balance=balance, wallet=wallet_address)
    except Exception as e:
        return render_template('token_balance.html', balance="Error", wallet=wallet_address, error=str(e))

def get_sensor_count(wallet):
    try:
        with open("data/sensor_registry.json", "r") as f:
            registry = json.load(f)
            sensors = registry.get(wallet, [])
            return len(sensors), sensors
    except:
        return 0, []



# 📤 Send Token
@app.route('/send_token', methods=['POST'])
def send_token():
    try:
        to_address = request.form['to_address']
        amount = int(request.form['amount'])
        tx_hash = send_tokens(to_address, amount)
        return jsonify({'status': 'success', 'tx_hash': tx_hash})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


def update_sensor_registry(wallet, sensor_id):
    try:
        with open("data/sensor_registry.json", "r") as f:
            registry = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        registry = {}

    if wallet not in registry:
        registry[wallet] = []

    if sensor_id not in registry[wallet]:
        registry[wallet].append(sensor_id)

    with open("data/sensor_registry.json", "w") as f:
        json.dump(registry, f, indent=4)


# 📝 Signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        wallet = request.form['wallet']

        users = load_users()
        if email in users:
            flash("Email already registered. Please login.", "warning")
            return redirect(url_for('login'))

        users[email] = {
            'password': generate_password_hash(password),
            'wallet': wallet
        }
        save_users(users)

        flash("Signup successful. Please login.", "success")
        # Inside your signup POST logic
        print(f"✅ Registered: {email} - {wallet}")

        return redirect('/login')

    return render_template('signup.html')

@app.route("/latest-readings")
def latest_readings():
    with open("data/blockchain.json") as f:
        blockchain = json.load(f)

    latest_data = {}  # deviceId -> latest reading

    for block in blockchain:
        for tx in block.get("transactions", []):
            device_id = tx.get("deviceId")
            location = tx.get("location")
            environment = tx.get("environment")
            timestamp = tx.get("timestamp")

            if device_id and location and environment:
                if device_id not in latest_data or timestamp > latest_data[device_id]["timestamp"]:
                    latest_data[device_id] = {
                        "deviceId": device_id,
                        "location": location,
                        "aqi": environment.get("aqi", 0),
                        "temperature": environment.get("temperature", 0),
                        "humidity": environment.get("humidity", 0),
                        "timestamp": timestamp
                    }

    return jsonify(list(latest_data.values()))


# 🔐 Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')  # ✅ safer than request.form['email']
        password = request.form.get('password')

        if not email or not password:
            flash("Please enter both email and password.", "warning")
            return redirect('/login')

        users = load_users()
        user = users.get(email)

        if user and check_password_hash(user['password'], password):
            session['email'] = email
            session['wallet'] = user['wallet']
            return redirect('/dashboard')
        else:
            flash("Invalid credentials!", "danger")
            return redirect('/login')

    return render_template('login.html')

@app.route('/buy_kit')
def buy_kit():
    return render_template('buy_kit.html')

@app.route('/place_order', methods=['POST'])
def place_order():
    # You can optionally grab these values (not storing)
    email = request.form.get('email')
    kit = request.form.get('kit')
    address = request.form.get('address')

    print(f"✅ Order placed: {email}, {kit}, {address}")

    # Just redirect to success page
    return redirect('/success')

@app.route('/orderplaced')
def success():
    return render_template('orderplaced.html')


@app.route('/order')
def order():
    return render_template('order.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')


from aqi_token.contract import get_token_balance

@app.route("/dashboard")
def dashboard():
    wallet = session.get("wallet")
    balance = get_token_balance(wallet)
    sensor_count, sensor_list = get_sensor_count(wallet)
    return render_template("dashboard.html", 
                           wallet=wallet, 
                           balance=balance,
                           sensor_count=sensor_count,
                           sensor_list=sensor_list)





# 🚪 Logout
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect('/login')


# 🧪 Optional Decimals (debug)
@app.route('/decimals')
def decimals():
    return str(contract.functions.decimals().call())  # You had get_token_decimals(), which wasn't imported

# ✅ Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
