from fastapi import APIRouter, Depends

from backend.services.system_status_service import build_system_status


router = APIRouter(prefix="/api/v1/system")


def get_system_status_builder():
    return build_system_status


@router.get("/status")
def get_system_status(status_builder=Depends(get_system_status_builder)):
    return status_builder()
