from pydantic import BaseModel
from typing import List

class JobPost(BaseModel):
    post_id: str
    employer_id: str  # Reference to the User
    job_title: str
    job_description: str
    shift_start: str  # Use str or a datetime object
    shift_end: str
    salary: float
    location: str
    skills_required: List[str]
    status: str  # e.g., 'active', 'completed', 'cancelled'
