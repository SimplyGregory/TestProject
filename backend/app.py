# https://flask.palletsprojects.com/en/stable/quickstart/
# Reference for starting example
# https://www.sqlitetutorial.net/sqlite-python/creating-database/ SQLite tut
#https://medium.com/@icodewithben/flask-sqlite-login-and-register-form-48640743bf55

from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import uuid

app = Flask(__name__, template_folder="../frontend/public")
app.secret_key = "7H6dJd0DKDd-gD6h2KD"
DATABASE = "database.db"

@app.route("/")
def hello_world():
    return render_template("login.html")

@app.route("/send-register", methods=["GET", "POST"])
def attempt_register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ? AND username = ?", (email, username))
        if c.fetchone():
            return "Username or Email already exists"
        sessionID = str(uuid.uuid4())
        c.execute("INSERT INTO users (username, email, password, sessionID) VALUES (?, ?, ?, ?)", (username, email, password, sessionID))
        conn.commit()
        conn.close()
        response = redirect(url_for("dashboard"))
        response.set_cookie("session_cookie", sessionID, max_age=60 * 60 * 24)
        return response

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


def create_login_tables():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            password TEXT,
            sessionID TEXT UNIQUE
            )''')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_login_tables()
    app.run(debug=True)
    