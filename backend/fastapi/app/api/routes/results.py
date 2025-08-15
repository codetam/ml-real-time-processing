from fastapi import APIRouter
from fastapi import WebSocket

from app.core.redis import read_results

router = APIRouter(
    prefix="/results",
    tags=["results"],
)

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(session_id: str, websocket: WebSocket):
    await websocket.accept()
    redis_client = websocket.app.state.redis
    async for result in read_results(redis_client, session_id):
        data = {
            "session_id": result["session_id"],
            "frame_id": result["frame_id"],
            "timestamp": result["timestamp"],
            "model_name": result["model_name"],
            "processing_time_ms": result["processing_time_ms"],
            "detections": result["detections"]
        }
        await websocket.send_json(data)