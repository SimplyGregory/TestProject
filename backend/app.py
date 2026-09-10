# https://flask.palletsprojects.com/en/stable/quickstart/
# Reference for starting example
# https://www.sqlitetutorial.net/sqlite-python/creating-database/ SQLite tut
# https://medium.com/@icodewithben/flask-sqlite-login-and-register-form-48640743bf55
# https://developers.google.com/identity/sign-in/web/sign-in
# https://jaggedarray.hashnode.dev/flask-google-login#heading-conclusion

from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import uuid
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests as google_auth_requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder="../frontend/")
app.secret_key = "7H6dJd0DKDd-gD6h2KD"
DATABASE = "database.db"

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

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

    return render_template("private/index.html", username=user[1])

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
        password = request.form.get("password")
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email,))
        user = c.fetchone()

        if user:
            correct_pass = user[3]
            if password == correct_pass:
                sessionID = user[4]
                response = redirect(url_for("dashboard"))
                response.set_cookie("session_cookie", sessionID, max_age=60 * 60 * 24)

       
        conn.commit()
        conn.close()
        return response

@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        return redirect(url_for("hello_world"))

@app.route("/google-login", methods=["GET"])
def google_login():
    flow = Flow.from_client_config(
        client_config={
            "web": {
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "redirect_uris": ["http://127.0.0.1:5000/google-callback"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }

        ,scopes=[
            "https://www.googleapis.com/auth/userinfo.email"
            ,"https://www.googleapis.com/auth/userinfo.profile"
            ,"openid"
        ]
    )

    flow.redirect_uri = "http://127.0.0.1:5000/google-callback"

    authorization_url, state = (
        flow.authorization_url(
            access_type="offline",
            prompt="select_account",
            include_granted_scopes="true"
        )
    )

    session["state"] = state
    session["final_redirect"] = url_for("dashboard")

    return redirect(authorization_url)

@app.route("/google-callback", methods=["GET"])
def google_callback():
    session_state=session["state"]
    redirect_uri = request.base_url
    authorization_response = request.url

    flow = Flow.from_client_config(
        client_config={
            "web": {
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }
        ,scopes=[
            "https://www.googleapis.com/auth/userinfo.email"
            ,"https://www.googleapis.com/auth/userinfo.profile"
            ,"openid"
        ]
        ,state=session_state
    )

    flow.redirect_uri = redirect_uri
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials

    id_info = id_token.verify_oauth2_token(
        id_token=credentials.id_token,
        request=google_auth_requests.Request(),
        audience=os.getenv("GOOGLE_CLIENT_ID")
    )

    session["id_info"] = id_info
    return redirect(url_for("dashboard"))

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
    