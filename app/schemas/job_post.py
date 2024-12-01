from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from bson import ObjectId

class JobPostBase(BaseModel):
    id: str
    job_title: str
    job_description: str
    shift_start: str
    shift_end: str
    salary: str
    location: str
    skills_required: str
    status: str  # active, completed, cancelled
    
class JobPostCreate(JobPostBase):
    employer_id: str  # Reference to User's user_id

class JobPostOut(JobPostBase):
    post_id: str  # MongoDB ObjectId as string
    employer_id: str

class JobPostUpdate(BaseModel):
    job_title: str
    job_description: str
    shift_start: str
    shift_end: str
    salary: str
    location: str
    skills_required: str
    status: str


class JobPost(BaseModel):
    job_title: str
    job_description: str
    shift_start: str
    shift_end: str
    salary: str
    location: str
    skills_required: str
    status: str 