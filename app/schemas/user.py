from pydantic import BaseModel, EmailStr
from typing import List, Optional,Dict


class UserCreate(BaseModel):
    name: str
    email: str
    phone: str
    password: str
    age: int
    # nationality: str
    is_student: bool
    skills: str
    id_proof: str
    working_hours: Optional[Dict[str, Optional[str]]] = None
    applied_jobs: Optional[List[str]] = None
    # company_name: Optional[str] = None
    location: Optional[str] = None

class UserResponse(BaseModel):
    # user_id: str
    name: str
    email: str
    phone: str
    age: int
    # nationality: str
    is_student: bool
    skills: str
    id_proof: str
    # company_name: Optional[str] = None
    location: Optional[str] = None
    working_hours: Optional[Dict[str, Optional[str]]] = None
    # isEmployee: bool

    class Config:
        orm_mode = True


class UserLogin(BaseModel):
    email: str
    password: str

class UserDocumentResponse(BaseModel):
    id_proof: str
    
class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    skills: Optional[str] = None  # Comma-separated string
    working_hours: Optional[dict] = None  # Dictionary of working hours
    id_proof: Optional[str] = None
    
class UserEmail(BaseModel):
    email: EmailStr
    
class UserPassword(BaseModel):
    password: str