import onnxruntime as ort
import cv2
import numpy as np

from yolo_utils import functions

mode_path = "yolo11s.onnx"
onnx_model = ort.InferenceSession(mode_path)
    
image = cv2.imread("bus.jpg")

img_w, img_h = image.shape[1], image.shape[0]

img = cv2.resize(image, (640, 640))
img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
img = img.transpose(2, 0, 1)
img = img.reshape(1, 3, 640, 640)

# Normalize pixel values to the range [0, 1]
img = img / 255.0

# Convert image to float32
img = img.astype(np.float32)

outputs = onnx_model.run(None, {"images": img})
results = outputs[0]
results = results.transpose()
results = functions.filter_Detections(results)
rescaled_results, confidences = functions.rescale_back(results, img_w, img_h)

cv2.imwrite("Output.jpg", functions.draw_detections_on_image(image, rescaled_results, confidences))