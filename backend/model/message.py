from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict

class Message(BaseModel):
    session_id: str
    type: Optional[str] = ""
    message: Optional[str] = ""
    image: Optional[str] = ""
    sender: str
    client_info: Optional[Dict] = None

    class Config:
        arbitrary_types_allowed = True

