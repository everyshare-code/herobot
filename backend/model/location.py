from pydantic import BaseModel
from typing import Optional
class Location(BaseModel):
    url: Optional[str] = None
    image_url: Optional[str] = None
    entity: Optional[str] = None
    class Config:
        arbitrary_types_allowed = True