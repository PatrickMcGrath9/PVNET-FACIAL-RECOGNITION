# import json
# import os
# import cv2
# import numpy as np
# import face_recognition
# from databasemanager import DatabaseManager

# class FaceManager:
#     class Face:
#         def __init__(self, name, location):
#             self.name = name
#             self.location = location

#     class params:
#         FRAME_SCALE_FACTOR     = 0.75
#         IDS_ENCODINGS_PATH     = "DB/encodings.json"
#         FACE_IDS_PATH          = "DB/faceids.json"
#         UNKNOWN_ENCODINGS_PATH = "DB/unknown_encodings.json"
#         AUDIT_FACES_PATH       = "DB/audit"
#         ENCODING_MATCH_TOLERANCE = 0.6
#         ENCODING_JITTERS         = 1

#     def __init__(self):
#         # load known people
#         self.id_to_encoding = {}
#         if os.path.exists(self.params.IDS_ENCODINGS_PATH):
#             with open(self.params.IDS_ENCODINGS_PATH, "r") as f:
#                 data = json.load(f)
#                 for pid, enc_list in data.items():
#                     self.id_to_encoding[pid] = [np.array(e) for e in enc_list]

#         self.id_to_label = {}
#         if os.path.exists(self.params.FACE_IDS_PATH):
#             with open(self.params.FACE_IDS_PATH, "r") as f:
#                 self.id_to_label = json.load(f)

#         # load unknown groups
#         self.unknown_encodings = {}   # { group_id: [enc1, enc2, ...] }
#         if os.path.exists(self.params.UNKNOWN_ENCODINGS_PATH):
#             with open(self.params.UNKNOWN_ENCODINGS_PATH, "r") as f:
#                 data = json.load(f)
#                 for gid, enc_list in data.items():
#                     self.unknown_encodings[int(gid)] = [np.array(e) for e in enc_list]

#         # helper to save audits & JSON
#         self.database_manager = DatabaseManager(self.params.AUDIT_FACES_PATH)

#     def _save_unknown_encodings(self):
#         """Write current unknown_encodings dict back to JSON."""
#         serial = {str(gid): [e.tolist() for e in encs]
#                   for gid, encs in self.unknown_encodings.items()}
#         with open(self.params.UNKNOWN_ENCODINGS_PATH, "w") as f:
#             json.dump(serial, f, indent=2)

#     def find_faces(self, frame):
#         """Detect & classify each face in the frame."""
#         s = self.params.FRAME_SCALE_FACTOR
#         small = cv2.resize(frame, (0, 0), fx=s, fy=s)
#         rgb   = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
#         faces = []
#         for (top, right, bottom, left) in face_recognition.face_locations(rgb):
#             loc_scaled = (left, top, right-left, bottom-top)
#             faces.append(self._identify_fallback(frame, rgb, loc_scaled))
#         return faces

#     def _identify_fallback(self, orig_frame, scaled_rgb, loc_scaled):
#         x_s, y_s, w_s, h_s = loc_scaled
#         s = self.params.FRAME_SCALE_FACTOR
#         # back to original coords
#         x, y, w, h = int(x_s/s), int(y_s/s), int(w_s/s), int(h_s/s)
#         loc_orig = (x, y, w, h)

#         # compute encoding
#         enc = face_recognition.face_encodings(
#             scaled_rgb, [(y_s, x_s+w_s, y_s+h_s, x_s)],
#             num_jitters=self.params.ENCODING_JITTERS
#         )[0]

#         # 1) check against known faces
#         for pid, enc_list in self.id_to_encoding.items():
#             if face_recognition.compare_faces(enc_list, enc, 
#                                               tolerance=self.params.ENCODING_MATCH_TOLERANCE)[0]:
#                 return FaceManager.Face(self.id_to_label[pid], loc_orig)

#         # 2) check against each existing unknown group
#         for gid, enc_list in self.unknown_encodings.items():
#             if face_recognition.compare_faces(enc_list, enc, 
#                                               tolerance=self.params.ENCODING_MATCH_TOLERANCE)[0]:
#                 # add this new encoding to the group
#                 self.unknown_encodings[gid].append(enc)
#                 self._save_unknown_encodings()
#                 return FaceManager.Face("UNKNOWN", loc_orig)

