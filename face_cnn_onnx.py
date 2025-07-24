# face_cnn_onnx.py
import tensorflow as tf
import tf2onnx

# 1. Load your Keras model
model = tf.keras.models.load_model("face_cnn_model.h5")

# 2. Define the input signature (batch‑size can be variable)
spec = (tf.TensorSpec((None, 100, 100, 3), tf.float32, name="input"),)

# 3. Convert & save to ONNX
output_path = "face_cnn.onnx"
tf2onnx.convert.from_keras(
    model,
    input_signature=spec,
    opset=13,
    output_path=output_path
)

print(f"✅ Saved ONNX model to {output_path}")
