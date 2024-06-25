import uvicorn
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import ssl
import uuid
import os
from dotenv import load_dotenv
from backend.databases.database import Database
from backend.services.chat import Herobot
from datetime import timedelta
from langchain import hub

# 환경변수 API키 로드
load_dotenv()
# 테스트용 ssl 설정 - Amadeus API https 요청을 위한 설정
ssl._create_default_https_context = ssl._create_unverified_context

prompt = hub.pull("test")

print(prompt)

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인 요청 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메소드 허용
    allow_headers=["*"]   # 모든 HTTP 헤더 허용
)


db = Database()
chatbot = Herobot(db)

def generate_session_id():
    return str(uuid.uuid4())

def get_session_id_from_cookie(request: Request):
    session_id = request.cookies.get('session_id')
    return session_id

@app.get("/")
async def read_root(request: Request, response: Response):
    session_id = get_session_id_from_cookie(request)
    if not session_id:
        session_id = generate_session_id()
        response.set_cookie(key="session_id", value=session_id, httponly=True, max_age=timedelta(days=1).total_seconds())
    return {"session_id": session_id}

@app.get("/get-session")
async def get_session(request: Request):
    session_id = get_session_id_from_cookie(request)
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID not found")
    return {"session_id": session_id}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5001, reload=True)