#         # 3) brand-new unknown: make a new group
#         new_gid = max(self.unknown_encodings.keys(), default=-1) + 1
#         self.unknown_encodings[new_gid] = [enc]
#         # persist JSON & save crop
#         self._save_unknown_encodings()
#         crop = orig_frame[y:y+h, x:x+w]
#         self.database_manager.save_unknown_face(crop, new_gid)
#         return FaceManager.Face("UNKNOWN", loc_orig)


# import json
# import os
# import cv2
# import numpy as np
# import face_recognition
# from databasemanager import DatabaseManager

# class FaceManager:
#     class Face:
#         def __init__(self, name, location):
#             self.name = name
#             self.location = location

#     class params:
#         FRAME_SCALE_FACTOR = 0.75
#         KNOWN_FACES_DIR = "DB/known"
#         KNOWN_ENCODINGS_PATH = "DB/known_encodings.json"
#         FACE_IDS_PATH = "DB/faceids.json"
#         UNKNOWN_ENCODINGS_PATH = "DB/unknown_encodings.json"
#         AUDIT_FACES_PATH = "DB/audit"
#         ENCODING_MATCH_TOLERANCE = 0.6
#         ENCODING_JITTERS = 1

#     def __init__(self):
#         self.id_to_encoding = {}
#         self.id_to_label = {}

#         # Ensure known and audit folders exist
#         self.database_manager = DatabaseManager(
#             self.params.AUDIT_FACES_PATH,
#             self.params.KNOWN_FACES_DIR
#         )

#         # Load known encodings and names
#         self._load_known_faces()

#         # Load unknown face groups
#         self.unknown_encodings = {}
#         if os.path.exists(self.params.UNKNOWN_ENCODINGS_PATH):
#             with open(self.params.UNKNOWN_ENCODINGS_PATH, "r") as f:
#                 data = json.load(f)
#                 for gid, enc_list in data.items():
#                     self.unknown_encodings[int(gid)] = [np.array(e) for e in enc_list]

#     def _load_known_faces(self):
#         # Load known encodings
#         if os.path.exists(self.params.KNOWN_ENCODINGS_PATH):
#             with open(self.params.KNOWN_ENCODINGS_PATH, "r") as f:
#                 data = json.load(f)
#                 for pid, enc_list in data.items():
#                     self.id_to_encoding[pid] = [np.array(e) for e in enc_list]

#         # Load or generate ID-to-name mapping
#         if os.path.exists(self.params.FACE_IDS_PATH):
#             with open(self.params.FACE_IDS_PATH, "r") as f:
#                 self.id_to_label = json.load(f)
#         else:
#             for file in os.listdir(self.params.KNOWN_FACES_DIR):
#                 if not file.lower().endswith(('.jpg', '.png', '.jpeg')):
#                     continue
#                 try:
#                     pid, name = os.path.splitext(file)[0].split('_', 1)
#                     self.id_to_label[pid] = name
#                 except ValueError:
#                     continue
#             self._save_id_labels()

#     def _save_known_encodings(self):
#         serial = {
#             pid: [e.tolist() for e in enc_list]
#             for pid, enc_list in self.id_to_encoding.items()
#         }
#         with open(self.params.KNOWN_ENCODINGS_PATH, "w") as f:
#             json.dump(serial, f, indent=2)

#     def _save_id_labels(self):
#         with open(self.params.FACE_IDS_PATH, "w") as f:
#             json.dump(self.id_to_label, f, indent=2)

#     def _save_unknown_encodings(self):
#         serial = {
#             str(gid): [e.tolist() for e in enc_list]
#             for gid, enc_list in self.unknown_encodings.items()
#         }
#         with open(self.params.UNKNOWN_ENCODINGS_PATH, "w") as f:
#             json.dump(serial, f, indent=2)

#     def find_faces(self, frame):
#         s = self.params.FRAME_SCALE_FACTOR
#         small = cv2.resize(frame, (0, 0), fx=s, fy=s)
#         rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
#         faces = []

#         for (top, right, bottom, left) in face_recognition.face_locations(rgb):
#             loc_scaled = (left, top, right-left, bottom-top)
#             face = self._identify_fallback(frame, rgb, loc_scaled)
#             faces.append(face)

#         return faces

