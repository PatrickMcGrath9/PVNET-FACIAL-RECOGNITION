# import face_recognition
# import cv2
# import numpy as np
# import pickle
# import pyttsx3
# import time
# import threading
# import os
# from concurrent.futures import ThreadPoolExecutor, as_completed
# from apscheduler.schedulers.background import BackgroundScheduler

# # Parameters
# frame_skip = 2
# frame_count = 0
# scaling_factor = 1  # Scale down for faster processing
# database_path = "C:/Users/Educa/Documents/GitHub/PVNET-FACIAL-RECOGNITION/Database"
# encoding_file = "encodings.pkl"

# # Load known faces and encodings
# def load_encodings():
#     if os.path.exists(encoding_file):
#         with open(encoding_file, "rb") as f:
#             return pickle.load(f)
#     return [], [], set()

# known_face_encodings, known_face_names, processed_images = load_encodings()

# # Initialize TTS engine
# engine = pyttsx3.init()
# last_spoken_time = {}
# face_detection_time = {}
# SPEAK_INTERVAL = 300  # 1 hour for known individuals
# UNKNOWN_SPEAK_INTERVAL = 30  # 30 seconds for unknown individuals
# DETECTION_TIME_REQUIRED = .35
# UNKNOWN_DETECTION_TIME_REQUIRED = 0.85  # Time required for unknown individuals

# # Initialize webcam
# video_capture = cv2.VideoCapture(0)
# video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
# video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
# video_capture.set(cv2.CAP_PROP_FPS, 30)
# video_capture.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)  # Enable auto-exposure

# # Function to calculate the average brightness of a frame
# def calculate_brightness(frame):
#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#     return np.mean(gray)

# # Adjust the brightness based on average frame brightness
# def adjust_brightness(video_capture, target_brightness=120):
#     ret, frame = video_capture.read()
#     if not ret:
#         return

#     avg_brightness = calculate_brightness(frame)
    
#     # Get current brightness setting
#     brightness_setting = video_capture.get(cv2.CAP_PROP_BRIGHTNESS)
    
#     # Adjust brightness incrementally
#     if avg_brightness < target_brightness - 10:
#         brightness_setting += 0.1  # Increase brightness
#     elif avg_brightness > target_brightness + 10:
#         brightness_setting -= 0.1  # Decrease brightness
    
#     # Set the new brightness level
#     video_capture.set(cv2.CAP_PROP_BRIGHTNESS, brightness_setting)

# def speak_name(name):
#     """Threaded function to speak a person's name."""
#     if name == "Unknown":
#         engine.say("Welcome to PVNet")
#     else:
#         engine.say(f"Hello {name}")
#     engine.runAndWait()

# def detect_faces(frame):
#     """Detect faces in a frame."""
#     return face_recognition.face_locations(frame, model="hog")

# def encode_face(frame, face_location):
#     """Encode a single face."""
#     return face_recognition.face_encodings(frame, [face_location])[0]

# def daily_encoding_update():
#     """Function to update encodings daily by adding new images."""
#     global known_face_encodings, known_face_names, processed_images

#     print("Starting daily encoding update...")
    
#     encoded_count = len(processed_images)
    
#     # Loop over each person in the database
#     for person_name in os.listdir(database_path):
#         person_folder = os.path.join(database_path, person_name)
        
#         if os.path.isdir(person_folder):
#             for image_name in os.listdir(person_folder):
#                 if image_name.endswith(('.jpg', '.jpeg', '.png')):
#                     image_path = os.path.join(person_folder, image_name)
#                     relative_image_path = os.path.relpath(image_path, database_path)
                    
#                     if relative_image_path in processed_images:
#                         continue
                    
#                     image = face_recognition.load_image_file(image_path)
#                     face_encodings = face_recognition.face_encodings(image)

#                     if face_encodings:
#                         known_face_encodings.append(face_encodings[0])
#                         known_face_names.append(person_name)
#                         processed_images.add(relative_image_path)
#                         encoded_count += 1

#     # Save updated encodings to file
#     with open(encoding_file, "wb") as f:
#         pickle.dump((known_face_encodings, known_face_names, processed_images), f)
#     print(f"Daily encoding update completed. {encoded_count} new images processed.")

