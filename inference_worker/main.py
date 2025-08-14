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
    
MODEL_NAME = "yolo11"

async def read_images_from_redis() -> None:
    redis = await aioredis.from_url(constants.REDIS_URL)
    print("Connected to redis")
    last_id = "0-0"
    triton_client = triton_utils.get_triton_http_client()
    triton_utils.test_model_ready(triton_client, MODEL_NAME)
    while True:
        messages = await redis.xread({"frames": last_id}, count=1, block=1000)
        if messages:
            for stream, events in messages:
                for msg_id, fields in events:
                    last_id = msg_id
                    
                    session_id: str = fields[b"session_id"].decode()
                    frame_id: str = fields[b"frame_id"].decode()
                    frame: bytes = fields[b"frame"]  # raw bytes
                    
                    start = time.time()
                    nparr = np.frombuffer(frame, np.uint8)
                    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    rescaled_results, confidences = triton_utils.run_inference(image, MODEL_NAME, triton_client)
                    processing_time_ms = (time.time() - start) * 1000
                    
                    detections = functions.get_detections_output(rescaled_results, confidences)
                    result = {
                        "session_id": session_id,
                        "frame_id": frame_id,
                        "timestamp": datetime.now().isoformat() + "Z",
                        "model_version": MODEL_NAME,
                        "processing_time_ms": processing_time_ms,
                        "detections": detections
                    }
                    await redis.xadd(f"results:{session_id}", {"data": json.dumps(result)})
        else:
            print("Polling for messages...")

print("Starting service")
output = asyncio.run(read_images_from_redis())