
            
# import face_recognition
# from PIL import Image, ImageDraw

# # Load the image
# image_path = "C:/Users/Educa/Documents/GitHub/PVNET-FACIAL-RECOGNITION/Database/Patrick/Patrick2.jpg"  # Change this to your image file
# image = face_recognition.load_image_file(image_path)

# # Detect facial landmarks
# face_landmarks_list = face_recognition.face_landmarks(image)

# # Convert to a PIL image for drawing
# pil_image = Image.fromarray(image)
# draw = ImageDraw.Draw(pil_image)

# # Draw facial landmarks
# for face_landmarks in face_landmarks_list:
#     for feature, points in face_landmarks.items():
#         draw.line(points, fill="red", width=2)  # Draw lines connecting feature points

# # Save and show the image
# output_path = "output_facial_features.jpg"
# pil_image.save(output_path)
# pil_image.show()

# print(f"Facial features image saved to {output_path}")


import cv2
import face_recognition
import pickle
import os

# Directory to store encodings
ENCODINGS_DIR = "encodings"
os.makedirs(ENCODINGS_DIR, exist_ok=True)

def capture_image(name):
    """Captures an image from the webcam and saves it."""
    video_capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    while True:
        ret, frame = video_capture.read()  # Capture frame
        cv2.imshow("Press 'SPACE' to capture or 'Q' to quit", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord(" "):  # Press SPACE to capture
            cv2.imwrite(f"{name}.jpg", frame)
            print(f"Image saved as {save_path}")
            break
        elif key == ord("q"):  # Press Q to quit
            video_capture.release()
            cv2.destroyAllWindows()
            return None

    video_capture.release()
    cv2.destroyAllWindows()
    return save_path

def encode_face(image_path, person_name):
    """Encodes the face in the image and saves the encoding."""
    image = face_recognition.load_image_file(image_path)
    face_encodings = face_recognition.face_encodings(image)

    if not face_encodings:
        print("⚠ No face detected. Try taking a clearer image.")
        return None

    encoding = face_encodings[0]  # Use the first face found

    # Save encoding
    encoding_path = os.path.join(ENCODINGS_DIR, f"{person_name}_encoding.pkl")
    with open(encoding_path, "wb") as f:
        pickle.dump({"name": person_name, "encoding": encoding}, f)

    print(f"✅ Face encoded and saved as {encoding_path}")
    return encoding

if __name__ == "__main__":
    name = input("Enter your name: ")
    image_path = capture_image(name)
    
    if image_path:
        encode_face(image_path, name)
