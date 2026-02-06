from pydantic import BaseModel
from typing import Optional, Dict, Literal


# -------- Upload Response --------
class JobCreatedResponse(BaseModel):
    job_id: str
    status: Literal["processing"]
    message: str


# -------- Job Status --------
class JobStatusResponse(BaseModel):
    job_id: str
    status: Literal["processing", "completed", "failed"]
    outputs: Optional[Dict[str, str]] = None
    error: Optional[str] = None


# -------- Error Response --------
class ErrorResponse(BaseModel):
    status: Literal["error"]
    message: str
    details: Optional[str] = None
