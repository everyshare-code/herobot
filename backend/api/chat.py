# backend/api/chat.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Cookie, HTTPException
from backend.model.messages import Message
from backend.databases.database import Database
from backend.services.chat import Herobot
from backend.services.connection_manager import ConnectionManager
import json

router = APIRouter()

# WebSocket 연결 관리 인스턴스 생성
manager = ConnectionManager()

# Herobot 인스턴스 생성
db = Database()
herobot = Herobot(db)

@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket, session_id: str = Cookie(None)):
    if not session_id:
        await websocket.close(code=1008)
        raise HTTPException(status_code=400, detail="Session ID not found")

    await manager.connect(websocket, session_id)
    try:
        while True:
            try:
                data = await websocket.receive_text()
                data_dict = json.loads(data)
                data_dict['session_id'] = session_id
                user_message = Message(**data_dict)
                response_message = herobot.response(user_message)
                await manager.send_json(response_message, session_id)
            except WebSocketDisconnect:
                manager.disconnect(session_id)
                break
    except WebSocketDisconnect:
        manager.disconnect(session_id)
