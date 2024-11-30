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

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Create Application API
async def get_current_user_id(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")  # Extract user ID from the token payload
        if not user_id:
            raise HTTPException(status_code=403, detail="Invalid Token")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail="Invalid Token")

# Create Application API
@router.post("/apply")
async def create_application(
    post_id: str = Body(...),  # Job Post ID
    user_id: str = Depends(get_current_user_id),  # Extract user_id from token
):
    try:
        # Check if the job post exists
        existing_application = await db["applications"].find_one({"post_id": post_id})
        if not existing_application:
            # If no application exists, create a new application record
            application = Application(
                application_id=str(uuid.uuid4()),  # Generate unique ID
                user_ids=[{"user_id": user_id, "timestamp": datetime.utcnow().isoformat()}],
                post_id=post_id,
                status="pending",
            )
            await db["applications"].insert_one(application.dict())
        else:
            # If application exists, append the user_id and timestamp to the user_ids array
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

        return {"message": "Application created successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))