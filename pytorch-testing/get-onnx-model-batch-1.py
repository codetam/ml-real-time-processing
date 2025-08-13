from ultralytics import YOLO

model = YOLO("yolo11s.pt")

model.export(
    format="onnx",
    imgsz=(640, 640),
    device=0,
    opset=17,
    dynamic=False
)