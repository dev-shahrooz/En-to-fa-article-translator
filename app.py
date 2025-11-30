"""Flask application exposing translation job management endpoints."""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Optional

from flask import Flask, jsonify, render_template, request, send_from_directory
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from core.pipeline import run_translation_pipeline


UPLOAD_DIR = Path("uploads")
TRANSLATED_DIR = Path("translated")

# Ensure directories exist at startup to avoid race conditions later on.
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
TRANSLATED_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Job:
    """Represents the lifecycle of a PDF translation request."""

    id: str
    filename_original: str
    filename_translated: str | None
    status: str  # "pending", "running", "done", "failed"
    error_message: str | None = None


class InMemoryJobStore:
    """Thread-safe in-memory storage for translation jobs."""

    def __init__(self) -> None:
        self._jobs: Dict[str, Job] = {}
        self._lock = threading.Lock()

    def create_job(self, filename_original: str) -> Job:
        job_id = str(uuid.uuid4())
        job = Job(
            id=job_id,
            filename_original=filename_original,
            filename_translated=None,
            status="pending",
            error_message=None,
        )
        with self._lock:
            self._jobs[job_id] = job
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def update_job(self, job_id: str, **updates: object) -> Optional[Job]:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            for key, value in updates.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            return job

    def next_pending_job(self) -> Optional[Job]:
        with self._lock:
            for job in self._jobs.values():
                if job.status == "pending":
                    job.status = "running"
                    return job
        return None


job_store = InMemoryJobStore()

app = Flask(__name__)


@app.route("/")
def dashboard() -> str:
    """Serve the single-page dashboard template."""

    return render_template("dashboard.html")


def _save_upload(file: FileStorage) -> str:
    """Persist an uploaded PDF under a unique filename and return its path."""

    filename = secure_filename(file.filename or "uploaded.pdf")
    unique_name = f"{uuid.uuid4()}_{filename}" if filename else str(uuid.uuid4())
    destination = UPLOAD_DIR / unique_name
    file.save(destination)
    return unique_name


def _process_pdf_job(job: Job) -> None:
    """Run the translation pipeline for the given job."""

    original_path = UPLOAD_DIR / job.filename_original
    translated_name = f"translated_{job.id}.pdf"
    translated_path = TRANSLATED_DIR / translated_name

    try:
        run_translation_pipeline(str(original_path), str(translated_path))
    except Exception as exc:  # pragma: no cover - background worker error path
        job_store.update_job(job.id, status="failed", error_message=str(exc))
        return

    job_store.update_job(
        job.id,
        status="done",
        filename_translated=translated_name,
        error_message=None,
    )


def _worker_loop(poll_interval: float = 1.0) -> None:
    """Continuously pick up pending jobs and process them."""

    while True:
        job = job_store.next_pending_job()
        if job:
            _process_pdf_job(job)
        else:
            time.sleep(poll_interval)


def start_worker() -> None:
    """Spawn the background worker thread if not already running."""

    worker = threading.Thread(target=_worker_loop, daemon=True, name="job-worker")
    worker.start()


@app.route("/api/upload", methods=["POST"])
def upload_pdf():
    """Accept a PDF upload, create a job, and return its identifier."""

    uploaded: FileStorage | None = request.files.get("file")
    if not uploaded or not uploaded.filename:
        return jsonify({"error": "No PDF file provided"}), 400

    if not uploaded.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF uploads are supported"}), 400

    saved_name = _save_upload(uploaded)
    job = job_store.create_job(filename_original=saved_name)
    return jsonify({"job_id": job.id}), 202


@app.route("/api/status/<job_id>", methods=["GET"])
def job_status(job_id: str):
    """Return structured information for the requested job."""

    job = job_store.get_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    return jsonify(asdict(job))


@app.route("/api/download/<job_id>", methods=["GET"])
def download(job_id: str):
    """Return the translated PDF for completed jobs."""

    job = job_store.get_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    if job.status != "done" or not job.filename_translated:
        return jsonify({"error": "Job not completed"}), 400

    file_path = TRANSLATED_DIR / job.filename_translated
    if not file_path.exists():
        return jsonify({"error": "Translated file missing"}), 404

    return send_from_directory(
        directory=TRANSLATED_DIR,
        path=job.filename_translated,
        as_attachment=True,
    )


# Start the worker as soon as the module is imported. In production this
# would likely be a separate process or managed by a task queue, but a
# lightweight daemon thread suffices for local development.
start_worker()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
