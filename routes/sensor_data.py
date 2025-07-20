from flask import Blueprint, request, jsonify
from aqi_token.contract import contract, w3, public_address, private_key
import time, json, os

sensor_bp = Blueprint('sensor_bp', __name__)
TOKEN_REWARD_AMOUNT = 1  # Just 1 token unit

@sensor_bp.route('/sensor_data', methods=['POST'])
def receive_sensor_data():
    try:
        data = request.get_json()
        device_wallet = data.get("wallet")

        # ✅ Append to blockchain.json
        json_path = os.path.join("data", "blockchain.json")
        if not os.path.exists(json_path):
            with open(json_path, "w") as f:
                json.dump([], f)

        with open(json_path, "r+") as f:
            chain = json.load(f)
            data["timestamp"] = time.time()
            chain.append(data)
            f.seek(0)
            json.dump(chain, f, indent=4)

        # ✅ Mint token
        nonce = w3.eth.get_transaction_count(public_address)
        txn = contract.functions.mint(device_wallet, TOKEN_REWARD_AMOUNT).build_transaction({
            'from': public_address,
            'nonce': nonce,
            'gas': 200000,
            'gasPrice': w3.to_wei('5', 'gwei'),
            'chainId': 97
        })
        signed_txn = w3.eth.account.sign_transaction(txn, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)

        return jsonify({
            "status": "success",
            "tx_hash": tx_hash.hex(),
            "message": f"Token minted to {device_wallet}"
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