#     def _identify_fallback(self, orig_frame, scaled_rgb, loc_scaled):
#         x_s, y_s, w_s, h_s = loc_scaled
#         s = self.params.FRAME_SCALE_FACTOR
#         x, y, w, h = int(x_s/s), int(y_s/s), int(w_s/s), int(h_s/s)
#         loc_orig = (x, y, w, h)

#         encodings = face_recognition.face_encodings(
#             scaled_rgb,
#             [(y_s, x_s + w_s, y_s + h_s, x_s)],
#             num_jitters=self.params.ENCODING_JITTERS
#         )

#         if not encodings:
#             return FaceManager.Face("UNKNOWN", loc_orig)

#         enc = encodings[0]

#         # Step 1: Check known
#         for pid, enc_list in self.id_to_encoding.items():
#             matches = face_recognition.compare_faces(enc_list, enc,
#                                                      tolerance=self.params.ENCODING_MATCH_TOLERANCE)
#             if True in matches:
#                 self.id_to_encoding[pid].append(enc)
#                 self._save_known_encodings()
#                 return FaceManager.Face(self.id_to_label[pid], loc_orig)

#         # Step 2: Check unknown groups
#         for gid, enc_list in self.unknown_encodings.items():
#             matches = face_recognition.compare_faces(enc_list, enc,
#                                                      tolerance=self.params.ENCODING_MATCH_TOLERANCE)
#             if True in matches:
#                 self.unknown_encodings[gid].append(enc)
#                 self._save_unknown_encodings()
#                 return FaceManager.Face("UNKNOWN", loc_orig)

#         # Step 3: New unknown group
#         new_gid = max(self.unknown_encodings.keys(), default=-1) + 1
#         self.unknown_encodings[new_gid] = [enc]
#         self._save_unknown_encodings()
#         crop = orig_frame[y:y+h, x:x+w]
#         self.database_manager.save_unknown_face(crop, new_gid)
#         return FaceManager.Face("UNKNOWN", loc_orig)
# import json
# import os
# import cv2
# import numpy as np
# import face_recognition
# from databasemanager import DatabaseManager

# class FaceManager:
#     class Face:
#         def __init__(self, name, location):
#             self.name = name
#             self.location = location

#     class params:
#         FRAME_SCALE_FACTOR = 0.75
#         KNOWN_FACES_DIR = "DB/known"
#         KNOWN_ENCODINGS_PATH = "DB/known_encodings.json"
#         UNKNOWN_ENCODINGS_PATH = "DB/unknown_encodings.json"
#         AUDIT_FACES_PATH = "DB/audit"
#         ENCODING_MATCH_TOLERANCE = 0.6
#         ENCODING_JITTERS = 1

#     def __init__(self):
#         self.id_to_encoding = {}
#         self.id_to_label = {}

#         # Create known and audit directories if missing
#         self.database_manager = DatabaseManager(
#             self.params.AUDIT_FACES_PATH,
#             self.params.KNOWN_FACES_DIR
#         )

#         # Load known faces and unknown groups
#         self._load_known_faces()
#         self._load_unknown_faces()

#     def _load_known_faces(self):
#         # Load known encodings
#         if os.path.exists(self.params.KNOWN_ENCODINGS_PATH):
#             with open(self.params.KNOWN_ENCODINGS_PATH, "r") as f:
#                 data = json.load(f)
#                 for pid, enc_list in data.items():
#                     self.id_to_encoding[pid] = [np.array(e) for e in enc_list]

#         # Extract IDs and names from filenames
#         for file in os.listdir(self.params.KNOWN_FACES_DIR):
#             if not file.lower().endswith(('.jpg', '.png', '.jpeg')):
#                 continue
#             try:
#                 pid, name = os.path.splitext(file)[0].split('_', 1)
#                 self.id_to_label[pid] = name
#             except ValueError:
#                 continue

#     def _load_unknown_faces(self):
#         self.unknown_encodings = {}
#         if os.path.exists(self.params.UNKNOWN_ENCODINGS_PATH):
#             with open(self.params.UNKNOWN_ENCODINGS_PATH, "r") as f:
#                 data = json.load(f)
#                 for gid, enc_list in data.items():
#                     self.unknown_encodings[int(gid)] = [np.array(e) for e in enc_list]

