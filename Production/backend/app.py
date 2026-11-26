# https://mojoauth.com/security-guides/argon2-in-python#how-to-install-argon2-for-python
# https://flask.palletsprojects.com/en/stable/quickstart/
# https://www.sqlitetutorial.net/sqlite-python/creating-database/ SQLite tut
# https://medium.com/@icodewithben/flask-sqlite-login-and-register-form-48640743bf55
# https://www.geeksforgeeks.org/python/python-using-for-loop-in-flask/
# https://www.svgviewer.dev/s/492029/eye
# https://blog.rtwilson.com/a-python-sqlite3-context-manager-gotcha/
# https://blog.miguelgrinberg.com/post/handling-file-uploads-with-flask

#IMPORTED LIBRARIES FOR THE BACKEND
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from google.auth.transport import requests as google_auth_requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from argon2.exceptions import VerifyMismatchError
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from argon2 import PasswordHasher
from werkzeug.utils import secure_filename
from pathlib import Path
from dotenv import load_dotenv  
from datetime import datetime, timedelta
import json   
import os
import re
import sqlite3
import uuid                                                                                                                                                             

#LOADING ENV AND CONFIG FLASK APP
current_folder = Path(__file__).resolve().parent
load_dotenv(dotenv_path=current_folder / ".env")
app = Flask(__name__, template_folder="../frontend", static_folder="../frontend/content", static_url_path="/content")

#UPLOADING ENV FOR CONFIGURATIONS
app.secret_key = os.getenv("SECRET_KEY")
DATABASE = "database.db"
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

#COMPRESS DATABASE WRITTING
def database_action(sql, params=(), read = False, row_val = False, fetch_one = True):

    with sqlite3.connect(DATABASE) as connection:
        if row_val:
            connection.row_factory = sqlite3.Row

        cursor = connection.cursor()
        cursor.execute(sql, params)

        if read:
            return cursor.fetchone() if fetch_one else cursor.fetchall()
        
        return None

#BASE DOMAIN REDIRECT
@app.route("/")
def login_index():
    if "session_cookie" in request.cookies:
        user_data = database_action("SELECT * FROM users WHERE sessionID = ?", (request.cookies.get("session_cookie"),), True)
        if user_data:
            if datetime.fromisoformat(user_data["session_expiry"]) < datetime.now():
                return redirect(url_for("dashboard"))

    return render_template("public/login.html")

#ACCOUNT REGISTER
@app.route("/send-register", methods=["POST"])
def attempt_register():

    ph = PasswordHasher()
    form = request.form
    username, email, password = form.get("username", "").strip().lower(), form.get("email", "").strip().lower(), form.get("password", "")
    
    regex = re.compile(r"^[A-Za-z0-9!@#$%&.+\-_]+$")
    email_pattern = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    email_domains = [
        "gmail.com",
        "yahoo.com",
        "outlook.com",
        "hotmail.com",
        "icloud.com"
    ]


        
    if not username or not email or not password:
        return "Missing Field"
    if len(password) < 3:
        return "Password has minimum of 8 characters"
    if not regex.fullmatch(username):
        return "username incorrectly formatted"
    if not 4 < len(username) < 21:
        return "Username incorrect length"
    if not 7 < len(password) < 51:
            return "Username incorrect length"

    stripped_email = email.strip()
    domain = stripped_email.split("@")[1].lower()

    if not email_pattern.fullmatch(stripped_email) or domain not in email_domains:
        return "Incorrect email format"

    if not 7 < len(stripped_email.split("@")[0]) < 51:
                return "Email incorrect length"

    password = ph.hash(password)
    sessionID = str(uuid.uuid4())
    expires = (datetime.now() + timedelta(days=30)).isoformat()
    database_action("INSERT INTO users (username, email, password, sessionID, session_expiry) VALUES (?, ?, ?, ?, ?)", (username, email, password, sessionID, expires))
    user_id = database_action("SELECT id FROM users WHERE username = ?", (username,), True, True)
    database_action("INSERT INTO statistics (user_id, streak, lesson_inprogress, completed_lessons, daily_streak, assigned_units) VALUES (?, ?, ?, ?, ?, ?)", (user_id, 0, False, 0, 0, 0))
        
    response = redirect(url_for("dashboard"))
    response.set_cookie("session_cookie", sessionID, max_age=60 * 60 * 24)
    return response

