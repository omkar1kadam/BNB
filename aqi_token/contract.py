from web3 import Web3
from aqi_token.aqi_token_config import contract_address, contract_abi

w3 = Web3(Web3.HTTPProvider("https://rpc-amoy.polygon.technology"))

private_key = "0xB70cE2ECAA7bAc6Ef7245DF471A9Cb98c94909F3"
account = w3.eth.account.from_key(private_key)
public_address = account.address

contract = w3.eth.contract(address=contract_address, abi=contract_abi)

def get_token_balance(address):
    balance = contract.functions.balanceOf(address).call()
    return balance

def send_tokens(to_address, amount):
    nonce = w3.eth.getTransactionCount(public_address)
    txn = contract.functions.transfer(to_address, amount).buildTransaction({
        'from': public_address,
        'gas': 300000,
        'gasPrice': w3.toWei('3', 'gwei'),
        'nonce': nonce,
        'chainId': 80002
    })
    signed_txn = w3.eth.account.sign_transaction(txn, private_key=private_key)
    tx_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    return w3.toHex(tx_hash)