#     def _save_known_encodings(self):
#         serial = {
#             pid: [e.tolist() for e in enc_list]
#             for pid, enc_list in self.id_to_encoding.items()
#         }
#         with open(self.params.KNOWN_ENCODINGS_PATH, "w") as f:
#             json.dump(serial, f, indent=2)

#     def _save_unknown_encodings(self):
#         serial = {
#             str(gid): [e.tolist() for e in enc_list]
#             for gid, enc_list in self.unknown_encodings.items()
#         }
#         with open(self.params.UNKNOWN_ENCODINGS_PATH, "w") as f:
#             json.dump(serial, f, indent=2)

#     def find_faces(self, frame):
#         s = self.params.FRAME_SCALE_FACTOR
#         small = cv2.resize(frame, (0, 0), fx=s, fy=s)
#         rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
#         faces = []

#         for (top, right, bottom, left) in face_recognition.face_locations(rgb):
#             loc_scaled = (left, top, right-left, bottom-top)
#             face = self._identify_fallback(frame, rgb, loc_scaled)
#             faces.append(face)

#         return faces

#     def _identify_fallback(self, orig_frame, scaled_rgb, loc_scaled):
#         x_s, y_s, w_s, h_s = loc_scaled
#         s = self.params.FRAME_SCALE_FACTOR
#         x, y, w, h = int(x_s/s), int(y_s/s), int(w_s/s), int(h_s/s)
#         loc_orig = (x, y, w, h)

#         encodings = face_recognition.face_encodings(
#             scaled_rgb,
#             [(y_s, x_s + w_s, y_s + h_s, x_s)],
#             num_jitters=self.params.ENCODING_JITTERS
#         )

#         if not encodings:
#             return FaceManager.Face("UNKNOWN", loc_orig)

#         enc = encodings[0]

#         # Step 1: Check known
#         for pid, enc_list in self.id_to_encoding.items():
#             matches = face_recognition.compare_faces(enc_list, enc,
#                                                      tolerance=self.params.ENCODING_MATCH_TOLERANCE)
#             if True in matches:
#                 self.id_to_encoding[pid].append(enc)
#                 self._save_known_encodings()
#                 return FaceManager.Face(self.id_to_label.get(pid, "UNKNOWN"), loc_orig)

#         # Step 2: Check unknown groups
#         for gid, enc_list in self.unknown_encodings.items():
#             matches = face_recognition.compare_faces(enc_list, enc,
#                                                      tolerance=self.params.ENCODING_MATCH_TOLERANCE)
#             if True in matches:
#                 self.unknown_encodings[gid].append(enc)
#                 self._save_unknown_encodings()
#                 return FaceManager.Face("UNKNOWN", loc_orig)

#         # Step 3: New unknown group
#         new_gid = max(self.unknown_encodings.keys(), default=-1) + 1
#         self.unknown_encodings[new_gid] = [enc]
#         self._save_unknown_encodings()
#         crop = orig_frame[y:y+h, x:x+w]
#         self.database_manager.save_unknown_face(crop, new_gid)
#         return FaceManager.Face("UNKNOWN", loc_orig)


import json
import os
import cv2
import numpy as np
import face_recognition
from databasemanager import DatabaseManager

