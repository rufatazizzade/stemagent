# Vulnerable example: Debug mode enabled in production
# WARNING: This is intentionally vulnerable code for educational purposes only.

from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    return "Hello, World!"


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    # VULNERABLE: Debug mode should never be enabled in production
    app.run(debug=True, host="0.0.0.0", port=5000)