#PRIVATE DASHBOARD
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if ("session_cookie" not in request.cookies) or (not database_action("SELECT * FROM users WHERE sessionID = ?", (request.cookies.get("session_cookie"),), True)):
        return redirect(url_for("login_index"))
    
    sessionID = request.cookies.get("session_cookie")

    user_data = database_action("SELECT * FROM users WHERE sessionID = ?", (sessionID,), True, True)
    if not user_data:
        response = redirect(url_for("login_index"))
        response.set_cookie("session_cookie", "", max_age=0)
        return response

    if datetime.fromisoformat(user_data["session_expiry"]) < datetime.now():
        return render_template("public/login.html")

    statistics_data = database_action("SELECT * FROM statistics WHERE user_id = ?", (user_data["id"],), True, True)
    if not statistics_data:
        database_action("INSERT INTO statistics (user_id, streak, lesson_inprogress, completed_lessons, daily_streak, assigned_units) VALUES (?, ?, ?, ?, ?, ?)", (user_data["id"], 0, False, 0, 0, 0))
        statistics_data = database_action("SELECT * FROM statistics WHERE user_id = ?", (user_data["id"],), True, True)

    leaderboard = []

    stats_data = json.loads((database_action("SELECT json_group_array(json_object('user_id', user_id, 'streak', streak)) FROM (SELECT user_id, streak FROM statistics ORDER BY streak DESC LIMIT 10)", "", True, False, True))[0])
    for content in stats_data:
        if content:
            username = database_action("SELECT username FROM users WHERE id = ?", (content["user_id"],), True)
            
            user = {"username": username, "streak": content["streak"]}
            leaderboard.append(user)

    context = {
        'username': user_data["username"],
        'streak': statistics_data["streak"],
        'completed_lessons': statistics_data["completed_lessons"],
        'lesson_inprogress': statistics_data["lesson_inprogress"],
        'daily_streak': statistics_data["daily_streak"],
        'leaderboard_data': leaderboard
    }

    return render_template("private/dashboard.html", **context)

#PRIVATE leaderboard
@app.route("/leaderboard", methods=["GET", "POST"])
def leaderboard():
    if ("session_cookie" not in request.cookies) or (not database_action("SELECT * FROM users WHERE sessionID = ?", (request.cookies.get("session_cookie"),), True)):
        return redirect(url_for("login_index"))
    
    sessionID = request.cookies.get("session_cookie")
    
    user_data = database_action("SELECT * FROM users WHERE sessionID = ?", (sessionID,), True, True)
    if not user_data:
        response = redirect(url_for("login_index"))
        response.set_cookie("session_cookie", "", max_age=0)
        return response

    if datetime.fromisoformat(user_data["session_expiry"]) < datetime.now():
            return render_template("public/login.html")

    statistics_data = database_action("SELECT * FROM statistics WHERE user_id = ?", (user_data["id"],), True, True)
    if not statistics_data:
        database_action("INSERT INTO statistics (user_id, streak, lesson_inprogress, completed_lessons, daily_streak, assigned_units) VALUES (?, ?, ?, ?, ?, ?)", (user_data["id"], 0, False, 0, 0, 0))
        statistics_data = database_action("SELECT * FROM statistics WHERE user_id = ?", (user_data["id"],), True, True)

    leaderboard = []
    stats_data = json.loads((database_action("SELECT json_group_array(json_object('user_id', user_id, 'streak', streak)) FROM (SELECT user_id, streak FROM statistics ORDER BY streak DESC LIMIT 50)", "", True, False, True))[0])
    for content in stats_data:
        if content:
            username = database_action("SELECT username FROM users WHERE id = ?", (content["user_id"],), True)
            
            user = {"username": username, "streak": content["streak"]}
            leaderboard.append(user)

    context = {
        'username': user_data["username"],
        'streak': statistics_data["streak"],
        'leaderboard_data': leaderboard
    }


    return render_template("private/leaderboard.html", **context)

#PRIVATE settings
@app.route("/settings", methods=["GET", "POST"])
def settings():
    if ("session_cookie" not in request.cookies) or (not database_action("SELECT * FROM users WHERE sessionID = ?", (request.cookies.get("session_cookie"),), True)):
        return redirect(url_for("login_index"))
    
    sessionID = request.cookies.get("session_cookie")

    user_data = database_action("SELECT * FROM users WHERE sessionID = ?", (sessionID,), True, True)
    if not user_data:
        response = redirect(url_for("login_index"))
        response.set_cookie("session_cookie", "", max_age=0)
        return response

    if datetime.fromisoformat(user_data["session_expiry"]) < datetime.now():
                return render_template("public/login.html")

    statistics_data = database_action("SELECT * FROM statistics WHERE user_id = ?", (user_data["id"],), True, True)
    if not statistics_data:
        database_action("INSERT INTO statistics (user_id, streak, lesson_inprogress, completed_lessons, daily_streak, assigned_units) VALUES (?, ?, ?, ?, ?, ?)", (user_data["id"], 0, False, 0, 0, 0))
        statistics_data = database_action("SELECT * FROM statistics WHERE user_id = ?", (user_data["id"],), True, True)

    context = {
        'username': user_data["username"],
        'streak': statistics_data["streak"]
    }

    
    return render_template("private/settings.html", **context)

