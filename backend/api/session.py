from fastapi import APIRouter, Request, Response, HTTPException
from datetime import timedelta
from backend.utils.session_util import generate_session_id, get_session_id_from_cookie

router = APIRouter()

@router.get("/")
async def read_root(request: Request, response: Response):
    session_id = get_session_id_from_cookie(request)
    if not session_id:
        session_id = generate_session_id()
        response.set_cookie(key="session_id", value=session_id, httponly=True, max_age=timedelta(days=1).total_seconds())
    return {"session_id": session_id}

@router.get("/get-session")
async def get_session(request: Request):
    session_id = get_session_id_from_cookie(request)
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID not found")
    return {"session_id": session_id}
