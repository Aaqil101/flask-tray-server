import subprocess
from pathlib import Path

from flask import Flask, jsonify
from flask_httpauth import HTTPBasicAuth

app = Flask(__name__)
auth = HTTPBasicAuth()

# Path to the script you want to run
SCRIPT_PATH = str(Path(__file__).parent / "hello.bat")
# Secret key for simple authentication
SECRET_KEY = "test"

users = {"admin": SECRET_KEY}


@auth.verify_password
def verify_password(username, password):
    if username in users and users[username] == password:
        return username
    return None


@app.route("/run", methods=["GET", "POST"])
@auth.login_required
def run_script():
    subprocess.Popen(["cmd.exe", "/c", SCRIPT_PATH])
    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
