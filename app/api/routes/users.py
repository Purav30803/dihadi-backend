from fastapi import APIRouter, HTTPException, Depends
from app.schemas.user import UserCreate, UserResponse, UserLogin, UserDocumentResponse,UserUpdate,UserEmail,UserPassword
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
    
    # HTML email template with inline CSS
    html_body = f"""
    <html>
    <head>
        <style type="text/css">
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .container {{
                background-color: #f4f4f4;
                border-radius: 10px;
                padding: 30px;
                text-align: center;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .otp-code {{
                font-size: 24px;
                font-weight: bold;
                color: #007bff;
                background-color: #e9ecef;
                display: inline-block;
                padding: 10px 20px;
                border-radius: 5px;
                margin: 20px 0;
                letter-spacing: 3px;
            }}
            .disclaimer {{
                font-size: 12px;
                color: #6c757d;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Your One-Time Password (OTP)</h2>
            <p>Please use the following code to complete your verification:</p>
            <div class="otp-code">{otp}</div>
            <p class="disclaimer">
                If you did not request this OTP, please ignore this email or contact support.
            </p>
        </div>
    </body>
    </html>
    """
    
    # Prepare the email message
    msg = MIMEMultipart()
    msg["From"] = USER_EMAIL
    msg["To"] = email
    msg["Subject"] = "Your One-Time Password (OTP)"
    
    # Attach both plain text and HTML versions
    msg.attach(MIMEText(f"Your OTP code is: {otp}", "plain"))
    msg.attach(MIMEText(html_body, "html"))
    
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
async def get_applied_jobs(token: str = Depends(oauth2_scheme)):
    try:
        # Decode the token to get user information
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get('email')

        if not user_email:
            raise HTTPException(status_code=400, detail="Invalid token")

        # Fetch the user from the database
        user = await db["users"].find_one({"email": user_email})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        applied_job_ids = user.get('applied_jobs', [])
        jobs = []

        # Retrieve job details for each applied job ID
        for job_id in applied_job_ids:
            if isinstance(job_id, str):  # Ensure the job_id is in the correct format (string)
                try:
                    # Validate job_id as a valid ObjectId
                    object_id = ObjectId(job_id)
                except Exception:
                    continue  # Skip invalid job IDs

                job_details = await db["job_post"].find_one({"_id": object_id})
                if job_details:
                    # Build a sanitized response object
                    sanitized_job = {
                        "id": str(job_details["_id"]),
                        "title": job_details.get("title"),
                        "description": job_details.get("description"),
                        "salary": job_details.get("salary"),
                        "location": job_details.get("location"),
                        "status": job_details.get("status"),
                    }
                    jobs.append(sanitized_job)

        # Return the jobs as a structured JSON response
        return {
            "status_code": 200,
            "message": "Applied jobs retrieved successfully",
            "jobs": jobs,
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

        
@router.post("/forgot-otp")
async def forgot_otp(user:UserEmail):
    user_dict = user.dict()
    email = user_dict['email']
    user = await db["users"].find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    else:
        otp =  send_otp(email)
        await db["users"].update_one({"email": email}, {"$set": {"otp_forgot": otp}})
        return JSONResponse({
            "status_code":200,
            "message":"OTP sent successfully",
        })
        
@router.get("/forgot-password/verify")
async def verify_user(email:str, otp:int):
    user = await db["users"].find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    else:
        #drop otp from users collection
        if user['otp_forgot'] != otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")
        else:
            await db["users"].update_one({"email": email}, {"$unset": {"otp_forgot": ""}})
            return JSONResponse({
            "status_code":200,
            "message":"User verified successfully",
            })
            
@router.put("/password/reset-password")
async def reset_password(user:UserLogin):
    user_dict = user.dict()
    email = user_dict['email']
    print(email)
    password = user_dict['password']
    user = await db["users"].find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    else:
        await db["users"].update_one({"email": email}, {"$set": {"password": get_password_hash(password)}})
        return JSONResponse({
            "status_code":200,
            "message":"Password reset successfully",
        })
        
@router.put("/password/reset-password-user")
async def reset_password(user:UserPassword,token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    email = payload['email']
    user_dict = user.dict()
    password = user_dict['password']
    user = await db["users"].find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    else:
        await db["users"].update_one({"email": email}, {"$set": {"password": get_password_hash(password)}})
        return JSONResponse({
            "status_code":200,
            "message":"Password reset successfully",
        })