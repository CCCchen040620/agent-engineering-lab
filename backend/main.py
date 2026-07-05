from fastapi import FastAPI

from backend.routers.chat import router as chat_router
from backend.routers.info import router as info_router


app = FastAPI(title="Enterprise Knowledge Base Agent")

app.include_router(chat_router)
app.include_router(info_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}