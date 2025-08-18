# PVNET Facial Recognition System

PVNET Facial Recognition is a web-based platform for real-time facial detection, identification, and audit, designed to be accessible and extensible for research and practical deployment. This project is made possible by PVNET Advanced Technology Center.

## Abstract

PVNET Facial Recognition is a client-server system that enables live video facial detection and identification using ONNX models. The platform supports modular deployment of the FaceManager and DatabaseManager, allowing flexible configuration for local or remote use. The system is designed for ease of use, extensibility, and accessibility, with a modern web interface and audit tools for managing unknown faces.

Features:
- Real-time facial detection and identification via web interface
- Modular architecture: FaceManager and DatabaseManager can run locally or remotely
- Audit tool for reviewing and labeling unknown faces
- Configurable camera settings (resolution, framerate, etc.)
- Secure login and user management

To get started, clone the repository and follow the setup instructions below.

## System Overview (Frontend & Backend)

### Web Client

The client provides a live video feed with facial recognition capabilities. Users can adjust camera settings, enable/disable detection and identification, and audit unknown faces.

#### Controls

| Action            | Endpoint/Control                | Description                                 |
|-------------------|---------------------------------|---------------------------------------------|
| Start Video Feed  | `/video_feed`                   | View live camera feed                       |
| Audit Unknowns    | `/audit`                        | Review and label unknown faces              |
| Login             | `/login`                        | Secure access for administrators            |

#### Camera Settings

- `width=[int]` – Desired video width
- `height=[int]` – Desired video height
- `fps_target=[int]` – Desired framerate

### FaceManager & DatabaseManager

The backend consists of two main services:

- **FaceManager**: Handles facial detection and identification using ONNX models.
- **DatabaseManager**: Stores facial encodings and manages user identities.

#### Setup Instructions

##### Connecting the Client

1. Launch the client and navigate to `http://localhost:9253`
2. Access the video feed at `http://localhost:9253/video_feed`
3. Adjust camera and recognition settings via URL parameters as needed.

## Audit Tool

The audit interface allows administrators to review unknown faces detected by the system and assign labels or identities. This improves accuracy and helps build a robust facial database.

## Model & Data Requirements

- Download required ONNX models as specified in `/models/README.md`
- Configure paths in `config.json`

## Background

This project was developed as part of PVNET’s initiative to advance accessible and ethical facial recognition technology. The goal is to provide a flexible platform for research, security, and accessibility applications, while maintaining transparency and user control.

## Aspects of Improvement

Areas for future development include:
- Expanding recognition accuracy with additional models
- Improving UI accessibility and responsiveness
- Integrating advanced audit workflows (bulk labeling, feedback)
- Supporting mobile and edge deployments

## Team Members

