# Vulnerable example: Command Injection via os.system
# WARNING: This is intentionally vulnerable code for educational purposes only.

import os
from flask import Flask, request

app = Flask(__name__)


@app.route("/ping")
def ping():
    host = request.args.get("host", "127.0.0.1")
    # VULNERABLE: User input passed directly to os.system
    result = os.system(f"ping -c 1 {host}")
    return f"Ping result code: {result}"


@app.route("/lookup")
def dns_lookup():
    domain = request.args.get("domain")
    # VULNERABLE: User input in shell command
    output = os.popen(f"nslookup {domain}").read()
    return f"DNS result: {output}"
