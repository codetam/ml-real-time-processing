import onnxruntime as ort

# Load the ONNX model
model_path = "yolo11s-batch8.onnx"
session = ort.InferenceSession(model_path)

# Get model input details
print("=== Model Inputs ===")
for i, input_meta in enumerate(session.get_inputs()):
    print(f"Input {i}:")
    print(f"  Name: {input_meta.name}")
    print(f"  Shape: {input_meta.shape}")
    print(f"  Type: {input_meta.type}")

# Get model output details
print("\n=== Model Outputs ===")
for i, output_meta in enumerate(session.get_outputs()):
    print(f"Output {i}:")
    print(f"  Name: {output_meta.name}")
    print(f"  Shape: {output_meta.shape}")
    print(f"  Type: {output_meta.type}")
