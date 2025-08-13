import tritonclient.http as httpclient
import cv2
from tritonclient.utils import np_to_triton_dtype

from yolo_utils import functions

TRITON_URL = "triton:9002"
MODEL_NAME = "yolo11"

client = httpclient.InferenceServerClient(url=TRITON_URL, verbose=False)

if not client.is_server_live():
    raise RuntimeError("Triton server is not live")
if not client.is_model_ready(MODEL_NAME):
    raise RuntimeError(f"Model {MODEL_NAME} is not ready")

image = cv2.imread("img1.jpg")
img_w, img_h = image.shape[1], image.shape[0]
input_data = functions.pre_process_image(image)

inputs = []
inputs.append(httpclient.InferInput("images", input_data.shape, np_to_triton_dtype(input_data.dtype)))
inputs[0].set_data_from_numpy(input_data)

outputs = []
outputs.append(httpclient.InferRequestedOutput("output0"))

results = client.infer(
    model_name=MODEL_NAME,
    inputs=inputs,
    outputs=outputs,
)

output_data = results.as_numpy("output0")
print("Output shape:", output_data.shape)
print("First few values:", output_data.flatten()[:10])

results = output_data[0]
results = results.transpose()
results = functions.filter_Detections(results)
rescaled_results, confidences = functions.rescale_back(results, img_w, img_h)

cv2.imwrite("Output_triton.jpg", functions.draw_detections_on_image(image, rescaled_results, confidences))