import cv2
import threading
from deepface import DeepFace

# Load reference image (known face)
reference_img = cv2.imread("luna.JPG")

# Create a Haar Cascade classifier for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Open a video capture object
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

face_match = False
faces = []
match_distance = None

# Adjust these parameters to fine-tune the verification
model_name = "Facenet512"  # You can try "Facenet", "OpenFace", "DeepFace", "DeepID"
distance_metric = "cosine"  # You can try "cosine", "euclidean", "euclidean_l2"
threshold = 0.4  # Lower threshold for stricter verification

def face_read(frame, faces):
    global face_match, match_distance
    try:
        for (x, y, w, h) in faces:
            detected_face = frame[y:y + h, x:x + w]
            result = DeepFace.verify(detected_face, reference_img.copy(), model_name=model_name, distance_metric=distance_metric)
            distance = result['distance']
            face_match = distance < threshold
            match_distance = distance
    except Exception as e:
        print(f"Error detecting or verifying face: {e}")
        face_match = False
        match_distance = None

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    # Set face_match to False if no faces are detected
    if len(faces) == 0:
        face_match = False
        match_distance = None

    # Run face verification periodically in a separate thread
    if threading.active_count() == 1 and len(faces) > 0:  # Ensure only one thread is running and faces are detected
        threading.Thread(target=face_read, args=(frame.copy(), faces)).start()

    # Draw rectangles and text around faces
    for (x, y, w, h) in faces:
        color = (0, 255, 0) if face_match else (0, 0, 255)
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

        if face_match:
            text = f"Match ({match_distance:.2f})"
        elif match_distance == None:
            text = f"Wait, Face not detected"
        else:
            text = f"No Match({match_distance:.2f})"
        # text = f"Match ({match_distance:.2f})" if face_match  else f"No Match ({match_distance})"
        cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

    status_text = f"Match ({match_distance:.2f})" if face_match and match_distance is not None else "None"


    cv2.putText(frame, status_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1,
                (0, 255, 0) if face_match else (0, 0, 255), 2)
    cv2.imshow("Frame", frame)

    key = cv2.waitKey(1)
    if key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()