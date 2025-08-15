import io
from fastapi import APIRouter, HTTPException
from fastapi.testclient import TestClient

from app.core.redis import send_image_to_redis

router = APIRouter(
    prefix="/image",
    tags=["image"],
)

def test_upload_image(client):
    test_image = io.BytesIO(b"fake image bytes")
    response = client.post(
        "/image/test/yolo11/session123",
        files={"image": ("test.jpg", test_image, "image/jpg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["filename"] == "test.jpg"
    client.app.state.redis.xadd.assert_awaited_once()
