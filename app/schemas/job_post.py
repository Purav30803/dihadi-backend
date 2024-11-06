from pydantic import BaseModel
from datetime import datetime
from typing import List

class JobPostBase(BaseModel):
    job_title: str
    job_description: str
    shift_start: datetime
    shift_end: datetime
    salary: float
    location: str
    skills_required: str
    status: str  # active, completed, cancelled

class JobPostCreate(JobPostBase):
    employer_id: str  # Reference to User's user_id

class JobPostOut(JobPostBase):
    post_id: str  # MongoDB ObjectId as string
    employer_id: str
