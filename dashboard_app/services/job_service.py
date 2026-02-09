# services/job_service.py

import requests
import pandas as pd
from io import BytesIO
from utils.constants import BACKEND_URL

# =========================
# Job Status Constants
# =========================
JOB_PENDING = "pending"
JOB_RUNNING = "running"
JOB_COMPLETED = "completed"
JOB_FAILED = "failed"

def normalize_job_status(status: str | None) -> str:
    """
    Normalize backend job status to lowercase string.
    Safe against None, uppercase, or unexpected input.
    """
    if not status:
        return JOB_PENDING
    return str(status).strip().lower()

def submit_job(json_file) -> str:
    resp = requests.post(
        BACKEND_URL,
        files={
            "file": (
                json_file.name,
                json_file.getvalue(),
                "application/json"
            )
        }
    )
    resp.raise_for_status()
    return resp.json()["job_id"]


def get_job_status(job_id: str) -> str:
    resp = requests.get(f"{BACKEND_URL}/{job_id}")
    resp.raise_for_status()
    job = resp.json()
    return normalize_job_status(job.get("status"))


def download_csv(job_id: str, output_type: str) -> pd.DataFrame:
    resp = requests.get(f"{BACKEND_URL}/{job_id}/download/{output_type}")
    resp.raise_for_status()
    return pd.read_csv(BytesIO(resp.content))
