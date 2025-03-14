import json
import cv2
import face_recognition
import os

class FaceManager:  # TODO make singleton
    class Face:
        def __init__(self, encoding, name, location):
            self.encoding = encoding
            self.name = name
            self.location = location

    class params:
        CONFIDENCE_THRESHOLD = 0.6
        ENCODINGS_PATH = "encodings.json"

    faces = []

    def __init__(self):
        self.load_encodings_from_file()

    def load_encodings_from_file(self):
        if os.path.exists(self.params.ENCODINGS_PATH):
            with open(self.params.ENCODINGS_PATH, "rt") as file:
                self.faces = json.load(file)
        else:
            self.faces = []

    def write_encodings_to_file(self):
        with open(self.params.ENCODINGS_PATH, "wt") as file:
            json.dump(self.faces, file)

    async def find_faces(self, frame):
        face_locations = face_recognition.face_locations(frame)
        face_encodings = face_recognition.face_encodings(frame, face_locations)

        for location, encoding in zip(face_locations, face_encodings):
            name = await self.identify_face(encoding)
            yield location, name

    async def identify_face(self, encoding) -> str:
        if not self.faces:
            return "Unknown"

        known_encodings = [face["encoding"] for face in self.faces]
        known_names = [face["name"] for face in self.faces]

        matches = face_recognition.compare_faces(known_encodings, encoding, tolerance=self.params.CONFIDENCE_THRESHOLD)
        name = "Unknown"

        if True in matches:
            match_index = matches.index(True)
            name = known_names[match_index]

        return name

    async def add_face(self, name, encoding):
        self.faces.append({"name": name, "encoding": encoding})
        self.write_encodings_to_file()
