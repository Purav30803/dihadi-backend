from fastapi import APIRouter, HTTPException, Depends
from app.schemas.user import UserCreate, UserResponse, UserLogin, UserDocumentResponse,UserUpdate
from app.db.mongodb import db
from fastapi.responses import JSONResponse
import os
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.security import get_password_hash, verify_password
import jwt
from app.core.config import SECRET_KEY, ALGORITHM
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
from bson import ObjectId
from datetime import datetime, timedelta

router = APIRouter()
load_dotenv()

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
USER_EMAIL = os.getenv("USER_EMAIL")
USER_PASSWORD = os.getenv("USER_PASSWORD")

def send_otp(email):
    
    otp = random.randint(100000, 999999)
    subject = "Your OTP Code"
    body = f"Your OTP code is {otp}"

    msg = MIMEMultipart()
    msg["From"] = USER_EMAIL
    msg["To"] = email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(USER_EMAIL, USER_PASSWORD)
            server.sendmail(USER_EMAIL, email, msg.as_string())
        
        return otp  # Return the OTP for further processing if needed
    except smtplib.SMTPException as e:
        print(f"Failed to send email: {e}")
        return None



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
    
    # create OTP and send to user
    else:
        otp =  send_otp(user_email)    
    #    save otp in users collection
        await db["users"].update_one({"email": user_email}, {"$set": {"otp": otp}})
       
        
    
    return JSONResponse({
       "status_code":201,
       "message":"User created successfully",}
    
    )


@router.get("/verify")
async def verify_user(email:str, otp:int):
    user = await db["users"].find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    else:
        #drop otp from users collection
        if user['otp'] != otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")
        else:
            await db["users"].update_one({"email": email}, {"$unset": {"otp": ""}})
            return JSONResponse({
            "status_code":200,
            "message":"User verified successfully",
            })
         
def generate_token(user_email, user_id):
    expiration = datetime.utcnow() + timedelta(days=60)  # Token expires in 1 hour
    payload = {
        "email": user_email,
        "id": user_id,
        "exp": expiration  # Add the expiration claim
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

# Login
@router.post("/login")
async def login_user(user:UserLogin):
    user_dict = user.dict()
    user_email = user_dict['email']
    user_password = user_dict['password']
    print(user_email)
    print(user_password)
    otp_exists = await db["users"].find_one({"email": user_email, "otp": {"$exists": True}})
    if otp_exists:
        return JSONResponse({
            "status_code":400,
            "message":"User not verified",
        })
    user_exists = await db["users"].find_one({"email": user_email})
    
    
    if not user_exists:
        raise HTTPException(status_code=400, detail="User with this email address does not exist")
    
    
    correctPassword = verify_password(user_password, user_exists['password'])
    
    if not correctPassword:
        raise HTTPException(status_code=400, detail="Invalid Password")
    
    user_id = user_exists['_id']
    user_id = str(user_id)
    


# Example Usage
    token = generate_token(user_email, user_id)   
    return JSONResponse({
        "status_code":200,
        "message":"Login Successful",
        "token":token,
        
    })
    
# get user token from header and find user
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.get("/me", response_model=UserResponse)
async def get_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # print(payload)
        user = await db["users"].find_one({"email": payload['email']})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail="Invalid Token")
    
@router.get("/{id}", response_model=UserResponse)
async def get_user(id:str,token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # print(payload)
        user = await db["users"].find_one({"_id": ObjectId(id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail="Invalid Token")
    
    
@router.put("/me", response_model=UserUpdate)
async def update_user(user_update: UserUpdate, token: str = Depends(oauth2_scheme)):
    try:
        # Decode and validate the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("email")
        if not user_email:
            raise HTTPException(status_code=403, detail="Invalid Token")

        # Find the user by email
        user = await db["users"].find_one({"email": user_email})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user_id = user["_id"]
        
        # check phone number
        if user_update.phone:
            user_exists = await db["users"].find_one({"phone": user_update.phone})
            if user_exists and user_exists['_id'] != user_id:
                raise HTTPException(status_code=400, detail="User with this phone number already exists")   

        # Build the update dictionary
        update_data = user_update.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid fields to update")

        # Update the user in the database
        await db["users"].update_one({"_id": ObjectId(user_id)}, {"$set": update_data})

        # Fetch the updated user
        updated_user = await db["users"].find_one({"_id": ObjectId(user_id)})
        if not updated_user:
            raise HTTPException(status_code=404, detail="Failed to fetch updated user")

        # Convert ObjectId to string
        updated_user["_id"] = str(updated_user["_id"])

        # Return the updated user validated by UserUpdate
        return UserUpdate(**updated_user)

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=403, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail="Invalid Token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    

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
    

@router.get("/jobs/applied")
async def apply_job(token:str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user = await db["users"].find_one({"email": payload['email']})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user_id = user['_id']
        user_id = str(user_id)
        jobs_ids = user.get('applied_jobs')
        if not jobs_ids:
            jobs_ids = []
        
        jobs = []
        for job_id in jobs_ids:
            job = await db["job_post"].find_one({"_id": ObjectId(job_id)})
            if job:
                job['id'] = str(job.pop('_id'))
                jobs.append(job)
        return JSONResponse({
            "status_code":200,
            "jobs":jobs,
        })
    
    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail="Invalid Token")
        
        
    