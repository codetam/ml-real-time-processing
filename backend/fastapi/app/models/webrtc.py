from pydantic import BaseModel


class Offer(BaseModel):
    sdp: str
    type: str
    session_id: str