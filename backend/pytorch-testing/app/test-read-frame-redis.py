import asyncio
from PIL import Image
from io import BytesIO
import aioredis
    
    
async def read_image_from_redis(session_id: str) -> None:
    redis = await aioredis.from_url("redis://redis:6379/0")
    last_id = "0-0"
    i = 0
    while True:
        messages = await redis.xread({"frames": last_id}, count=1, block=1000)
        if messages:
            for stream, events in messages:
                for msg_id, fields in events:
                    last_id = msg_id
                    session = fields[b"session"].decode()
                    frame = fields[b"frame"]  # raw bytes
                    image = Image.open(BytesIO(frame))
                    image.save(f"{i}.jpg")
                    result = {"labels": ["person"], "conf": [0.97]}
                    await redis.xadd(f"results:{session}", {"result": str(result)})
                    i += 1
    
session_id = "1234"
output = BytesIO()
im = Image.open("bus.jpg")
im.save(output, format=im.format)

output = asyncio.run(read_image_from_redis(session_id))