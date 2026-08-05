from fastapi import FastAPI

from src.api.routers.system import router as system_router
from src.settings import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.fastapi.title,
    description=settings.fastapi.description,
    version=settings.fastapi.version,
)

app.include_router(system_router)
