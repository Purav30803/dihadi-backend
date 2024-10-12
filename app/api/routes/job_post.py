from fastapi import APIRouter, HTTPException, Depends
from app.schemas import job_post as job_post_schema
from app.db.mongodb import db
from bson import ObjectId

router = APIRouter()

@router.post("/job_posts/", response_model=job_post_schema.JobPostOut)
async def create_job_post(job_post: job_post_schema.JobPostCreate):
    # Insert the job post into MongoDB
    job_post_doc = {
        "employer_id": ObjectId(job_post.employer_id),
        "job_title": job_post.job_title,
        "job_description": job_post.job_description,
        "shift_start": job_post.shift_start,
        "shift_end": job_post.shift_end,
        "salary": job_post.salary,
        "location": job_post.location,
        "skills_required": job_post.skills_required,
        "status": job_post.status,
    }

    result = await db["job_posts"].insert_one(job_post_doc)

    return job_post_schema.JobPostOut(
        post_id=str(result.inserted_id),
        **job_post.dict()
    )