#     # Exit the script after encoding to trigger a restart
#     os._exit(0)

# # Schedule daily encoding update at 1 PM
# scheduler = BackgroundScheduler()
# scheduler.add_job(daily_encoding_update, 'cron', hour=13)
# scheduler.start()

# # Main loop for continuous recognition
# executor = ThreadPoolExecutor()
# try:
#     while True:
#         ret, frame = video_capture.read()
#         if not ret:
#             break

#         frame_count += 1
#         if frame_count % frame_skip != 0:
#             continue

#         # Adjust brightness every 10 frames
#         if frame_count % 10 == 0:
#             adjust_brightness(video_capture, target_brightness=120)

#         small_frame = cv2.resize(frame, (0, 0), fx=scaling_factor, fy=scaling_factor)
#         rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

#         detection_future = executor.submit(detect_faces, rgb_small_frame)
#         face_locations = detection_future.result()

#         face_encodings = []
#         face_names = []

#         if face_locations:
#             encoding_executor = ThreadPoolExecutor(max_workers=min(10, len(face_locations)))
#             encoding_futures = {encoding_executor.submit(encode_face, rgb_small_frame, loc): loc for loc in face_locations}

#             for future in as_completed(encoding_futures):
#                 try:
#                     face_encoding = future.result()
#                     face_encodings.append(face_encoding)
#                 except IndexError:
#                     pass
#                 except Exception as e:
#                     print(f"Encoding error: {e}")

#             encoding_executor.shutdown(wait=True)

#             for face_encoding in face_encodings:
#                 matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.45)
#                 name = "Unknown"

#                 face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
#                 best_match_index = np.argmin(face_distances) if matches else None
#                 if best_match_index is not None and matches[best_match_index]:
#                     name = known_face_names[best_match_index]

#                 current_time = time.time()
#                 detection_time_required = DETECTION_TIME_REQUIRED if name != "Unknown" else UNKNOWN_DETECTION_TIME_REQUIRED
#                 speak_interval = SPEAK_INTERVAL if name != "Unknown" else UNKNOWN_SPEAK_INTERVAL

#                 if name not in face_detection_time:
#                     face_detection_time[name] = current_time

#                 if current_time - face_detection_time[name] >= detection_time_required:
#                     if name not in last_spoken_time or (current_time - last_spoken_time[name]) > speak_interval:
#                         threading.Thread(target=speak_name, args=(name,)).start()
#                         last_spoken_time[name] = current_time

#                 face_names.append(name)

#             for name in list(face_detection_time.keys()):
#                 if name not in face_names:
#                     del face_detection_time[name]

#         for (top, right, bottom, left), name in zip(face_locations, face_names):
#             top = int(top / scaling_factor)
#             right = int(right / scaling_factor)
#             bottom = int(bottom / scaling_factor)
#             left = int(left / scaling_factor)

#             cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
#             cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
#             font_scale = (bottom - top) / 150
#             cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, font_scale, (255, 255, 255), 1)

#         cv2.imshow('Video', frame)

#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break

# finally:
#     video_capture.release()
#     cv2.destroyAllWindows()
#     executor.shutdown()
#     scheduler.shutdown()

import face_recognition
import cv2
import numpy as np
import pickle
import pyttsx3
import time
import threading
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from apscheduler.schedulers.background import BackgroundScheduler
import queue

# Parameters
frame_skip = 2
frame_count = 0
scaling_factor = 1.1  # Scale down for faster processing
database_path = "C:/Users/Educa/Documents/GitHub/PVNET-FACIAL-RECOGNITION/Database"
encoding_file = "encodings.pkl"

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
DETECTION_TIME_REQUIRED = .35
UNKNOWN_DETECTION_TIME_REQUIRED = 0.5  # Time required for unknown individuals

# Initialize webcam
video_capture = cv2.VideoCapture(0)
video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
video_capture.set(cv2.CAP_PROP_FPS, 30)
video_capture.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)  # Enable auto-exposure

