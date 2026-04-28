# Vulnerable example: Insecure use of eval/exec
# WARNING: This is intentionally vulnerable code for educational purposes only.

from flask import Flask, request

app = Flask(__name__)


@app.route("/calculate")
def calculate():
    expression = request.args.get("expr", "1+1")
    # VULNERABLE: eval with user-controlled input
    result = eval(expression)
    return f"Result: {result}"


@app.route("/run")
def run_code():
    code = request.args.get("code", "")
    # VULNERABLE: exec with user-controlled input
    exec(code)
    return "Executed"
