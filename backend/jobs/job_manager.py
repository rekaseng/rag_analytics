import uuid
from datetime import datetime
from jobs.job_models import Job

_JOBS = {}

def create_job() -> Job:
    job_id = str(uuid.uuid4())
    job = Job(
        job_id=job_id,
        status="processing",
        created_at=datetime.utcnow(),
        outputs={}
    )
    _JOBS[job_id] = job
    return job

def get_job(job_id: str) -> Job | None:
    return _JOBS.get(job_id)

def complete_job(job_id: str, outputs: dict):
    job = _JOBS[job_id]
    job.status = "completed"
    job.outputs = outputs

def fail_job(job_id: str, error: str):
    job = _JOBS[job_id]
    job.status = "failed"
    job.error = error
