from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from langchain_core.messages import HumanMessage, AIMessage
from backend.model.client import Client
class Message(BaseModel):
    session_id: Optional[str] = Field(description="session_id 값")
    type: Optional[str] = Field(description="question의 의도(search, flight, history, message)", default="")
    message: Optional[str] = Field(description="사용자나 개발자에게 받은 메시지 또는 llm의 메시지", default="")
    image: Optional[str] = Field(description="사용자가 전달한 이미지의 base64 문자열", default="")
    sender: str = Field(description="메시지를 보내는 사람(user, hero)", default="")
    client_info: Optional[Client] = Field(description="항공권 예약을 위한 사용자의 입력사항", default=None)
    history: Optional[str] = Field(description="답변에 참고할 대화 내역", default="")

class CustomHumanMessage(HumanMessage):
    additional_kwargs: Dict[str, Any] = Field(default_factory=dict)
    def __init__(self, **data):
        base_message = Message(**data)
        super().__init__(content=base_message.message, additional_kwargs=base_message.dict(by_alias=True))

class CustomAIMessage(AIMessage):
    additional_kwargs: Dict[str, Any] = Field(default_factory=dict)
    def __init__(self, **data):
        base_message = Message(**data)
        super().__init__(content=base_message.message, additional_kwargs=base_message.dict(by_alias=True))
