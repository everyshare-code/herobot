from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict

class Message(BaseModel):
    type: Optional[str] = None
    time: Optional[datetime] = None
    message: Optional[str] = None
    image: Optional[str] = None
    sender: Optional[str] = None
    client_info: Optional[Dict] = None

    class Config:
        arbitrary_types_allowed = True
