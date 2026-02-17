from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.db import models  # noqa: F401
from app.db.session import init_db
from app.services.events import EventBus, set_event_bus

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    bus = EventBus(settings.redis_url)
    await bus.connect()
    set_event_bus(bus)
    try:
        yield
    finally:
        await bus.close()


app = FastAPI(title="AaS API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_base_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)
