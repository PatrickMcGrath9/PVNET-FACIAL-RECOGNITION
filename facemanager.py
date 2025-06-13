import cv2
import numpy as np
import face_recognition
import uuid

class FaceManager:
    class Face:
        def __init__(self, name, location):
            self.name = name
            self.location = location

    class params:
        FRAME_SCALE_FACTOR = 0.75
        ENCODING_MATCH_TOLERANCE = 0.45
        ENCODING_JITTERS = 1

    def __init__(self, database_manager):
        self.database_manager = database_manager
        self.faces_encodings = self.database_manager.load_all_faces()

    def find_faces(self, frame):
        scale = self.params.FRAME_SCALE_FACTOR
        small = cv2.resize(frame, (0, 0), fx=scale, fy=scale)
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        faces = []

        face_locations = face_recognition.face_locations(rgb)
        face_encodings = face_recognition.face_encodings(rgb, face_locations, num_jitters=self.params.ENCODING_JITTERS)

        for (top, right, bottom, left), enc in zip(face_locations, face_encodings):
            loc_scaled = (left, top, right - left, bottom - top)
            face = self._identify_face(frame, loc_scaled, enc)
            faces.append(face)

        return faces

    def _identify_face(self, frame, loc_scaled, enc):
        x_s, y_s, w_s, h_s = loc_scaled
        s = self.params.FRAME_SCALE_FACTOR
        x, y, w, h = int(x_s / s), int(y_s / s), int(w_s / s), int(h_s / s)
        loc_orig = (x, y, w, h)

        for folder, enc_list in self.faces_encodings.items():
            distances = face_recognition.face_distance(enc_list, enc)
            if len(distances) == 0:
                continue
            if np.min(distances) < self.params.ENCODING_MATCH_TOLERANCE:
                return FaceManager.Face("UNKNOWN", loc_orig)

        # New unknown face, ask database manager to handle
        new_uuid = str(uuid.uuid4())
        new_folder = f"!_{new_uuid}"
        crop = frame[y:y + h, x:x + w]

        self.database_manager.save_new_unknown(new_folder, crop, enc)
        self.faces_encodings[new_folder] = [enc]

        return FaceManager.Face("UNKNOWN", loc_orig)
