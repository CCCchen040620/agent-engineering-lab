from fastapi import FastAPI

from backend.routers.chat import router as chat_router
from backend.routers.info import router as info_router
from backend.routers.health import router as health_router
from backend.routers.documents import router as documents_router


app = FastAPI(title="Enterprise Knowledge Base Agent")

app.include_router(chat_router)
app.include_router(info_router)
app.include_router(health_router)
app.include_router(documents_router)