# Function to calculate the average brightness of a frame
def calculate_brightness(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return np.mean(gray)

# Adjust the brightness based on average frame brightness
def adjust_brightness(video_capture, target_brightness=120):
    ret, frame = video_capture.read()
    if not ret:
        return

    avg_brightness = calculate_brightness(frame)
    
    # Get current brightness setting
    brightness_setting = video_capture.get(cv2.CAP_PROP_BRIGHTNESS)
    
    # Adjust brightness incrementally
    if avg_brightness < target_brightness - 10:
        brightness_setting += 0.1  # Increase brightness
    elif avg_brightness > target_brightness + 10:
        brightness_setting -= 0.1  # Decrease brightness
    
    # Set the new brightness level
    video_capture.set(cv2.CAP_PROP_BRIGHTNESS, brightness_setting)

# Create queue for speech requests
speech_queue = queue.Queue()

def speech_worker():
    """Threaded function to process speech requests from the queue."""
    while True:
        name = speech_queue.get()  # Get a name from the queue
        if name is None:
            break  # Exit if None is received (for clean shutdown)
        
        if name == "Unknown":
            engine.say("Welcome to PVNet")
        else:
            engine.say(f"Hello {name}")
        engine.runAndWait()

# Start the speech worker thread
speech_thread = threading.Thread(target=speech_worker, daemon=True)
speech_thread.start()

def request_speak(name):
    """Function to add a name to the speech queue."""
    speech_queue.put(name)

def detect_faces(frame):
    """Detect faces in a frame."""
    return face_recognition.face_locations(frame, model="hog")

def encode_face(frame, face_location):
    """Encode a single face."""
    return face_recognition.face_encodings(frame, [face_location])[0]

def daily_encoding_update():
    """Function to update encodings daily by adding new images."""
    global known_face_encodings, known_face_names, processed_images

    print("Starting daily encoding update...")

    encoded_count = len(processed_images)

    # Loop over each person in the database
    for person_name in os.listdir(database_path):
        person_folder = os.path.join(database_path, person_name)
        
        if os.path.isdir(person_folder):
            for image_name in os.listdir(person_folder):
                if image_name.endswith(('.jpg', '.jpeg', '.png')):
                    image_path = os.path.join(person_folder, image_name)
                    relative_image_path = os.path.relpath(image_path, database_path)
                    
                    if relative_image_path in processed_images:
                        continue
                    
                    image = face_recognition.load_image_file(image_path)
                    face_encodings = face_recognition.face_encodings(image)

                    if face_encodings:
                        known_face_encodings.append(face_encodings[0])
                        known_face_names.append(person_name)
                        processed_images.add(relative_image_path)
                        encoded_count += 1

    # Save updated encodings to file
    with open(encoding_file, "wb") as f:
        pickle.dump((known_face_encodings, known_face_names, processed_images), f)
    print(f"Daily encoding update completed. {encoded_count} new images processed.")

    # Exit the script after encoding to trigger a restart
    os._exit(0)

# Schedule daily encoding update at 1 PM
scheduler = BackgroundScheduler()
scheduler.add_job(daily_encoding_update, 'cron', hour=14)
scheduler.start()

# Main loop for continuous recognition
executor = ThreadPoolExecutor()
try:
    while True:
        ret, frame = video_capture.read()
        if not ret:
            break

        frame_count += 1
        if frame_count % frame_skip != 0:
            continue

        # Adjust brightness every 10 frames
        if frame_count % 10 == 0:
            adjust_brightness(video_capture, target_brightness=120)

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

        for (top, right, bottom, left), name in zip(face_locations, face_names):
            top = int(top / scaling_factor)
            right = int(right / scaling_factor)
            bottom = int(bottom / scaling_factor)
            left = int(left / scaling_factor)

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            font_scale = (bottom - top) / 150
            cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, font_scale, (255, 255, 255), 1)

        cv2.imshow('Video', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Shutdown and cleanup
    speech_queue.put(None)  # Signal the speech thread to exit
    video_capture.release()
    cv2.destroyAllWindows()
    executor.shutdown()
    scheduler.shutdown()
    speech_thread.join()  # Wait for the speech thread to finish


