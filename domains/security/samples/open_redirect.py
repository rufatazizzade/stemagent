# Vulnerable example: Open Redirect
# WARNING: This is intentionally vulnerable code for educational purposes only.

from flask import Flask, request, redirect

app = Flask(__name__)


@app.route("/login")
def login():
    next_url = request.args.get("next", "/")
    # VULNERABLE: Redirect to user-controlled URL without validation
    return redirect(next_url)


@app.route("/goto")
def goto():
    url = request.args.get("url")
    # VULNERABLE: Another open redirect pattern
    return redirect(url)
