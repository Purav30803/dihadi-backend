from pydantic import BaseModel, EmailStr
from typing import List, Optional

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    password: str
    age: int
    # nationality: str
    is_student: bool
    skills: List[str]
    id_proof: str
    # company_name: Optional[str] = None
    location: Optional[str] = None

class UserResponse(BaseModel):
    user_id: str
    name: str
    email: EmailStr
    phone: str
    age: int
    # nationality: str
    is_student: bool
    skills: List[str]
    id_proof: str
    # company_name: Optional[str] = None
    location: Optional[str] = None
    # isEmployee: bool

    class Config:
        orm_mode = True
