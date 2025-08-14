from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse, JSONResponse

from app.core.redis import read_results, send_image_to_redis

router = APIRouter(
    prefix="/stream",
    tags=["stream"],
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
            "model_version": result["model_version"],
            "processing_time_ms": result["processing_time_ms"],
            "detections": result["detections"]
        }
        await websocket.send_json(data)
        
@router.post("/upload-image/{session_id}")
async def upload_image(session_id: str, request: Request, image: UploadFile = File(...)):
    try:
        img_bytes = await image.read()
        await send_image_to_redis(request.app.state.redis, img_bytes, session_id, frame_number=1)
        return JSONResponse({"status": "ok", "filename": image.filename})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
