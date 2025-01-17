import cv2

def initialize_camera():
    # Open the default camera
    video_capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Use DirectShow for better compatibility (Windows)
    
    if not video_capture.isOpened():
        print("Error: Unable to access the camera.")
        exit()

    print("Camera initialized with default settings (driver-controlled).")
    return video_capture

# Initialize the webcam
video_capture = initialize_camera()

# Main loop to display the video
while True:
    ret, frame = video_capture.read()
    if not ret:
        print("Error: Unable to read a frame from the camera.")
        break

    # Display the frame
    cv2.imshow("Webcam - Default Auto Settings", frame)

    # Exit when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
video_capture.release()
cv2.destroyAllWindows()
