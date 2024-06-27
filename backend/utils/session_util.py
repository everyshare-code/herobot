import uuid
from fastapi import Request

# 세션 아이디 생성
def generate_session_id():
    return str(uuid.uuid4())

# 쿠키로 부터 세션 아이디 받아오기
def get_session_id_from_cookie(request: Request):
    return request.cookies.get('session_id')
