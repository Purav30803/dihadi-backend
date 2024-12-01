from fastapi import APIRouter, HTTPException, Body, Depends
from pydantic import BaseModel
from typing import List
from datetime import datetime
from app.db.mongodb import db
import uuid  # For generating unique application IDs
from app.schemas.application import Application
from app.core.config import SECRET_KEY, ALGORITHM
import jwt
from fastapi.security import OAuth2PasswordBearer
from bson import ObjectId


router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Create Application API
async def get_current_user_id(token):
    
    try:
        print(token)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # print(payload)
        user_id = payload['id']
        if not user_id:
            raise HTTPException(status_code=403, detail="Invalid Token")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail="Invalid Token")

# Create Application API
@router.get("/apply")
async def create_application(post_id: str, token: str = Depends(oauth2_scheme)):
    try:
        # Extract user ID from the token
        user_id = await get_current_user_id(token)  # Implement this function to extract user_id from the token
        
        # Check if the job post already exists in applications
        existing_application = await db["applications"].find_one({"post_id": post_id})
        if not existing_application:
            # If no application exists, create a new application record
            application = Application(
                application_id=str(uuid.uuid4()),  # Generate unique ID
                user_ids=[{"user_id": user_id, "timestamp": datetime.utcnow().isoformat()}],
                post_id=str(post_id),
                status="pending",
            )
            await db["applications"].insert_one(application.dict())
        else:
            # If application exists, check if the user has already applied
            already_applied = any(
                user["user_id"] == user_id for user in existing_application["user_ids"]
            )
            if already_applied:
                raise HTTPException(
                    status_code=400, detail="User has already applied for this job."
                )

            # Append the new user with timestamp
            await db["applications"].update_one(
                {"post_id": post_id},
                {
                    "$push": {
                        "user_ids": {
                            "user_id": user_id,
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    }
                },
            )

        # Update the user's collection to include the post_id in their applications
        updated_user = await db["users"].find_one_and_update(
             {"_id": ObjectId(user_id)},
             {"$addToSet": {"applied_jobs": post_id}},  # Avoid duplicate entries
             return_document=True  # Return the updated document
        )

        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")

# Extract the `applied_jobs` list
        applied_jobs = updated_user.get("applied_jobs", [])

        return {"message": "Application created successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))