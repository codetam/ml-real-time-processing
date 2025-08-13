import logging
import os
import aioredis
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from app.api.routes import stream
from app.utils.formatting import handler

logging.basicConfig(
    level=logging.INFO,
    handlers=[handler]
)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = await aioredis.from_url(REDIS_URL)
    yield
    await app.state.redis.close()
    
app = FastAPI(lifespan=lifespan)

app.include_router(stream.router)
