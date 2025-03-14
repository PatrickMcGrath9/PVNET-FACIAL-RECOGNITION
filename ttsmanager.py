# import json
# import cv2
# import face_recognition
# import os

# class FaceManager:  # TODO make singleton
#     class Face:
#         def __init__(self, encoding, name, location):
#             self.encoding = encoding
#             self.name = name
#             self.location = location

#     class params:
#         CONFIDENCE_THRESHOLD = 0.6
#         ENCODINGS_PATH = "encodings.json"

#     faces = []

#     def __init__(self):
#         self.load_encodings_from_file()

#     def load_encodings_from_file(self):
#         if os.path.exists(self.params.ENCODINGS_PATH):
#             with open(self.params.ENCODINGS_PATH, "rt") as file:
#                 self.faces = json.load(file)
#         else:
#             self.faces = []

#     def write_encodings_to_file(self):
#         with open(self.params.ENCODINGS_PATH, "wt") as file:
#             json.dump(self.faces, file)

#     async def find_faces(self, frame):
#         face_locations = face_recognition.face_locations(frame)
#         face_encodings = face_recognition.face_encodings(frame, face_locations)

#         for location, encoding in zip(face_locations, face_encodings):
#             name = await self.identify_face(encoding)
#             yield location, name

#     async def identify_face(self, encoding) -> str:
#         if not self.faces:
#             return "Unknown"

#         known_encodings = [face["encoding"] for face in self.faces]
#         known_names = [face["name"] for face in self.faces]

#         matches = face_recognition.compare_faces(known_encodings, encoding, tolerance=self.params.CONFIDENCE_THRESHOLD)
#         name = "Unknown"

#         if True in matches:
#             match_index = matches.index(True)
#             name = known_names[match_index]

#         return name

#     async def add_face(self, name, encoding):
#         self.faces.append({"name": name, "encoding": encoding})
#         self.write_encodings_to_file()

import asyncio
import json
import pyttsx3 #for the TTS engine

class TTSManager:
    file_lock = asyncio.Lock()
    tts_lock = asyncio.Lock()
    catchphrases = { #TODO load from file instead
        "Tiffany" : "borbnation will flourish.",
        "Patrick" : "slayer of bugnation.",
        "Tyler" : "ruler of the monkeys."
    }

    class params:
        SPEAK_INTERVAL = 300 # TODO ?
        UNKNOWN_SPEAK_INTERVAL = 60 # TODO ?
        DETECTION_TIME_REQUIRED = 0.3 # Time required for known faces, stops random objects being recognized as faces TODO necessary?
        UNKNOWN_DETECTION_TIME_REQUIRED = 0.75 # Time required for unknown faces, stops random objects being recongized as faces TODO necessary?
        CATCHPHRASES_DB_PATH = ""

    def __init__(self):  
        self.engine = pyttsx3.init() #intialize TTS engine
        with open("catchphrases.json", "rt") as f:
            catchphrases = json.load(f)
    
    def __del__(self): #TODO

        #write catch phrases to db file
        async with file_lock:
            with open(self.params.CATCHPHRASES_DB_PATH, "wt") as f:
                    json.dump(self.catchphrases, f)

    async def request_speak(self, speech): #TODO
        async with tts_lock:
            self.engine.say(speech)
            self.engine.runAndWait()

    async def add_catchphrase(self, name, catchphrase):
            self.catchphrases[name] = catchphrase