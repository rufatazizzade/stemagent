# Vulnerable example: Insecure Deserialization via pickle
# WARNING: This is intentionally vulnerable code for educational purposes only.

import pickle
from flask import Flask, request

app = Flask(__name__)


@app.route("/load")
def load_data():
    data = request.get_data()
    # VULNERABLE: Deserializing untrusted user input with pickle
    obj = pickle.loads(data)
    return str(obj)


@app.route("/session")
def load_session():
    raw = request.cookies.get("session_data", "")
    # VULNERABLE: Pickle on cookie data
    session = pickle.loads(raw.encode("latin-1"))
    return f"Welcome, {session.get('user', 'guest')}"
