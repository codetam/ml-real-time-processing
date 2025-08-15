from datetime import datetime
import json
import os
import time
from typing import AsyncGenerator

import aioredis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

def __generate_frame_id(session_id: str, frame_number: int):
    ts = int(time.time() * 1000)
    return f"{session_id}-{ts}-{frame_number}"

async def send_image_to_redis(redis_client: aioredis.Redis, model_name: str, data: bytes, session_id: str, frame_number: int):
    await redis_client.xadd("frames", {
        "session_id": session_id,
        "model_name": model_name,
        "frame_id": __generate_frame_id(session_id, frame_number),
        "timestamp": datetime.now().isoformat() + "Z",
        "frame": data
    })
    
async def read_results(
    redis_client: aioredis.Redis,
    session_id: str,
    idle_timeout: int = 60
) -> AsyncGenerator[dict, None]:
    last_id = "$"
    idle_counter = 0
    while True:
        messages = await redis_client.xread({f"results:{session_id}": last_id}, count=1, block=1000)
        
        if not messages:
            idle_counter += 1
            if idle_timeout and idle_counter >= idle_timeout:
                break
            continue
        for stream, events in messages:
            for msg_id, fields in events:
                last_id = msg_id
                try:
                    result = json.loads(fields[b"data"].decode())
                    yield result
                except Exception as e:
                    print(f"Error decoding message {msg_id}: {e}")