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
    print(user)
    # Insert user into the database
    user_dict = user.dict()
    user_dict['password'] = get_password_hash(user_dict['password'])  # Ensure password is hashed
    created_user = await db["users"].insert_one(user_dict)
    
    if not created_user.inserted_id:
        raise HTTPException(status_code=400, detail="User not created")
    
    # Fetch the inserted user with all its details
    created_user = await db["users"].find_one({"_id": created_user.inserted_id})
    
    # Map _id to user_id and ensure all required fields are present
    return UserResponse({
       "status_code":201,
       "message":"User created successfully",}
    
    )
