import ssl
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.config import settings
from backend.api.session import router as session_router
from backend.api.chat import router as chat_router

# 테스트용 ssl 설정 - Amadeus API https 요청을 위한 설정
ssl._create_default_https_context = ssl._create_unverified_context

def create_app() -> FastAPI:
    app = FastAPI()

    # CORS 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOW_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],  # 모든 HTTP 메소드 허용
        allow_headers=["*"]   # 모든 HTTP 헤더 허용
    )



    # 라우터 포함
    app.include_router(session_router, prefix="/session", tags=["session"])
    app.include_router(chat_router, prefix="/chat", tags=["chat"])

    # 앱 시작 시 실행되는 초기화 함수
    @app.on_event("startup")
    async def startup_event():
        pass

    return app
