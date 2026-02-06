from fastapi import HTTPException
from jobs.job_manager import get_job

def get_valid_job(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job
