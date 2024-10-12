from fastapi import APIRouter, HTTPException
from app.schemas.user import UserCreate, UserResponse
from app.models.user import User
from app.db.mongodb import db
import bcrypt
from app.core.security import get_password_hash
from bson import ObjectId

router = APIRouter()

@router.post("/signup", response_model=UserResponse)
async def create_user(user: UserCreate):
    # Insert user into the database
    user_dict = user.dict()
    user_dict['password'] = get_password_hash(user_dict['password'])  # Ensure password is hashed
    created_user = await db["users"].insert_one(user_dict)
    
    if not created_user.inserted_id:
        raise HTTPException(status_code=400, detail="User not created")
    
    # Fetch the inserted user with all its details
    created_user = await db["users"].find_one({"_id": created_user.inserted_id})
    
    # Map _id to user_id and ensure all required fields are present
    return UserResponse(
        user_id=str(created_user["_id"]),
        name=created_user["name"],
        email=created_user["email"],
        phone=created_user["phone"],
        age=created_user["age"],
        # nationality=created_user["nationality"],
        is_student=created_user["is_student"],
        skills=created_user["skills"],
        id_proof=created_user["id_proof"],
        # company_name=created_user["company_name"],
        location=created_user["location"],
        # isEmployee=created_user.get("isEmployee", False)  # Default isEmployee to False if missing
    )
