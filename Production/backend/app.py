from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__, template_folder="../frontend/", static_folder="../frontend/media", static_url_path="/media")

@app.route("/")
def login_index():

    return render_template("public/login.html")

if __name__ == "__main__":
    app.run()