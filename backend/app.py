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

if __name__ == "__main__":
    app.run(debug=True)