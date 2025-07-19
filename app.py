from flask import Flask, render_template, request, jsonify
from aqi_token.contract import get_token_balance, send_tokens

app = Flask(__name__)

@app.route('/token_balance/<wallet_address>')
def token_balance(wallet_address):
    balance = get_token_balance(wallet_address)
    return render_template('token_balance.html', balance=balance, wallet=wallet_address)

@app.route('/send_token', methods=['POST'])
def send_token():
    to_address = request.form['to_address']
    amount = int(request.form['amount'])
    tx_hash = send_tokens(to_address, amount)
    return jsonify({'tx_hash': tx_hash})

if __name__ == "__main__":
    app.run(debug=True)
