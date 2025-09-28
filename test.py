import io
import sys
import threading

import requests
from flask import Flask, jsonify, request
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction, QIcon, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMenu,
    QPushButton,
    QSystemTrayIcon,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# -------------------
# Flask server setup
# -------------------
SECRET_KEY = "my_secret_key"
server_thread = None
server_running = False

app = Flask(__name__)


@app.route("/run-script", methods=["POST"])
def run_script():
    key = request.args.get("key")
    if key != SECRET_KEY:
        return jsonify({"status": "error", "message": "Invalid key"}), 403

    # Put your script logic here
    print("Running script from phone...")
    return jsonify({"status": "success", "message": "Script executed"})


@app.route("/shutdown", methods=["POST"])
def shutdown():
    if request.args.get("key") != SECRET_KEY:
        return jsonify({"status": "error", "message": "Invalid key"}), 403
    shutdown_func = request.environ.get("werkzeug.server.shutdown")
    if shutdown_func:
        shutdown_func()
        return jsonify({"status": "success", "message": "Server shutting down..."})
    else:
        return jsonify({"status": "error", "message": "Shutdown not available"}), 500


def run_flask():
    app.run(host="0.0.0.0", port=5000, use_reloader=False)


def start_server():
    global server_thread, server_running
    if not server_running:
        server_thread = threading.Thread(target=run_flask, daemon=True)
        server_thread.start()
        server_running = True
        print("Server started.")


def stop_server():
    global server_running
    if server_running:
        try:
            requests.post("http://localhost:5000/shutdown", params={"key": SECRET_KEY})
        except requests.exceptions.RequestException:
            pass
        server_running = False
        print("Server stopped.")


# -------------------
# PySide6 GUI + Tray
# -------------------
class EmittingStream(QObject):
    text_written = Signal(str)

    def write(self, text):
        if text.strip():  # avoid empty newlines
            self.text_written.emit(str(text))

    def flush(self):
        pass


class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Settings")

        self.layout = QVBoxLayout()

        self.status_label = QLabel("Checking server status...")
        self.layout.addWidget(self.status_label)

        self.start_button = QPushButton("Start Server")
        self.stop_button = QPushButton("Stop Server")

        self.start_button.clicked.connect(self.start_server)
        self.stop_button.clicked.connect(self.stop_server)

        self.layout.addWidget(self.start_button)
        self.layout.addWidget(self.stop_button)

        # 👇 Add log box
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        # self.log_box.moveCursor(QTextCursor.End)
        self.layout.addWidget(self.log_box)

        # 👇 Clear log button
        self.clear_button = QPushButton("Clear Logs")
        self.clear_button.clicked.connect(self.clear_logs)
        self.layout.addWidget(self.clear_button)

        self.setLayout(self.layout)
        self.update_buttons()

        # 👇 Redirect stdout/stderr
        sys.stdout = EmittingStream(text_written=self.append_log)
        sys.stderr = EmittingStream(text_written=self.append_log)

    def append_log(self, text):
        self.log_box.append(text)
        self.log_box.moveCursor(QTextCursor.End)  # auto-scroll to bottom

    def clear_logs(self):
        self.log_box.clear()

    def start_server(self):
        start_server()
        self.update_buttons()

    def stop_server(self):
        stop_server()
        self.update_buttons()

    def update_buttons(self):
        if server_running:
            self.status_label.setText("Server is running.")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
        else:
            self.status_label.setText("Server is stopped.")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def closeEvent(self, event):
        event.ignore()  # prevent the window from actually closing
        self.hide()  # hide instead


def main():
    # Start Qt app
    app_qt = QApplication(sys.argv)
    app_qt.setQuitOnLastWindowClosed(False)

    # Start server automatically
    start_server()

    tray = QSystemTrayIcon(QIcon.fromTheme("applications-system"))
    tray.setToolTip("Flask Server Controller")

    menu = QMenu()
    settings_action = QAction("Settings")
    exit_action = QAction("Exit")

    # Settings window
    settings_window = SettingsWindow()
    settings_action.triggered.connect(settings_window.show)

    # Exit action
    def quit_app():
        stop_server()
        app_qt.quit()

    exit_action.triggered.connect(quit_app)

    menu.addAction(settings_action)
    menu.addAction(exit_action)

    tray.setContextMenu(menu)
    tray.show()

    sys.exit(app_qt.exec())


if __name__ == "__main__":
    main()
