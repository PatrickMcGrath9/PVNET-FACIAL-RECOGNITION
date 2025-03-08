import face_recognition
import cv2
import numpy as np
import pickle
import pyttsx3
import time
import threading
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
import datetime

# Parameters
frame_skip = 2
frame_count = 0
scaling_factor = .75  # Scale down for faster processing
database_path = "C:/Users/Educa/Documents/GitHub/PVNET-FACIAL-RECOGNITION/Database"
encoding_file = "encodings.pkl"

# Set the stop time (e.g., 6:00 PM)
STOP_TIME = ["11:59", "12:59", "13:59", "14:59", "15:59", "16:59", "17:59"]

# Load known faces and encodings
def load_encodings():
    if os.path.exists(encoding_file):
        with open(encoding_file, "rb") as f:
            return pickle.load(f)
    return [], [], set()

known_face_encodings, known_face_names, processed_images = load_encodings()

# Initialize TTS engine
engine = pyttsx3.init()
last_spoken_time = {}
face_detection_time = {}
SPEAK_INTERVAL = 300  # 1 hour for known individuals
UNKNOWN_SPEAK_INTERVAL = 60  # 30 seconds for unknown individuals
DETECTION_TIME_REQUIRED = .3
UNKNOWN_DETECTION_TIME_REQUIRED = 0.75 # Time required for unknown individuals

# Initialize webcam
video_capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)#library for streamlining camera video process
video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280) #monitor feed size resolution
video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720) #monitor feed size resolution
video_capture.set(cv2.CAP_PROP_FPS, 30)
video_capture.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)  # Enable auto-exposure, lighting

# Create queue for speech requests
speech_queue = queue.Queue() #needed for seperate voice lines, one at a time voicelines after detection

def speech_worker():
    """Threaded function to process speech requests from the queue."""
    while True:
        name = speech_queue.get()  # Get a name from the queue, FIFO
        if name is None: #no one there
            break  # Exit if None is received (for clean shutdown)
        
        if name == "Unknown":
            engine.say("Welcome to PVNet")
        else:
            if name == "Tiffany":
                engine.say(f"Hello {name} borbnation will fluorish.")
            elif name == "Patrick":
                engine.say(f"Hello {name} slayer of bugnation")
            elif name == "Tyler":
                engine.say(f"Hello {name}, ruler of the Monkeys")
            else:
                engine.say(f"Hello {name}")
            
        engine.runAndWait()

# Start the speech worker thread; divides resources
speech_thread = threading.Thread(target=speech_worker, daemon=True)
speech_thread.start()

def request_speak(name): #like add to a queue
    """Function to add a name to the speech queue.""" 
    speech_queue.put(name)

def detect_faces(frame):
    """Detect faces in a frame."""
    return face_recognition.face_locations(frame, model="hog")

def encode_face(frame, face_location):
    """Encode a single face."""
    return face_recognition.face_encodings(frame, [face_location])[0]

# Main loop for continuous recognition
executor = ThreadPoolExecutor()
try:
    while True:
        # Check if current time matches the stop time
        current_time = datetime.datetime.now().strftime("%H:%M")
        if current_time in STOP_TIME:
            print(f"Stop time reached at {STOP_TIME}. Exiting program.")
            break  # Exit the loop and stop the program
        
        ret, frame = video_capture.read()
        #ret is if the camera is running, frame is data face recog
        # If no frame is captured (camera might be disconnected), try reconnecting
        if not ret:
            print("Warning: No frame detected, trying to reconnect...")
            video_capture.release()  # Release the current camera
            video_capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Reinitialize the camera
            video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            video_capture.set(cv2.CAP_PROP_FPS, 30)
            video_capture.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)  # Enable auto-exposure
            time.sleep(2)  # Wait for the camera to reinitialize

            ret, frame = video_capture.read()  # Try reading the frame again
            if not ret:
                print("Error: Still no frame detected after reconnecting.")
                continue  # Skip to the next loop iteration if still no frame

        frame_count += 1
        if frame_count % frame_skip != 0:
            continue

        small_frame = cv2.resize(frame, (0, 0), fx=scaling_factor, fy=scaling_factor)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        detection_future = executor.submit(detect_faces, rgb_small_frame)
        face_locations = detection_future.result()

        face_encodings = []
        face_names = []

        if face_locations:
            encoding_executor = ThreadPoolExecutor(max_workers=min(10, len(face_locations)))
            encoding_futures = {encoding_executor.submit(encode_face, rgb_small_frame, loc): loc for loc in face_locations}

            for future in as_completed(encoding_futures):
                try:
                    face_encoding = future.result()
                    face_encodings.append(face_encoding)
                except IndexError:
                    pass
                except Exception as e:
                    print(f"Encoding error: {e}")

            encoding_executor.shutdown(wait=True)

            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.45)
                name = "Unknown"

                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances) if matches else None
                if best_match_index is not None and matches[best_match_index]:
                    name = known_face_names[best_match_index]

                current_time = time.time()
                detection_time_required = DETECTION_TIME_REQUIRED if name != "Unknown" else UNKNOWN_DETECTION_TIME_REQUIRED
                speak_interval = SPEAK_INTERVAL if name != "Unknown" else UNKNOWN_SPEAK_INTERVAL

                if name not in face_detection_time:
                    face_detection_time[name] = current_time

                if current_time - face_detection_time[name] >= detection_time_required:
                    if name not in last_spoken_time or (current_time - last_spoken_time[name]) > speak_interval:
                        request_speak(name)  # Add the name to the speech queue
                        last_spoken_time[name] = current_time

                face_names.append(name)

            for name in list(face_detection_time.keys()):
                if name not in face_names:
                    del face_detection_time[name]

        for (top, right, bottom, left), name in zip(face_locations, face_names): #tracking box in frames
            top = int(top / scaling_factor)
            right = int(right / scaling_factor)
            bottom = int(bottom / scaling_factor)
            left = int(left / scaling_factor)

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            font_scale = (bottom - top) / 150
            cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, font_scale, (255, 255, 255), 1)

        cv2.imshow('Video', frame) #showing to monitor

        if cv2.waitKey(1) & 0xFF == ord('q'): #keyboard command to quit
            break

finally:
    # Shutdown and cleanup
    speech_queue.put(None)  # Signal the speech thread to exit
    video_capture.release()
    cv2.destroyAllWindows()
    executor.shutdown()
    speech_thread.join()  # Wait for the speech thread to finish
