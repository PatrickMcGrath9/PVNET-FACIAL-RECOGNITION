# import face_recognition
# import cv2
# import numpy as np
# import pickle
# import pyttsx3
# import time
#
# scaling_frame = 1
# going_back_frame = 1/scaling_frame
# # print(going_back_frame)
#
# # Load the known faces and encodings
# with open("encodings.pkl", "rb") as f:
#     known_face_encodings, known_face_names, _ = pickle.load(f)  # The third value (processed_images) is ignored
#
# # Initialize TTS engine
# engine = pyttsx3.init()
#
# # Track the last time each person was recognized
# last_spoken_time = {}
# face_detection_time = {}  # New dictionary to track when faces are first detected
#
# # Time limits
# SPEAK_INTERVAL = 3600  # 1 hour
# DETECTION_TIME_REQUIRED = .5  # Half-second
#
# # Initialize some variables
# face_locations = []
# face_encodings = []
# face_names = []
# process_this_frame = True
#
# # Get a reference to webcam #0 (the default one)
# video_capture = cv2.VideoCapture(0)
#
# while True:
#     # Grab a single frame of video
#     ret, frame = video_capture.read()
#
#     # Only process every other frame of video to save time
#     if process_this_frame:
#         # Resize frame of video to 1/4 size for faster face recognition processing
#         small_frame = cv2.resize(frame, (0, 0), fx=scaling_frame, fy=scaling_frame)
#
#         # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
#         rgb_small_frame = np.ascontiguousarray(small_frame[:, :, ::-1])
#
#         # Find all the faces and face encodings in the current frame of video
#         face_locations = face_recognition.face_locations(rgb_small_frame)
#         face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
#
#         face_names = []
#         for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
#             # See if the face is a match for the known face(s)
#             matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
#             name = "Unknown"
#
#             # Use the known face with the smallest distance to the new face
#             face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
#             best_match_index = np.argmin(face_distances)
#             if matches[best_match_index]:
#                 name = known_face_names[best_match_index]
#
#                 # Track the time when the face was first detected
#                 current_time = time.time()
#                 if name not in face_detection_time:
#                     face_detection_time[name] = current_time
#
#                 # Check if the face has been detected for the required time
#                 if current_time - face_detection_time[name] >= DETECTION_TIME_REQUIRED:
#                     # Check if the name was spoken more than the SPEAK_INTERVAL
#                     if name not in last_spoken_time or (current_time - last_spoken_time[name]) > SPEAK_INTERVAL:
#                         # Say the name
#                         engine.say(f"Hello {name}")
#                         engine.runAndWait()
#
#                         # Update the last spoken time
#                         last_spoken_time[name] = current_time
#
#             face_names.append(name)
#
#         # Reset the detection time for faces not in the current frame
#         for name in list(face_detection_time.keys()):
#             if name not in face_names:
#                 del face_detection_time[name]
#
#     process_this_frame = not process_this_frame
#
#     # Display the results
#     for (top, right, bottom, left), name in zip(face_locations, face_names):
#         # Scale back up face locations since the frame we detected in was scaled to 1/4 size
#         top = int(top * going_back_frame)
#         right = int(right * going_back_frame)
#         bottom = int(bottom * going_back_frame)
#         left = int(left * going_back_frame)
#
#         # Draw a box around the face
#         cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
#
#         # Draw a label with a name below the face
#         cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
#         font = cv2.FONT_HERSHEY_DUPLEX
#         cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
#
#     # Display the resulting image
#     cv2.imshow('Video', frame)
#
#     # Hit 'q' on the keyboard to quit!
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break
#
# # Release handle to the webcam
# video_capture.release()
# cv2.destroyAllWindows()
#
#
#
#

import face_recognition
import cv2
import numpy as np
import pickle
import pyttsx3
import time
import threading

# Adjust frame processing frequency
frame_skip = 3  # Process every second frame
frame_count = 0

# Adjust the scaling factor for faster processing
scaling_frame = 1.5  # Adjust the scaling to a reasonable size for better performance
going_back_frame = 1 / scaling_frame

# Load the known faces and encodings
with open("encodings.pkl", "rb") as f:
    known_face_encodings, known_face_names, _ = pickle.load(f)  # The third value (processed_images) is ignored

# Initialize TTS engine
engine = pyttsx3.init()

# Track the last time each person was recognized
last_spoken_time = {}
face_detection_time = {}

# Time limits
SPEAK_INTERVAL = 3600  # 1 hour
DETECTION_TIME_REQUIRED = 0.5  # Half-second

# Initialize some variables
face_locations = []
face_encodings = []
face_names = []

# Get a reference to webcam #0 (the default one) and set lower resolution for faster processing
video_capture = cv2.VideoCapture(0)
video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

def speak_name(name):
    """Threaded function to speak a person's name using TTS."""
    engine.say(f"Hello {name}")
    engine.runAndWait()

while True:
    # Grab a single frame of video
    ret, frame = video_capture.read()

    # Skip frames to reduce workload
    if frame_count % frame_skip == 0:
        # Resize frame of video to the specified size for faster face recognition processing
        small_frame = cv2.resize(frame, (0, 0), fx=scaling_frame, fy=scaling_frame)

        # Convert the image from BGR color (OpenCV) to RGB color (face_recognition)
        rgb_small_frame = np.ascontiguousarray(small_frame[:, :, ::-1])

        # Use the HOG-based model (faster for CPUs) to find all the faces and encodings
        face_locations = face_recognition.face_locations(rgb_small_frame, model="hog")  # Using HOG for CPU
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            # Calculate the face distance to known faces and find the best match
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            matches = face_distances <= 0.6  # Use a distance threshold for face comparison

            name = "Unknown"
            if matches[best_match_index]:
                name = known_face_names[best_match_index]

                # Track the time when the face was first detected
                current_time = time.time()
                if name not in face_detection_time:
                    face_detection_time[name] = current_time

                # Check if the face has been detected for the required time
                if current_time - face_detection_time[name] >= DETECTION_TIME_REQUIRED:
                    # Check if the name was spoken more than the SPEAK_INTERVAL ago
                    if name not in last_spoken_time or (current_time - last_spoken_time[name]) > SPEAK_INTERVAL:
                        # Speak the name in a separate thread
                        threading.Thread(target=speak_name, args=(name,)).start()

                        # Update the last spoken time
                        last_spoken_time[name] = current_time

            face_names.append(name)

        # Reset the detection time for faces not in the current frame
        for name in list(face_detection_time.keys()):
            if name not in face_names:
                del face_detection_time[name]

    frame_count += 1  # Increment the frame count

    # Display the results
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        # Scale back up face locations since the frame was resized
        top = int(top * going_back_frame)
        right = int(right * going_back_frame)
        bottom = int(bottom * going_back_frame)
        left = int(left * going_back_frame)

        # Draw a box around the face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        # Draw a label with a name below the face
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

    # Display the resulting image
    cv2.imshow('Video', frame)

    # Hit 'q' on the keyboard to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release handle to the webcam
video_capture.release()
cv2.destroyAllWindows()


