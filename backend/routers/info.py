from fastapi import APIRouter


router = APIRouter(prefix="/api/v1")


@router.get("/info")
def get_info():
    return {
        "name": "Enterprise Knowledge Base Agent",
        "version": "0.1.0",
        "features": [
            "health_check",
            "chat_with_citations",
            "refusal_for_unknown_questions",
        ],
    }