from pydantic import BaseModel
from datetime import datetime

class ApplicationBase(BaseModel):
    user_id: str  # Reference to User's user_id
    post_id: str  # Reference to JobPost's post_id
    application_date: datetime
    status: str  # applied, accepted, rejected

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationOut(ApplicationBase):
    application_id: str  # MongoDB ObjectId as string
