import asyncio
from datetime import datetime
import json
import time
from PIL import Image
from io import BytesIO
import aioredis
import cv2
import numpy as np
from yolo_utils import functions, triton as triton_utils
import constants

async def read_images_from_redis() -> None:
    redis = await aioredis.from_url(constants.REDIS_URL)
    print("Connected to redis")
    
    group_name = "frame_consumers"
    consumer_name = "consumer_1"
    stream_name = "frames"

    # Create consumer group if it doesn't exist
    try:
        await redis.xgroup_create(stream_name, group_name, id="0-0", mkstream=True)
        print(f"Created consumer group '{group_name}' for stream '{stream_name}'")
    except aioredis.exceptions.ResponseError as e:
        if "BUSYGROUP" in str(e):
            # Group already exists
            pass
        else:
            raise
        
    triton_client = triton_utils.get_triton_http_client()
    while True:
        messages = await redis.xreadgroup(
            groupname=group_name,
            consumername=consumer_name,
            streams={stream_name: ">"},
            count=1,
            block=1000
        )
        if not messages:
            print("Polling for messages...")
            continue

        for stream, events in messages:
            for msg_id, fields in events:
                try:
                    session_id: str = fields[b"session_id"].decode()
                    frame_id: str = fields[b"frame_id"].decode()
                    frame: bytes = fields[b"frame"]  # raw bytes
                    model_name: str = fields[b"model_name"].decode()
                    
                    start = time.time()
                    nparr = np.frombuffer(frame, np.uint8)
                    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    rescaled_results, confidences = triton_utils.run_inference(
                        image, model_name, triton_client
                    )
                    processing_time_ms = (time.time() - start) * 1000
                    
                    detections = functions.get_detections_output(rescaled_results, confidences)
                    result = {
                        "session_id": session_id,
                        "frame_id": frame_id,
                        "timestamp": datetime.now().isoformat() + "Z",
                        "model_name": model_name,
                        "processing_time_ms": processing_time_ms,
                        "detections": detections
                    }
                    await redis.xadd(f"results:{session_id}", {"data": json.dumps(result)})
                    await redis.xack(stream_name, group_name, msg_id)
                except Exception as e:
                    print(f"Error processing message {msg_id}: {e}")

print("Starting service")
output = asyncio.run(read_images_from_redis())