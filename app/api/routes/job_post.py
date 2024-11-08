from fastapi import APIRouter, HTTPException, Depends
from app.schemas import job_post as job_post_schema
from app.db.mongodb import db
from app.core.middleware import get_current_user
from bson import ObjectId
from fastapi.security import OAuth2PasswordBearer
from app.core.config import SECRET_KEY, ALGORITHM
import jwt
from app.schemas.user import UserCreate, UserResponse, UserLogin, UserDocumentResponse
from app.schemas.job_post import JobPostCreate, JobPostBase
from app.models.user import User

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/create", response_model=JobPostCreate)
async def create_job_post(job_post: JobPostBase, current_user: User = Depends(get_current_user)):
    job_post = job_post.dict()
    job_post['user_id'] = current_user.user_id  # Add user_id to job_post
    
    result = await db.job_post.insert_one(job_post)
    job_post['id'] = str(result.inserted_id)
    
    # Map user_id to employer_id for the response
    job_post['employer_id'] = job_post.pop('user_id')
    
    return job_post
