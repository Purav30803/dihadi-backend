from pydantic import BaseModel
from typing import List

class Application(BaseModel):
    application_id: str
    user_ids: List[str]  # List of User IDs
    post_id: str  # Reference to JobPost
    application_date: str  # Use str or a datetime object
    status: str  # Status of the application (e.g., pending, approved)
