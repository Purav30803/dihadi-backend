from pydantic import BaseModel, EmailStr
from typing import List, Optional

class User(BaseModel):
    user_id: str
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
    # isEmployee: bool
