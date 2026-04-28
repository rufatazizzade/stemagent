# Vulnerable example: Path Traversal
# WARNING: This is intentionally vulnerable code for educational purposes only.

from flask import Flask, request, send_file

app = Flask(__name__)


@app.route("/download")
def download():
    filename = request.args.get("file")
    # VULNERABLE: User-controlled path without validation
    filepath = f"/var/data/{filename}"
    return send_file(filepath)


@app.route("/read")
def read_file():
    path = request.args.get("path")
    # VULNERABLE: Direct file read with user input
    with open(path, "r") as f:
        content = f.read()
    return content