@app.route("/data/lesson_list.json", methods=["POST"])
def grab_data():
    dir = os.path.abspath(os.path.join(app.root_path, "../frontend/private/data"))
    data = request.get_json()

    if not data:
        return jsonify({"error": "Missing version"}), 400
    
    version = str(data.get("version"))

    filepath = os.path.join(dir, "lesson_list.json")
    with open(filepath, "r", encoding="utf-8") as file:
        jsonContent = json.load(file)
    
    if version == str(jsonContent.get("version")):
        return jsonify({"error": "No version mismatch"}), 409

    if ("session_cookie" not in request.cookies) or (not database_action("SELECT * FROM users WHERE sessionID = ?", (request.cookies.get("session_cookie"),), True)):
        return jsonify({"error": "Incorrect Credentials!"}), 401
    
    sessionID = request.cookies.get("session_cookie")

    user_data = database_action("SELECT * FROM users WHERE sessionID = ?", (sessionID,), True, True)
    if not user_data or datetime.fromisoformat(user_data["session_expiry"]) < datetime.now():
        return jsonify({"error": "Incorrect Credentials!"}), 401
    
    filename = "lesson_list.json"

    try:
        return send_from_directory(
            directory=dir,
            path=filename,
            mimetype="application/json"
        )
    except:
        return jsonify({"Error": "File not found"}), 404

    

#LOGOUT
@app.route("/send-logout", methods=["POST"])
def logout():
    if ("session_cookie" not in request.cookies) or (not database_action("SELECT * FROM users WHERE sessionID = ?", (request.cookies.get("session_cookie"),), True)):
        return redirect(url_for("login_index"))

    response = redirect(url_for("login_index"))
    response.set_cookie("session_cookie", "", max_age=0)
    return response

#LOGIN
@app.route("/send-login", methods=["POST"])
def login():

    ph = PasswordHasher()
    form = request.form
    input, password = form.get("email").lower(), request.form.get("password")
    response=redirect(url_for("login_index"))

    user_data = database_action("SELECT * FROM users WHERE LOWER(email) = ? or username = ?", (input, input), True, True)

    if user_data:
        try:
            ph.verify(user_data["password"], password)
            response = redirect(url_for("dashboard"))
            response.set_cookie("session_cookie", user_data["sessionID"], max_age=60 * 60 * 24)
        except VerifyMismatchError:
            print("Incorrect Password!")

    return response

#GOOGLE LOGIN
@app.route("/google-login", methods=["GET"])
def google_login():
    flow = Flow.from_client_config(
        client_config={
            "web": {
                "client_id": "1046333407287-q37gi497bhi6miet9s8rh3ttg4dja6ra.apps.googleusercontent.com",
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "redirect_uris": ["http://127.0.0.1:5000/google-callback"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        },
        scopes=[
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
    session["code_verifier"] = flow.code_verifier
    session["final_redirect"] = url_for("dashboard")

    return redirect(authorization_url)

#GOOGLE CALLBACK REDIRECT
@app.route("/google-callback", methods=["GET"])
def google_callback():
    session_state=session["state"]
    redirect_uri = request.base_url
    authorization_response = request.url

    flow = Flow.from_client_config(
        client_config={
            "web": {
                "client_id": "1046333407287-q37gi497bhi6miet9s8rh3ttg4dja6ra.apps.googleusercontent.com",
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        },
        scopes=[
            "https://www.googleapis.com/auth/userinfo.email"
            ,"https://www.googleapis.com/auth/userinfo.profile"
            ,"openid"
        ],
        state=session_state
    )

    flow.redirect_uri = redirect_uri
    flow.code_verifier = session["code_verifier"]
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials

    id_info = id_token.verify_oauth2_token(
        id_token=credentials.id_token,
        request=google_auth_requests.Request(),
        audience=os.getenv("GOOGLE_CLIENT_ID")
    )

    email = id_info["email"]
    sessionId = None

    user_data = database_action("SELECT * FROM users WHERE email = ?", (email,), True, True)
    expires = (datetime.now() + timedelta(days=30)).isoformat()

    if not user_data:
        sessionId = str(uuid.uuid4())
        username = id_info["name"]
        database_action("INSERT INTO users (username, email, password, sessionID, session_expiry) VALUES (?, ?, ?, ?, ?)", (username, email, None, sessionId, expires))


        user_data = database_action("SELECT * FROM users WHERE id = ?", ("cursor.lastrowid",))
    else:
        sessionId = user_data["sessionID"]

    response = redirect(url_for("dashboard"))
    response.set_cookie("session_cookie", sessionId, max_age=60 * 60 * 24 * 30)
    response.set_cookie("profile_picture", id_info.get("picture", ""), max_age=60 * 60 * 24 * 7, samesite="lax")
    return response

if __name__ == "__main__":
    #CREATE ACCOUNTS TABLE IF N/A, CREATE STATS TABLE IF N/A
    database_action('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, email TEXT UNIQUE, password TEXT, sessionID TEXT, session_expiry STRING)''')
    database_action('''CREATE TABLE IF NOT EXISTS statistics (user_id INTEGER UNIQUE PRIMARY KEY, streak INTEGER, lesson_inprogress BOOLEAN, completed_lessons INTEGER, daily_streak INTEGER, assigned_units STRING)''')
    app.run()