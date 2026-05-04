from pydantic import BaseModel
from typing import Optional

class UserInfo(BaseModel):
    user_id: str
    email: str
    created_at: Optional[str] = None
