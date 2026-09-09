# https://flask.palletsprojects.com/en/stable/quickstart/
# Reference for starting example
# https://www.sqlitetutorial.net/sqlite-python/creating-database/ SQLite tut
#https://medium.com/@icodewithben/flask-sqlite-login-and-register-form-48640743bf55

from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__, template_folder="../frontend/public")
app.secret_key = "7H6dJd0DKDd-gD6h2KD"
DATABASE = "database.db"

@app.route("/")
def hello_world():
    return render_template("login.html")

@app.route("/send-login", methods=["POST"])
def attempt_login():
    print("hello")

@app.route("/send-register", methods=["POST"])
def attempt_register():
    print("hello")

@app.route("/send-forgot-password", methods=["POST"])
def attempt_forgot_password():
    print("hello")

def create_login_tables():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT,
            password TEXT
            )''')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_login_tables()
    app.run(debug=True)
    