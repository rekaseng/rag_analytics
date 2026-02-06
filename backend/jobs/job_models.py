from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Optional

class Job(BaseModel):
    job_id: str
    status: str
    created_at: datetime
    outputs: Optional[Dict[str, str]] = None
    error: Optional[str] = None
