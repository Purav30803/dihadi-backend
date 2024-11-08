from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from pydantic import BaseModel
from typing import Optional
from bson import ObjectId
from app.db.mongodb import db
from fastapi.security import OAuth2PasswordBearer

# TokenData for validation
class TokenData(BaseModel):
    email: Optional[str] = None

# Update User to expect a `user_id` field
class User(BaseModel):
    user_id: str
    email: str
    name: Optional[str] = None
    location: Optional[str] = None
    # Add other fields as required

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Modified get_current_user
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    print("token: ", token)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, "dihadi", algorithms=["HS256"])
        email: str = payload.get("email")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception

    user = await db.users.find_one({"email": token_data.email})
    if user is None:
        raise credentials_exception

    # Ensure ObjectId `_id` is mapped to `user_id` as a string
    user["user_id"] = str(user.pop("_id", None))
    
    return User(**user)
