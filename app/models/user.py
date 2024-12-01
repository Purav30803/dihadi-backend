from pydantic import BaseModel, EmailStr
from typing import List, Optional,Dict

class User(BaseModel):
    user_id: str
    name: str
    email: EmailStr
    phone: str
    password: str
    age: int
    applied_jobs: List[str]
    # nationality: str
    is_student: bool
    skills: List[str]
    id_proof: str
    # add json field for user profile
    working_hours: Optional[Dict[str, Optional[str]]] = None
    # company_name: Optional[str] = None
    location: Optional[str] = None
    # isEmployee: bool
