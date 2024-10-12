from pydantic import BaseModel

class Review(BaseModel):
    review_id: str
    job_id: str  # Reference to JobPost
    user_id: str  # Reference to User
    rating: int  # 1-5
    feedback: str