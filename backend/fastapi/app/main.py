from datetime import datetime
import logging
import os
import uuid
import aioredis
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.testclient import TestClient
from app.api.routes import image, models, results, stream
from app.utils.formatting import handler
from fastapi.middleware.cors import CORSMiddleware

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
start_time = datetime.now()

app.include_router(results.router)
app.include_router(models.router)
app.include_router(image.router)
app.include_router(stream.router)

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/session")
async def create_session():
    session_id = str(uuid.uuid4())
    return {"session_id": session_id}

@app.get("/health")
async def healthcheck():
    return {"status": "ok", "uptime_seconds": (datetime.now() - start_time).total_seconds()}