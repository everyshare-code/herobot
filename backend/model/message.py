from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict

class Message(BaseModel):
    session_id: str
    type: str
    time: datetime
    message: Optional[str] = None
    image: Optional[str] = None
    sender: str
    client_info: Optional[Dict] = None

    class Config:
        arbitrary_types_allowed = True
