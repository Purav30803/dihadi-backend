from fastapi import APIRouter, HTTPException, Depends
from app.schemas.user import UserCreate, UserResponse, UserLogin, UserDocumentResponse
from app.models.user import User
from app.db.mongodb import db
from fastapi.responses import JSONResponse
import bcrypt
from app.core.security import get_password_hash, verify_password
import jwt
from app.core.config import SECRET_KEY, ALGORITHM
from fastapi.security import OAuth2PasswordBearer
import base64
import io
from PIL import Image

router = APIRouter()

@router.post("/signup", response_model=UserResponse)
async def create_user(user: UserCreate):
    print(user)
    # Insert user into the database
    user_dict = user.dict()
    user_dict['password'] = get_password_hash(user_dict['password'])  # Ensure password is hashed
    
    user_email = user_dict['email']
    user_exists_email = await db["users"].find_one({"email": user_email})
    if user_exists_email:
       raise HTTPException(status_code=400, detail="User with This Email Already Exists")
    
    user_phone = user_dict['phone']
    user_exists = await db["users"].find_one({"phone": user_phone})
    if user_exists:
        raise HTTPException(status_code=400, detail="User with This Phone Number Already Exists")
    
    created_user = await db["users"].insert_one(user_dict)
    
    if not created_user.inserted_id:
        raise HTTPException(status_code=500, detail="Failed to create user")
    
    
    return JSONResponse({
       "status_code":201,
       "message":"User created successfully",}
    
    )

# Login
@router.post("/login")
async def login_user(user:UserLogin):
    user_dict = user.dict()
    user_email = user_dict['email']
    user_password = user_dict['password']
    print(user_email)
    print(user_password)
    user_exists = await db["users"].find_one({"email": user_email})
    
    
    if not user_exists:
        raise HTTPException(status_code=400, detail="User with this email address does not exist")
    
    
    correctPassword = verify_password(user_password, user_exists['password'])
    
    if not correctPassword:
        raise HTTPException(status_code=400, detail="Invalid Password")
    
    # create a token
    token = jwt.encode({"email": user_email}, SECRET_KEY, algorithm=ALGORITHM)
    return JSONResponse({
        "status_code":200,
        "message":"Login Successful",
        "token":token,
    })
    
# get user token from header and find user
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.get("/me", response_model=UserResponse)
async def get_user(token: str = Depends(oauth2_scheme)):
    print(token)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # print(payload)
        user = await db["users"].find_one({"email": payload['email']})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail="Invalid Token")


@router.get("/me/document",response_model=UserDocumentResponse)
async def get_user_document(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user = await db["users"].find_one({"email": payload['email']})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        id_proof = user.get('id_proof')
        # convert base64 to image
    
        # convert base64 to image
      
        
        
        
        return JSONResponse({
            "status_code":200,
            "id_proof":id_proof,
        })
    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail="Invalid Token")