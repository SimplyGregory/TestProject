from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__, template_folder="../frontend/", static_folder="../frontend/content", static_url_path="/content")

@app.route("/")
def login_index():

    return render_template("private/dashboard.html")

if __name__ == "__main__":
    app.run()