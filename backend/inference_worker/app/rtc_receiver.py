import asyncio
import json
import logging
import os
import time

import aioredis
import cv2
import numpy as np
from aiortc import RTCPeerConnection, RTCSessionDescription

import tritonclient.grpc.aio as grpcclient
from tritonclient.utils import np_to_triton_dtype

from yolo_utils import functions

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logging.getLogger("aiortc").setLevel(logging.WARNING)
logging.getLogger("aioice").setLevel(logging.WARNING)
logging.getLogger("grpc").setLevel(logging.WARNING)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
TRITON_GRPC_URL = os.getenv("TRITON_GRPC_URL", "triton:8001")
# Process every Nth frame; at 30 fps this gives ~10 inference calls/s
INFERENCE_EVERY_N_FRAMES = int(os.getenv("INFERENCE_EVERY_N_FRAMES", "3"))

MODEL_IO = {
    "yolo11": ("images", "output0"),
}

pcs: set[RTCPeerConnection] = set()


# ---------------------------------------------------------------------------
# Inference (fully async, native gRPC — no thread executor needed)
# ---------------------------------------------------------------------------

async def run_inference_async(
    image: np.ndarray,
    model_name: str,
    client: grpcclient.InferenceServerClient,
):
    img_h, img_w = image.shape[:2]
    input_data = functions.pre_process_image(image)

    input_layer, output_layer = MODEL_IO[model_name]

    inputs = [grpcclient.InferInput(input_layer, list(input_data.shape), np_to_triton_dtype(input_data.dtype))]
    inputs[0].set_data_from_numpy(input_data)

    outputs = [grpcclient.InferRequestedOutput(output_layer)]

    response = await client.infer(model_name=model_name, inputs=inputs, outputs=outputs)

    raw = response.as_numpy(output_layer)[0].transpose()
    detections = functions.filter_Detections(raw)

    if len(detections) > 0:
        rescaled, confidences = functions.rescale_back(detections, img_w, img_h)
        return rescaled, confidences
    return [], []


# ---------------------------------------------------------------------------
# Per-connection video processing loop
# ---------------------------------------------------------------------------

async def process_video_track(track, channel_holder: dict, model_name: str, client: grpcclient.InferenceServerClient, session_id: str):
    log = logging.getLogger(f"session.{session_id[:8]}")
    log.info("Video processing task started (model=%s, throttle=every %d frames)", model_name, INFERENCE_EVERY_N_FRAMES)

    # Wait up to 5 s for the DataChannel to be set up by on_datachannel
    for i in range(50):
        if channel_holder["dc"] is not None:
            break
        await asyncio.sleep(0.1)
    else:
        log.warning("DataChannel never became available after 5 s — aborting")
        return

    channel = channel_holder["dc"]
    log.info("DataChannel is available (readyState=%s), starting frame loop", channel.readyState)

    frame_count = 0
    inference_count = 0

    while True:
        try:
            frame = await track.recv()
            frame_count += 1

            if frame_count % INFERENCE_EVERY_N_FRAMES != 0:
                continue

            if channel.readyState != "open":
                log.warning("DataChannel not open (state=%s), skipping frame", channel.readyState)
                continue

            # av.VideoFrame → BGR numpy array (same layout as OpenCV)
            img = frame.to_ndarray(format="bgr24")
            log.debug("Running inference on frame #%d (%dx%d)", frame_count, img.shape[1], img.shape[0])

            t0 = time.perf_counter()
            rescaled, confidences = await run_inference_async(img, model_name, client)
            elapsed_ms = (time.perf_counter() - t0) * 1000

            detections = functions.get_detections_output(rescaled, confidences)
            inference_count += 1
            log.info("Inference #%d done in %.1f ms — %d detection(s)", inference_count, elapsed_ms, len(detections))

            channel.send(json.dumps({"detections": detections, "inference_ms": round(elapsed_ms, 1)}))

        except asyncio.CancelledError:
            log.info("Video processing task cancelled")
            break
        except Exception as e:
            log.info("Video processing ended with: %s", e)
            break

    log.info("Video processing loop exited (frames received=%d, inferences=%d)", frame_count, inference_count)


# ---------------------------------------------------------------------------
# WebRTC peer-connection setup
# ---------------------------------------------------------------------------

async def create_webrtc_answer(params: dict, triton_client: grpcclient.InferenceServerClient):
    session_id = params["session_id"]
    model_name = params.get("model_name", "yolo11")
    log = logging.getLogger(f"session.{session_id[:8]}")

    log.info("Creating RTCPeerConnection for session %s (model=%s)", session_id, model_name)
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pcs.add(pc)

    # Shared mutable slot: on_datachannel writes here, process_video_track reads it
    channel_holder: dict = {"dc": None}

    @pc.on("datachannel")
    def on_datachannel(channel):
        log.info("DataChannel arrived: label=%s readyState=%s", channel.label, channel.readyState)
        channel_holder["dc"] = channel

        @channel.on("open")
        def on_open():
            log.info("DataChannel open")

        @channel.on("close")
        def on_close():
            log.info("DataChannel closed")

    @pc.on("track")
    async def on_track(track):
        log.info("Track received: kind=%s id=%s", track.kind, track.id)
        if track.kind == "video":
            asyncio.ensure_future(
                process_video_track(track, channel_holder, model_name, triton_client, session_id)
            )

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        log.info("Connection state → %s", pc.connectionState)
        if pc.connectionState in ("failed", "closed"):
            await pc.close()
            pcs.discard(pc)

    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        log.info("ICE connection state → %s", pc.iceConnectionState)

    @pc.on("icegatheringstatechange")
    async def on_icegatheringstatechange():
        log.info("ICE gathering state → %s", pc.iceGatheringState)

    log.info("Setting remote description (offer)")
    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    log.info("Local description set, answer ready")

    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}


# ---------------------------------------------------------------------------
# Main loop: read offers from Redis, produce answers
# ---------------------------------------------------------------------------

async def offer_loop():
    logging.info("Connecting to Redis at %s", REDIS_URL)
    redis = await aioredis.from_url(REDIS_URL)

    logging.info("Connecting to Triton gRPC at %s", TRITON_GRPC_URL)
    triton_client = grpcclient.InferenceServerClient(url=TRITON_GRPC_URL)
    if not await triton_client.is_server_live():
        raise RuntimeError("Triton server is not live — aborting")
    logging.info("Triton server is live. Waiting for WebRTC offers on 'signaling:offers'...")

    while True:
        results = await redis.xread({"signaling:offers": "$"}, block=0)
        for _, msgs in results:
            for _msg_id, fields in msgs:
                session_id = fields[b"session_id"].decode()
                params = {
                    "session_id": session_id,
                    "sdp": fields[b"sdp"].decode(),
                    "type": fields[b"type"].decode(),
                    "model_name": fields.get(b"model_name", b"yolo11").decode(),
                }
                logging.info("Offer received: session=%s model=%s", session_id, params["model_name"])

                answer_data = await create_webrtc_answer(params, triton_client)

                await redis.rpush(
                    f"signaling:answers:{session_id}",
                    json.dumps({"sdp": answer_data["sdp"], "type": answer_data["type"]}),
                )
                logging.info("Answer pushed for session %s", session_id)


if __name__ == "__main__":
    asyncio.run(offer_loop())
