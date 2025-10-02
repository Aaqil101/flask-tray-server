import subprocess
from pathlib import Path

from flask import Flask, jsonify
from flask_httpauth import HTTPBasicAuth
from waitress import serve

app = Flask(__name__)
auth = HTTPBasicAuth()

SCRIPT_PATH = Path(__file__).parent / "hello.bat"
users = {"admin": "test"}


@auth.verify_password
def verify_password(username, password):
    if username in users and users[username] == password:
        return username
    return None


@app.route("/run", methods=["GET", "POST"])
@auth.login_required
def run_script():
    try:
        if not SCRIPT_PATH.exists():
            return (
                jsonify(
                    {"status": "error", "message": f"Script not found: {SCRIPT_PATH}"}
                ),
                404,
            )

        # Run in a new terminal window (cmd.exe) and keep it open
        subprocess.Popen(
            ["cmd.exe", "/k", str(SCRIPT_PATH)],
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )

        return (
            jsonify({"status": "ok", "message": "Script started in new terminal"}),
            200,
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    # Use Waitress for production
    # serve(app, host="0.0.0.0", port=5000)

    # For development, use Flask's built-in server
    app.run(host="0.0.0.0", port=5000, debug=True)
