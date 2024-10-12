from pydantic import BaseModel

class Application(BaseModel):
    application_id: str
    user_id: str  # Reference to User
    post_id: str  # Reference to JobPost
    application_date: str  # Use str or a datetime object
    status: str  # e.g., 'applied', 'accepted', 'rejected'