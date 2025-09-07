import json
import os

# File paths
CUSTOMER_FILE = "customers.json"
BANK_FILE = "bank_data.json"

# Ensure files exist
for filepath in [CUSTOMER_FILE, BANK_FILE]:
    if not os.path.exists(filepath):
        with open(filepath, "w") as f:
            json.dump({}, f, indent=2)

# ---------- Generic JSON save/load ----------
def save_json(filepath, data):
    """Save data as JSON with indentation."""
    try:
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving {filepath}: {e}")

def load_json(filepath):
    """Load JSON data, return empty dict if file doesn't exist."""
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return {}

# ---------- Customer-specific functions ----------
def load_customers():
    """Load customers and ensure unique IDs and proper structure."""
    raw_data = load_json(CUSTOMER_FILE)
    customers = {}
    for cid_str, info in raw_data.items():
        try:
            cid = int(cid_str)
        except ValueError:
            continue
        customers[cid] = {
            "id": cid,
            "credit_score": info.get("credit_score", 300),
            "loans": info.get("loans", []),
            "deposits": info.get("deposits", []),
            "deposit_balance": info.get("deposit_balance", 0.0)
        }
    return customers

def save_customers(customers):
    """Save customers to file."""
    save_json(CUSTOMER_FILE, customers)

# ---------- Bank-specific functions ----------
def load_bank_data():
    """Load bank data, return empty dict if file doesn't exist."""
    return load_json(BANK_FILE)

def save_bank_data(data):
    """Save bank data to file."""
    save_json(BANK_FILE, data)
