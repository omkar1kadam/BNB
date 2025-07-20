from web3 import Web3
from .aqi_token_config import contract_address, contract_abi




# Connect to BNB Testnet
w3 = Web3(Web3.HTTPProvider("https://data-seed-prebsc-1-s1.binance.org:8545/")) 

# Your wallet credentials
private_key = "bfa9c044cadf852a18bf71109f7cee51392cc9e930d3a7191cc10a5748d3b826"
account = w3.eth.account.from_key(private_key)
public_address = account.address

# Connect to contract
contract = w3.eth.contract(address=contract_address, abi=contract_abi)

def get_token_balance(address):
    try:
        return contract.functions.balanceOf(address).call()
    except Exception as e:
        return f"Error getting balance: {str(e)}"
    
def get_token_decimals():
    return contract.functions.decimals().call()    

def send_tokens(to_address, amount):
    try:
        nonce = w3.eth.get_transaction_count(public_address)

        txn = contract.functions.transfer(to_address, amount).build_transaction({
            'from': public_address,
            'gas': 300000,
            'gasPrice': w3.to_wei('3', 'gwei'),
            'nonce': nonce,
            'chainId': 97  # BNB Testnet
        })

        # ✅ Sign the transaction
        signed_txn = w3.eth.account.sign_transaction(txn, private_key)

        # ✅ Send using .raw_transaction in Web3.py v7+
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)

        return w3.to_hex(tx_hash)

    except Exception as e:
        return f"Error sending tokens: {str(e)}"

balance = contract.functions.balanceOf(public_address).call()
print(balance)

if __name__ == "__main__":
    print("Public Address:", public_address)
    print("Balance:", get_token_balance(public_address))
