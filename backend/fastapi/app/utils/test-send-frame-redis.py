import asyncio
from datetime import datetime
import json
import time
from PIL import Image
from io import BytesIO
import aioredis

REDIS_URL = "redis://redis:6379/0"

def generate_frame_id(session_id: str, frame_number: int):
    ts = int(time.time() * 1000)
    return f"{session_id}-{ts}-{frame_number}"

async def send_image_to_redis(data: bytes, session_id: str, frame_number: int):
    redis = await aioredis.from_url(REDIS_URL)
    await redis.xadd("frames", {
        "session_id": session_id,
        "frame_id": generate_frame_id(session_id, frame_number),
        "timestamp": datetime.now().isoformat() + "Z",
        "frame": data
    })
    

async def read_results(session_id: str):
    redis = await aioredis.from_url(REDIS_URL)
    last_id = "0-0"
    i = 0
    while True:
        messages = await redis.xread({f"results:{session_id}": last_id}, count=1, block=1000)
        if messages:
            for stream, events in messages:
                for msg_id, fields in events:
                    last_id = msg_id
                    result = json.loads(fields[b"data"].decode())
                    
                    session_id = result["session_id"]
                    frame_id = result["frame_id"]
                    timestamp = result["timestamp"]
                    model_version = result["model_version"]
                    processing_time_ms = result["processing_time_ms"]
                    detections = result["detections"]
                    print(detections)


session_id = "1234"
output = BytesIO()
im = Image.open("/project/app/bus.jpg")
im.save(output, format=im.format)
# asyncio.run(send_image_to_redis(output.getvalue(), session_id, "1"))
asyncio.run(read_results(session_id))