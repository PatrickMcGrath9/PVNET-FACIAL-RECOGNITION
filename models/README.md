## Download and place each here in the `/models` directory:

1. https://github.com/onnx/models/blob/main/validated/vision/body_analysis/arcface/model/arcfaceresnet100-8.onnx
2. https://github.com/opencv/opencv_zoo/raw/refs/heads/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx?download=
- Update `/config.json` with the new paths to models if necessary

## Consider switching to:

1. Detector: https://github.com/onnx/models/tree/main/validated/vision/body_analysis/ultraface

### Also consider testing the int8 quantized and block quantized models