from fastapi import FastAPI

from backend.error_handlers import register_error_handlers
from backend.logging_config import configure_logging
from backend.request_id_middleware import add_request_id
from backend.routers.chat import router as chat_router
from backend.routers.info import router as info_router
from backend.routers.health import router as health_router
from backend.routers.documents import router as documents_router
from backend.routers.db_documents import router as db_documents_router
from backend.routers.feedback import router as feedback_router
from backend.routers.agent import router as agent_router
from backend.routers.langgraph_agent import router as langgraph_agent_router
from backend.routers.memory_demo import router as memory_demo_router
from backend.routers.conversations import router as conversations_router
from backend.routers.system import router as system_router
from backend.routers.postgresql_documents import router as postgresql_documents_router
from backend.routers.tasks import router as tasks_router


configure_logging()
app = FastAPI(title="Enterprise Knowledge Base Agent")
app.middleware("http")(add_request_id)
register_error_handlers(app)

app.include_router(chat_router)
app.include_router(info_router)
app.include_router(health_router)
app.include_router(documents_router)
app.include_router(db_documents_router)
app.include_router(feedback_router)
app.include_router(agent_router)
app.include_router(langgraph_agent_router)
app.include_router(memory_demo_router)
app.include_router(conversations_router)
app.include_router(system_router)
app.include_router(postgresql_documents_router)
app.include_router(tasks_router)