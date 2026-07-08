from fastapi import FastAPI

from backend.routers.chat import router as chat_router
from backend.routers.info import router as info_router
from backend.routers.health import router as health_router
from backend.routers.documents import router as documents_router
from backend.routers.db_documents import router as db_documents_router
from backend.routers.feedback import router as feedback_router
from backend.routers.agent import router as agent_router
from backend.routers.langgraph_agent import router as langgraph_agent_router
from backend.routers.memory_demo import router as memory_demo_router


app = FastAPI(title="Enterprise Knowledge Base Agent")

app.include_router(chat_router)
app.include_router(info_router)
app.include_router(health_router)
app.include_router(documents_router)
app.include_router(db_documents_router)
app.include_router(feedback_router)
app.include_router(agent_router)
app.include_router(langgraph_agent_router)
app.include_router(memory_demo_router)