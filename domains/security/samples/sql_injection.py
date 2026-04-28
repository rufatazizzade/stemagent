# Vulnerable example: SQL Injection via string formatting
# WARNING: This is intentionally vulnerable code for educational purposes only.

from flask import Flask, request
import sqlite3

app = Flask(__name__)


def get_db():
    conn = sqlite3.connect("app.db")
    return conn


@app.route("/user")
def get_user():
    username = request.args.get("username")
    conn = get_db()
    cursor = conn.cursor()
    # VULNERABLE: Direct string interpolation in SQL query
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return str(results)


@app.route("/search")
def search():
    term = request.args.get("q")
    conn = get_db()
    cursor = conn.cursor()
    # VULNERABLE: String concatenation in SQL query
    cursor.execute("SELECT * FROM products WHERE name LIKE '%" + term + "%'")
    results = cursor.fetchall()
    conn.close()
    return str(results)
