import asyncio
import contextlib
import json
import os
import time
from typing import Optional
from aiohttp import web

# pydantic, aiortc

from aioredis import Redis
import aioredis
from aiortc import RTCPeerConnection, RTCSessionDescription
from pydantic import BaseModel
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("aiortc").setLevel(logging.DEBUG)


REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
STREAM_PREFIX = os.getenv("STREAM_PREFIX", "frames")
FPS_TARGET = float(os.getenv("FPS_TARGET", "8") or 0)
JPEG_QUALITY = int(os.getenv("JPEG_QUALITY", "80"))
MAX_QUEUE = 2  # drop frames if we fall behind (simple backpressure)

pcs: set[RTCPeerConnection] = set()
answeres = set()
redis: Optional[Redis] = None

class Offer(BaseModel):
    sdp: str
    type: str
    session_id: Optional[str] = None

async def on_shutdown():
    global redis
    # Close all peer connections
    coros = [pc.close() for pc in list(pcs)]
    await asyncio.gather(*coros, return_exceptions=True)
    if redis:
        await redis.close()
      
    
async def create_webrtc_answer(params):
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    
    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(message):
            if isinstance(message, str) and message.startswith("ping"):
                channel.send("pong" + message[4:])

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print("Connection state: ", pc.connectionState)
        if pc.connectionState == "failed":
            await pc.close()
            pcs.discard(pc)
        
    await pc.setRemoteDescription(offer)
    
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    
    # Absolutely vital, need to be the answer in pc.localDescription
    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}    

async def offer_loop():
    redis = await aioredis.from_url("redis://redis:6379/0")
    while True:
        results = await redis.xread({"signaling:offers": "$"}, block=0)
        for _, msgs in results:
            for msg_id, fields in msgs:
                session_id = fields[b"session_id"].decode()
                sdp = fields[b"sdp"].decode()
                type_ = fields[b"type"].decode()
                params =  {
                    "sdp": sdp,
                    "type": type_
                }
                answer_data = await create_webrtc_answer(params)
                key = f"signaling:answers:{session_id}"
                await redis.rpush(key, json.dumps({
                    "sdp": answer_data["sdp"],
                    "type": answer_data["type"]
                }))

print("Starting WebRTC receiver")
if __name__ == "__main__":
    asyncio.run(offer_loop())