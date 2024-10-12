from pydantic import BaseModel

class ReviewBase(BaseModel):
    job_id: str  # Reference to JobPost's post_id
    user_id: str  # Reference to User's user_id
    rating: int  # Rating from 1 to 5
    feedback: str

class ReviewCreate(ReviewBase):
    pass

class ReviewOut(ReviewBase):
    review_id: str  # MongoDB ObjectId as string
