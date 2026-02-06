from fastapi import APIRouter, UploadFile, File
from jobs.job_manager import create_job, complete_job, fail_job, get_job
from pipeline import run_pipeline
from api.dependencies import get_valid_job
from fastapi.responses import FileResponse

router = APIRouter()

@router.post("/jobs")
async def upload_ragas(file: UploadFile = File(...)):
    job = create_job()
    try:
        outputs = run_pipeline(job.job_id, await file.read())
        complete_job(job.job_id, outputs)
    except Exception as e:
        fail_job(job.job_id, str(e))
    return {"job_id": job.job_id, "status": job.status}

@router.get("/jobs/{job_id}")
def job_status(job_id: str):
    job = get_job(job_id)
    return job

@router.get("/jobs/{job_id}/download/{output_type}")
def download(job_id: str, output_type: str):
    job = get_valid_job(job_id)
    path = job.outputs.get(output_type)
    return FileResponse(path, filename=f"{output_type}.csv")
