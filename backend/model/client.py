from pydantic import BaseModel, Field
from typing import Optional
class Client(BaseModel):
    adults: Optional[int] = Field(description="항공권 예약할 인원 수")
    origin: Optional[str] = Field(description="출발지 공항 이름")
    origin_location_code: Optional[str] = Field(description="출발지 공항 코드")
    destination: Optional[str] = Field(description="도착지 공항 이름")
    destination_location_code: Optional[str] = Field(description="도착지 공항 코드")
    departure_date: Optional[str] = Field(description="출발일")