import os
import numpy as np
import tritonclient.http as httpclient
import cv2
from tritonclient.utils import np_to_triton_dtype

TRITON_HTTP_URL=os.environ.get("TRITON_HTTP_URL")

from yolo_utils import functions

model_to_layers_map: dict[str, tuple[str, str]] = {
    "yolo11": ("images", "output0")
}

def get_triton_http_client() -> httpclient.InferenceServerClient:
    client = httpclient.InferenceServerClient(url=TRITON_HTTP_URL, verbose=False)
    if not client.is_server_live():
        raise RuntimeError("Triton server is not live")
    return client

def test_model_ready(client: httpclient.InferenceServerClient, model_name: str):
    if not client.is_model_ready(model_name):
        raise RuntimeError(f"Model {model_name} is not ready")
    
def run_inference(image: cv2.typing.MatLike, model_name: str, client: httpclient.InferenceServerClient):
    
    img_w, img_h = image.shape[1], image.shape[0]
    input_data = functions.pre_process_image(image)

    input_layer, output_layer = model_to_layers_map[model_name]
    
    inputs = []
    inputs.append(httpclient.InferInput(input_layer, input_data.shape, np_to_triton_dtype(input_data.dtype)))
    inputs[0].set_data_from_numpy(input_data)

    outputs = []
    outputs.append(httpclient.InferRequestedOutput(output_layer))

    results = client.infer(
        model_name=model_name,
        inputs=inputs,
        outputs=outputs,
    )

    output_data = results.as_numpy(output_layer)
    results = output_data[0]
    results = results.transpose()
    detections = functions.filter_Detections(results)
    if len(detections) > 0:
        rescaled_results, confidences = functions.rescale_back(detections, img_w, img_h)
        return rescaled_results, confidences
    else:
        return ([], [])