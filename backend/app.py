# https://flask.palletsprojects.com/en/stable/quickstart/
# Reference for starting example
# https://www.sqlitetutorial.net/sqlite-python/creating-database/ SQLite tut

from flask import Flask, render_template

app = Flask(__name__, template_folder="../frontend/public")


@app.route("/")
def hello_world():
    return render_template("login.html")

if __name__ == "__main__":
    app.run(debug=True)