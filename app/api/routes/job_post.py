from fastapi import APIRouter, HTTPException, Depends
from app.schemas import job_post as job_post_schema
from app.db.mongodb import db
from app.core.middleware import get_current_user
from bson import ObjectId
from fastapi.security import OAuth2PasswordBearer
from app.core.config import SECRET_KEY, ALGORITHM
import jwt
from app.schemas.user import UserCreate, UserResponse, UserLogin, UserDocumentResponse

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.get("/create", response_model=UserResponse)
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