class FaceManager:
    class Face:
        def __init__(self, name, location):
            self.name = name
            self.location = location

    class params:
        FRAME_SCALE_FACTOR = 0.75
        KNOWN_FACES_DIR = "DB/known"
        KNOWN_ENCODINGS_PATH = "DB/known_encodings.json"
        UNKNOWN_ENCODINGS_PATH = "DB/unknown_encodings.json"
        AUDIT_FACES_PATH = "DB/audit"
        ENCODING_MATCH_TOLERANCE = 0.6
        ENCODING_JITTERS = 1

    def __init__(self):
        self.id_to_encoding = {}
        self.id_to_label = {}

        # Create known and audit directories if missing
        self.database_manager = DatabaseManager(
            self.params.AUDIT_FACES_PATH,
            self.params.KNOWN_FACES_DIR
        )

        # Load known faces and unknown groups
        self._load_known_faces()
        self._load_unknown_faces()

    def _load_known_faces(self):
        # Initialize known encodings dictionary
        self.id_to_encoding = {}
        self.id_to_label = {}

        # Create known_encodings.json with an empty dict if it doesn't exist
        if not os.path.exists(self.params.KNOWN_ENCODINGS_PATH):
            with open(self.params.KNOWN_ENCODINGS_PATH, "w") as f:
                json.dump({}, f, indent=2)
        else:
            # Load known encodings if file exists
            with open(self.params.KNOWN_ENCODINGS_PATH, "r") as f:
                data = json.load(f)
                for pid, enc_list in data.items():
                    self.id_to_encoding[pid] = [np.array(e) for e in enc_list]

        # Extract IDs and names from filenames
        for file in os.listdir(self.params.KNOWN_FACES_DIR):
            if not file.lower().endswith(('.jpg', '.png', '.jpeg')):
                continue
            try:
                pid, name = os.path.splitext(file)[0].split('_', 1)
                self.id_to_label[pid] = name
            except ValueError:
                continue

    def _load_unknown_faces(self):
        self.unknown_encodings = {}
        if os.path.exists(self.params.UNKNOWN_ENCODINGS_PATH):
            with open(self.params.UNKNOWN_ENCODINGS_PATH, "r") as f:
                data = json.load(f)
                for gid, enc_list in data.items():
                    self.unknown_encodings[int(gid)] = [np.array(e) for e in enc_list]

    def _save_known_encodings(self):
        serial = {
            pid: [e.tolist() for e in enc_list]
            for pid, enc_list in self.id_to_encoding.items()
        }
        with open(self.params.KNOWN_ENCODINGS_PATH, "w") as f:
            json.dump(serial, f, indent=2)

    def _save_unknown_encodings(self):
        serial = {
            str(gid): [e.tolist() for e in enc_list]
            for gid, enc_list in self.unknown_encodings.items()
        }
        with open(self.params.UNKNOWN_ENCODINGS_PATH, "w") as f:
            json.dump(serial, f, indent=2)

    def find_faces(self, frame):
        s = self.params.FRAME_SCALE_FACTOR
        small = cv2.resize(frame, (0, 0), fx=s, fy=s)
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        faces = []

        for (top, right, bottom, left) in face_recognition.face_locations(rgb):
            loc_scaled = (left, top, right-left, bottom-top)
            face = self._identify_fallback(frame, rgb, loc_scaled)
            faces.append(face)

        return faces

    def _identify_fallback(self, orig_frame, scaled_rgb, loc_scaled):
        x_s, y_s, w_s, h_s = loc_scaled
        s = self.params.FRAME_SCALE_FACTOR
        x, y, w, h = int(x_s/s), int(y_s/s), int(w_s/s), int(h_s/s)
        loc_orig = (x, y, w, h)

        encodings = face_recognition.face_encodings(
            scaled_rgb,
            [(y_s, x_s + w_s, y_s + h_s, x_s)],
            num_jitters=self.params.ENCODING_JITTERS
        )

        if not encodings:
            return FaceManager.Face("UNKNOWN", loc_orig)

        enc = encodings[0]

        # Step 1: Check known
        for pid, enc_list in self.id_to_encoding.items():
            matches = face_recognition.compare_faces(enc_list, enc,
                                                     tolerance=self.params.ENCODING_MATCH_TOLERANCE)
            if True in matches:
                self.id_to_encoding[pid].append(enc)
                self._save_known_encodings()
                return FaceManager.Face(self.id_to_label.get(pid, "UNKNOWN"), loc_orig)

        # Step 2: Check unknown groups
        for gid, enc_list in self.unknown_encodings.items():
            matches = face_recognition.compare_faces(enc_list, enc,
                                                     tolerance=self.params.ENCODING_MATCH_TOLERANCE)
            if True in matches:
                self.unknown_encodings[gid].append(enc)
                self._save_unknown_encodings()
                return FaceManager.Face("UNKNOWN", loc_orig)

        # Step 3: New unknown group
        new_gid = max(self.unknown_encodings.keys(), default=-1) + 1
        self.unknown_encodings[new_gid] = [enc]
        self._save_unknown_encodings()
        crop = orig_frame[y:y+h, x:x+w]
        self.database_manager.save_unknown_face(crop, new_gid)
        return FaceManager.Face("UNKNOWN", loc_orig)