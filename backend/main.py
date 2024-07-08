from backend.core.init_app import create_app
import uvicorn
from backend.core.config import settings

app = create_app()

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=settings.RELOAD)