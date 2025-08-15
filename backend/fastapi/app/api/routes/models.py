from fastapi import APIRouter
from fastapi.responses import JSONResponse
import requests
import os

TRITON_HTTP_URL = os.environ.get("TRITON_HTTP_URL")

router = APIRouter(
    prefix="/models",
    tags=["models"],
)

@router.get("/")
def get_active_models() -> JSONResponse:
    response = requests.post(f"http://{TRITON_HTTP_URL}/v2/repository/index",json={
        "ready": True
    })
    response.raise_for_status()
    data = response.json()
    names = []
    for model in data:
        names.append(model["name"])
    return JSONResponse({"models": names})