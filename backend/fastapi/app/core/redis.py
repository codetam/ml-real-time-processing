from datetime import datetime
import json
import os
import time

import aioredis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

def __generate_frame_id(session_id: str, frame_number: int):
    ts = int(time.time() * 1000)
    return f"{session_id}-{ts}-{frame_number}"

async def send_image_to_redis(redis_client: aioredis.Redis, data: bytes, session_id: str, frame_number: int):
    await redis_client.xadd("frames", {
        "session_id": session_id,
        "frame_id": __generate_frame_id(session_id, frame_number),
        "timestamp": datetime.now().isoformat() + "Z",
        "frame": data
    })
    
async def read_results(redis_client: aioredis.Redis, session_id: str):
    last_id = "0-0"
    i = 0
    while True:
        messages = await redis_client.xread({f"results:{session_id}": last_id}, count=1, block=1000)
        if messages:
            for stream, events in messages:
                for msg_id, fields in events:
                    last_id = msg_id
                    result = json.loads(fields[b"data"].decode())
                    yield result