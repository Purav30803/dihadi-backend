from fastapi import APIRouter, Depends, HTTPException,Request
from app.db.mongodb import db
from app.core.middleware import get_current_user
from fastapi.security import OAuth2PasswordBearer
from app.schemas.job_post import JobPostCreate, JobPostBase,JobPostUpdate,JobPost
from app.models.user import User
from typing import List
import jwt
from app.core.config import SECRET_KEY, ALGORITHM
from bson import ObjectId
from datetime import datetime

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/create", response_model=JobPostBase)
async def create_job_post(job_post: JobPost, current_user: User = Depends(get_current_user)):
    job_post = job_post.dict()
    job_post['user_id'] = current_user.user_id  # Add user_id to job_post
    # insert timestamp
    job_post['timestamp'] = datetime.now()
    result = await db.job_post.insert_one(job_post)
    job_post['id'] = str(result.inserted_id)
    
    # Map user_id to employer_id for the response
    job_post['employer_id'] = job_post.pop('user_id')
    
    return job_post

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.get("/my_jobs", response_model=List[JobPostBase])  # Adjust return type
async def list_job_posts(token: str = Depends(oauth2_scheme)):
    try:
        # Decode the JWT and get the user ID
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get('id')  # Extract user ID from JWT payload

        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in token")
        user_id = str(user_id)  # Convert user_id to string
        # Query job posts for the given user
        job_posts_cursor = db["job_post"].find({"user_id": user_id})  # Ensure user_id is an ObjectId
        job_posts = await job_posts_cursor.to_list()  # Fetch all job posts for this user

        if not job_posts:
            raise HTTPException(status_code=404, detail="No job posts found for this user")

        # Transform `_id` to `id` for each job post
        for job in job_posts:
            if "job_title" not in job:
                raise HTTPException(status_code=500, detail="Job post missing required field: job_title")
            job["id"] = str(job.pop("_id"))
        

        return job_posts  # Return the modified job posts

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail="Invalid Token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.get("/job/{job_id}")
async def get_job_post(job_id: str):
    job_post = await db.job_post.find_one({"_id": ObjectId(job_id)})

    if not job_post:
        raise HTTPException(status_code=404, detail="Job post not found")

    job_post['id'] = str(job_post.pop('_id'))
    job_post['employer_id'] = job_post.pop('user_id')
    
    # fetch data from application collection
    application = await db.applications.find_one({"post_id": job_id})
    # return application
    users = []
    try:
        # Iterate over the user_ids in the application
        for user_data in application.get("user_ids", []):
            user_id = user_data.get("user_id")
            
            # Fetch user details from the database
            user = await db["users"].find_one({"_id": ObjectId(user_id)})
            if user:  # Ensure user exists
                # Convert MongoDB _id to string and add timestamp
                user["id"] = str(user.pop("_id"))
                user["timestamp"] = user_data.get("timestamp")
                # dont return password and image
                user.pop("password")
                user.pop("id_proof")
                users.append(user)   
    except Exception as e:
        print(f"Error fetching users: {e}")
    job_post['applications'] = users
    return job_post

@router.put("/job/{job_id}", response_model=JobPostBase)
async def update_job_post(job_id: str, job_post: JobPostUpdate):
    job_post_data = job_post.dict()  # Convert Pydantic model to dictionary
    
    # Remove 'employer_id' if it's not needed
    if 'employer_id' in job_post_data:
        job_post_data['user_id'] = job_post_data.pop('employer_id')
    
    result = await db.job_post.update_one({"_id": ObjectId(job_id)}, {"$set": job_post_data})
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Job post not found")
    
    updated_job = await db.job_post.find_one({"_id": ObjectId(job_id)})
    updated_job['id'] = str(updated_job.pop('_id'))
    
    return updated_job

@router.delete("/job/{job_id}")
async def delete_job_post(job_id: str):
    result = await db.job_post.delete_one({"_id": ObjectId(job_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Job post not found")
    
    return {"message": "Job post deleted successfully","status":200}

@router.get("/jobs", response_model=List[JobPostBase])
async def list_job_posts(token: str = Depends(oauth2_scheme),request: Request = None):
    # extract search query from the request
    job_title = request.query_params.get('search')
    print(job_title)
    try:
        # Decode the JWT and get the user ID
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get('id')  # Extract user ID from JWT payload

        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in token")
        user_id = str(user_id)  # Convert user_id to string
        # Query job posts for the given user
        job_posts_cursor = db["job_post"].find({"user_id": {"$ne": user_id},"status":"Active"})  # Ensure user_id is an ObjectId
        job_posts = await job_posts_cursor.to_list()  # Fetch all job posts for this user

        if not job_posts:
            raise HTTPException(status_code=404, detail="No job posts found for this user")

        # Transform `_id` to `id` for each job post
        for job in job_posts:
            if "job_title" not in job:
                raise HTTPException(status_code=500, detail="Job post missing required field: job_title")
            job["id"] = str(job.pop("_id"))
        
        # if users search for job it should filter from all job posts, skill, location, job title
        
        if job_title in job_posts:
            job_posts_cursor = db["job_post"].find({"job_title": job_title,"status":"Active"})  # Ensure user_id is an ObjectId
            job_posts = await job_posts_cursor.to_list()
            return job_posts
        
        
        final_job_posts = []
        for job in job_posts:
            if job_title in job['job_title']:
                final_job_posts.append(job)

        return final_job_posts  # Return the modified job posts

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail="Invalid Token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")