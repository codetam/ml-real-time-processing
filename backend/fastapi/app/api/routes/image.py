from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from app.core.redis import read_results, send_image_to_redis

router = APIRouter(
    prefix="/image",
    tags=["image"],
)

@router.post("/test/{model_name}/{session_id}")
async def upload_image(model_name: str, session_id: str, request: Request, image: UploadFile = File(...)):
    try:
        img_bytes = await image.read()
        await send_image_to_redis(request.app.state.redis, model_name, img_bytes, session_id, frame_number=1)
        return {"status": "ok", "filename": image.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
