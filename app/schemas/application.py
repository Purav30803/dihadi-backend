from pydantic import BaseModel
from datetime import datetime
from typing import List

# Application Model
class Application(BaseModel):
    application_id: str
    user_ids: list  # List of dictionaries containing user_id and timestamp
    post_id: str  # Reference to JobPost
    status: str = "pending"  # Default status is "pending"