#IMPORTED LIBRARIES FOR THE BACKEND
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import uuid
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests as google_auth_requests
import os
from dotenv import load_dotenv                                                                                                                                                                  

#LOADING ENV AND CONFIG FLASK APP
load_dotenv()
app = Flask(__name__, template_folder="../frontend/")

#UPLOADING ENV FOR CONFIGURATIONS
app.secret_key, DATABASE = os.getenv("SECRET_KEY"), "database.db"
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

#COMPRESS DATABASE WRITTING
def database_action(SQL, params, read = False, row_val = False):
    connection = sqlite3.connect(DATABASE)
    if row_val:
        connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    sql_code = str(SQL)
    try:
        if params:
            args = sql_code.split(", ", maxsplit=1)
            cursor.execute(args[0], params)
        else:
            cursor.execute(sql_code)
    except Exception as e:
        print(e)

    if read == True:
        return cursor.fetchone()
    
    return None


#BASE DOMAIN REDIRECT
@app.route("/")
def login_index():
    if "session_cookie" in request.cookies:

        sessionID = request.cookies.get("session_cookie")
        user_data = database_action("SELECT * FROM users WHERE sessionID = ?", (sessionID,), True)

        if user_data:
            return redirect(url_for("dashboard"))

    return render_template("public/login.html")

#ACCOUNT REGISTER
@app.route("/send-register", methods=["POST"])
def attempt_register():

    form = request.form
    username, email, password = form.get("username").lower(), form.get("email").lower(), form.get("password")

    if database_action("SELECT * FROM users WHERE email = ? AND username = ?", (email, username), True):
        return "Username or Email already exists"
    
    sessionID = str(uuid.uuid4())
    database_action("INSERT INTO users (username, email, password, sessionID) VALUES (?, ?, ?, ?)", (username, email, password, sessionID))
        
    response = redirect(url_for("dashboard"))
    response.set_cookie("session_cookie", sessionID, max_age=60 * 60 * 24)
    return response

#PRIVATE DASHBOARD
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "session_cookie" not in request.cookies:
        return redirect(url_for("login_index"))
    
    sessionID = request.cookies.get("session_cookie")

    user_data = database_action("SELECT * FROM users WHERE sessionID = ?", (sessionID,), True, True)

    if not user_data:
        response = redirect(url_for("login_index"))
        response.set_cookie("session_cookie", "", max_age=0)
        return response

    return render_template("private/index.html", username=user_data["username"])

#LOGOUT
@app.route("/send-logout", methods=["GET", "POST"])
def logout():
    if "session_cookie" not in request.cookies:
        return redirect(url_for("login_index"))

    response = redirect(url_for("login_index"))
    response.set_cookie("session_cookie", "", max_age=0)
    return response

#LOGIN
@app.route("/send-login", methods=["POST"])
def login():

    form = request.form
    email, password = form.get("email").lower(), request.form.get("password")
    response=redirect(url_for("login_index"))

    user_data = database_action("SELECT * FROM users WHERE LOWER(email) = ?", (email,), True, True)

    if user_data:
        if password == user_data["password"]:
            response = redirect(url_for("dashboard"))
            response.set_cookie("session_cookie", user_data["sessionID"], max_age=60 * 60 * 24)

    return response

#RESET (NOT BUILT BC NOT NEEDED FOR SUCCESS CRITERIA)
@app.route("/reset-password", methods=["POST"])
def reset_password():

    pass
    return redirect(url_for("login_index"))

#GOOGLE LOGIN
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
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
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

    if not user_data:
        sessionId = str(uuid.uuid4())
        username = id_info["name"]
        database_action("INSERT INTO users (username, email, password, sessionID) VALUES (?, ?, ?, ?)", (username, email, None, sessionId))


        user_data = database_action("SELECT * FROM users WHERE id = ?", ("cursor.lastrowid,"))
    else:
        sessionId = user_data["sessionID"]

    response = redirect(url_for("dashboard"))
    response.set_cookie("session_cookie", sessionId, max_age=60 * 60 * 24)
    return response

if __name__ == "__main__":
    #CREATE ACCOUNTS TABLE IF N/A
    database_action('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, email TEXT UNIQUE, password TEXT, sessionID TEXT UNIQUE)''', None)
    
    app.run()
    