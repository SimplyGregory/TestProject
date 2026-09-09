# https://flask.palletsprojects.com/en/stable/quickstart/
# Reference for starting example
# https://www.sqlitetutorial.net/sqlite-python/creating-database/ SQLite tut
#https://medium.com/@icodewithben/flask-sqlite-login-and-register-form-48640743bf55

from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import uuid

app = Flask(__name__, template_folder="../frontend/")
app.secret_key = "7H6dJd0DKDd-gD6h2KD"
DATABASE = "database.db"

@app.route("/")
def hello_world():
    if "session_cookie" in request.cookies:
        sessionID = request.cookies.get("session_cookie")

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE sessionID = ?", (sessionID,))
        user = c.fetchone()
        if user:
            conn.close()
            return redirect(url_for("dashboard"))

    return render_template("public/login.html")

@app.route("/send-register", methods=["GET", "POST"])
def attempt_register():
    if request.method == "POST":
        username = request.form.get("username").lower()
        email = request.form.get("email").lower()
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

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "session_cookie" not in request.cookies:
        return redirect(url_for("hello_world"))

    sessionID = request.cookies.get("session_cookie")
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE sessionID = ?", (sessionID,))
    user = c.fetchone()
    conn.close()
    if not user:
        response = redirect(url_for("hello_world"))
        response.set_cookie("session_cookie", "", max_age=0)
        return response
    
    return render_template("private/index.html")

@app.route("/send-logout", methods=["GET", "POST"])
def logout():
    if "session_cookie" not in request.cookies:
        return redirect(url_for("hello_world"))

    response = redirect(url_for("hello_world"))
    response.set_cookie("session_cookie", "", max_age=0)
    return response
    
@app.route("/send-login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        response=redirect(url_for("hello_world"))
        email = request.form.get("email").lower()
        print(email)
        password = request.form.get("password")
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email,))
        print(c.fetchone())
        # if c.fetchall():
            # confirmed_email = c.fetchone()["email"]
            # correct_pass = c.execute(f"SELECT password FROM users WHERE email = {confirmed_email},")
            # if password == correct_pass:
            #     sessionID = c.execute(f"SELECT sessionID FROM users WHERE email = {confirmed_email},")
            #     response = redirect(url_for("dashboard"))
            #     response.set_cookie("session_cookie", sessionID, max_age=60 * 60 * 24)
       
        conn.commit()
        conn.close()
        return response



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
    app.run()
    