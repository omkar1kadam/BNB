import os
import json

USERS_FILE = "users.json"
LEDGER_FILE = "token_ledger.json"

# Save users to JSON
def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def load_users():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


# Save token ledger
def save_ledger(ledger):
    with open(LEDGER_FILE, 'w') as f:
        json.dump(ledger, f, indent=4)

# Load token ledger
def load_ledger():
    if not os.path.exists(LEDGER_FILE) or os.path.getsize(LEDGER_FILE) == 0:
        return {}
    try:
        with open(LEDGER_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}
