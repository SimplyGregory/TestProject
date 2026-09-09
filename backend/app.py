# https://flask.palletsprojects.com/en/stable/quickstart/
# Reference for starting example

from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

if __name__ == "__main__":
    app.run(debug=True)