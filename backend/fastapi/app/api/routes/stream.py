from fastapi import APIRouter, HTTPException, Request

from app.core.redis import read_webrtc_answer, send_webrtc_offer
from app.models.webrtc import Offer

router = APIRouter(
    prefix="/stream",
    tags=["stream"],
)

@router.post("/webrtc/offer")
async def webrtc_offer(offer: Offer, request: Request):
    try:
        session_id = offer.session_id
        await send_webrtc_offer(request.app.state.redis, offer)
        
        answer = await read_webrtc_answer(request.app.state.redis, session_id)
        return answer
    except Exception as e:
        raise HTTPException(504, str(e))