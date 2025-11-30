"""Minimal Flask entry point for the translation dashboard."""
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)


@app.route("/")
def dashboard():
    """Serve the single-page dashboard template."""
    return render_template("dashboard.html")


@app.route("/api/upload", methods=["POST"])
def upload_pdf():
    """Accept a PDF upload request and return a placeholder job identifier."""
    _file = request.files.get("file")  # noqa: F841 - placeholder until implemented
    # TODO: enqueue translation job and persist metadata
    return jsonify({"job_id": "demo-job-123", "status": "pending"}), 202


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
