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
#         # Initialize known encodings dictionary
#         self.id_to_encoding = {}
#         self.id_to_label = {}

#         # Create known_encodings.json with an empty dict if it doesn't exist
#         if not os.path.exists(self.params.KNOWN_ENCODINGS_PATH):
#             with open(self.params.KNOWN_ENCODINGS_PATH, "w") as f:
#                 json.dump({}, f, indent=2)
#         else:
#             # Load known encodings if file exists
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
#         KNOWN_NAMES_PATH = "DB/known_names.json"
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

#         # Load known names and encodings, plus unknown faces
#         self._load_known_names()
#         self._load_known_encodings()
#         self._load_unknown_faces()

#     def _load_known_names(self):
#         if not os.path.exists(self.params.KNOWN_NAMES_PATH):
#             with open(self.params.KNOWN_NAMES_PATH, "w") as f:
#                 json.dump({}, f, indent=2)
#             self.id_to_label = {}
#         else:
#             with open(self.params.KNOWN_NAMES_PATH, "r") as f:
#                 self.id_to_label = json.load(f)

#     def _load_known_encodings(self):
#         if not os.path.exists(self.params.KNOWN_ENCODINGS_PATH):
#             with open(self.params.KNOWN_ENCODINGS_PATH, "w") as f:
#                 json.dump({}, f, indent=2)
#             self.id_to_encoding = {}
#         else:
#             with open(self.params.KNOWN_ENCODINGS_PATH, "r") as f:
#                 data = json.load(f)
#                 self.id_to_encoding = {pid: [np.array(enc) for enc in enc_list]
#                                        for pid, enc_list in data.items()}

#     def _load_unknown_faces(self):
#         self.unknown_encodings = {}
#         if os.path.exists(self.params.UNKNOWN_ENCODINGS_PATH):
#             with open(self.params.UNKNOWN_ENCODINGS_PATH, "r") as f:
#                 data = json.load(f)
#                 for gid, enc_list in data.items():
#                     self.unknown_encodings[int(gid)] = [np.array(e) for e in enc_list]

#     def _save_known_names(self):
#         with open(self.params.KNOWN_NAMES_PATH, "w") as f:
#             json.dump(self.id_to_label, f, indent=2)

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
#             loc_scaled = (left, top, right - left, bottom - top)
#             face = self._identify_fallback(frame, rgb, loc_scaled)
#             faces.append(face)

#         return faces

#     def _identify_fallback(self, orig_frame, scaled_rgb, loc_scaled):
#         x_s, y_s, w_s, h_s = loc_scaled
#         s = self.params.FRAME_SCALE_FACTOR
#         x, y, w, h = int(x_s / s), int(y_s / s), int(w_s / s), int(h_s / s)
#         loc_orig = (x, y, w, h)

#         encodings = face_recognition.face_encodings(
#             scaled_rgb,
#             [(y_s, x_s + w_s, y_s + h_s, x_s)],
#             num_jitters=self.params.ENCODING_JITTERS
#         )

#         if not encodings:
#             return FaceManager.Face("UNKNOWN", loc_orig)

#         enc = encodings[0]

#         # Step 1: Check known encodings
#         for pid, enc_list in self.id_to_encoding.items():
#             matches = face_recognition.compare_faces(enc_list, enc,
#                                                      tolerance=self.params.ENCODING_MATCH_TOLERANCE)
#             if True in matches:
#                 # Add new encoding to known encodings for that ID
#                 self.id_to_encoding[pid].append(enc)
#                 self._save_known_encodings()
#                 # Return known name if available, else UNKNOWN
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

#         crop = orig_frame[y:y + h, x:x + w]
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
#         KNOWN_NAMES_PATH = "DB/known_names.json"
#         KNOWN_ENCODINGS_PATH = "DB/known_encodings.json"
#         UNKNOWN_ENCODINGS_PATH = "DB/unknown_encodings.json"
#         AUDIT_FACES_PATH = "DB/audit"
#         ENCODING_MATCH_TOLERANCE = 0.6
#         ENCODING_JITTERS = 1

#     def __init__(self):
#         self.id_to_encoding = {}
#         self.id_to_label = {}

#         self.database_manager = DatabaseManager(
#             self.params.AUDIT_FACES_PATH,
#             self.params.KNOWN_FACES_DIR
#         )

#         # Load names and encodings from JSON files
#         self._load_known_names()
#         self._load_known_encodings()
#         self._load_unknown_faces()

#         # Update known names json with any new files in known folder
#         self._update_known_names_from_files()

#     def _load_known_names(self):
#         if not os.path.exists(self.params.KNOWN_NAMES_PATH):
#             with open(self.params.KNOWN_NAMES_PATH, "w") as f:
#                 json.dump({}, f, indent=2)
#             self.id_to_label = {}
#         else:
#             with open(self.params.KNOWN_NAMES_PATH, "r") as f:
#                 self.id_to_label = json.load(f)

#     def _load_known_encodings(self):
#         if not os.path.exists(self.params.KNOWN_ENCODINGS_PATH):
#             with open(self.params.KNOWN_ENCODINGS_PATH, "w") as f:
#                 json.dump({}, f, indent=2)
#             self.id_to_encoding = {}
#         else:
#             with open(self.params.KNOWN_ENCODINGS_PATH, "r") as f:
#                 data = json.load(f)
#                 self.id_to_encoding = {pid: [np.array(enc) for enc in enc_list]
#                                        for pid, enc_list in data.items()}

#     def _load_unknown_faces(self):
#         self.unknown_encodings = {}
#         if os.path.exists(self.params.UNKNOWN_ENCODINGS_PATH):
#             with open(self.params.UNKNOWN_ENCODINGS_PATH, "r") as f:
#                 data = json.load(f)
#                 for gid, enc_list in data.items():
#                     self.unknown_encodings[int(gid)] = [np.array(e) for e in enc_list]

#     def _save_known_names(self):
#         with open(self.params.KNOWN_NAMES_PATH, "w") as f:
#             json.dump(self.id_to_label, f, indent=2)

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

#     def _update_known_names_from_files(self):
#         """
#         Scan the known faces directory for new files.
#         If the ID from a filename is not in known_names.json, add it.
#         Filename format assumed: "<ID>_<Name>.jpg" or similar.
#         """
#         updated = False
#         for filename in os.listdir(self.params.KNOWN_FACES_DIR):
#             if not filename.lower().endswith(('.jpg', '.png', '.jpeg')):
#                 continue
#             try:
#                 pid, name = os.path.splitext(filename)[0].split('_', 1)
#             except ValueError:
#                 # Filename not in expected format, skip
#                 continue
#             if pid not in self.id_to_label:
#                 self.id_to_label[pid] = name
#                 updated = True
#         if updated:
#             self._save_known_names()

#     def find_faces(self, frame):
#         s = self.params.FRAME_SCALE_FACTOR
#         small = cv2.resize(frame, (0, 0), fx=s, fy=s)
#         rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
#         faces = []

#         for (top, right, bottom, left) in face_recognition.face_locations(rgb):
#             loc_scaled = (left, top, right - left, bottom - top)
#             face = self._identify_fallback(frame, rgb, loc_scaled)
#             faces.append(face)

#         return faces

#     def _identify_fallback(self, orig_frame, scaled_rgb, loc_scaled):
#         x_s, y_s, w_s, h_s = loc_scaled
#         s = self.params.FRAME_SCALE_FACTOR
#         x, y, w, h = int(x_s / s), int(y_s / s), int(w_s / s), int(h_s / s)
#         loc_orig = (x, y, w, h)

#         encodings = face_recognition.face_encodings(
#             scaled_rgb,
#             [(y_s, x_s + w_s, y_s + h_s, x_s)],
#             num_jitters=self.params.ENCODING_JITTERS
#         )

#         if not encodings:
#             return FaceManager.Face("UNKNOWN", loc_orig)

#         enc = encodings[0]

#         # Step 1: Check known encodings
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

#         crop = orig_frame[y:y + h, x:x + w]
#         self.database_manager.save_unknown_face(crop, new_gid)

#         return FaceManager.Face("UNKNOWN", loc_orig)



import json
import os
import cv2
import shutil
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
        KNOWN_NAMES_PATH = "DB/known_names.json"
        KNOWN_ENCODINGS_PATH = "DB/known_encodings.json"
        UNKNOWN_ENCODINGS_PATH = "DB/unknown_encodings.json"
        AUDIT_FACES_PATH = "DB/audit"
        ENCODING_MATCH_TOLERANCE = 0.6
        ENCODING_JITTERS = 1

    def __init__(self):
        self.id_to_encoding = {}
        self.id_to_label = {}

        self.database_manager = DatabaseManager(
            self.params.AUDIT_FACES_PATH,
            self.params.KNOWN_FACES_DIR
        )

        self._organize_known_faces_into_folders()
        self._load_known_names()
        self._load_known_encodings()
        self._load_unknown_faces()
        self._update_known_names_from_files()

    def _organize_known_faces_into_folders(self):
        """Create folders for each UID_Name and move images into them if not already inside."""
        for file in os.listdir(self.params.KNOWN_FACES_DIR):
            full_path = os.path.join(self.params.KNOWN_FACES_DIR, file)

            if not os.path.isfile(full_path) or not file.lower().endswith(('.jpg', '.jpeg', '.png')):
                continue

            try:
                base_name = os.path.splitext(file)[0]
                uid, name = base_name.split('_', 1)
                folder_name = f"{uid}_{name}"
                person_folder = os.path.join(self.params.KNOWN_FACES_DIR, folder_name)

                # Create folder if it doesn't exist
                os.makedirs(person_folder, exist_ok=True)

                # Move file into folder if it's not already inside
                destination = os.path.join(person_folder, file)
                if os.path.abspath(full_path) != os.path.abspath(destination):
                    shutil.move(full_path, destination)

            except ValueError:
                print(f"Skipping unrecognized file format: {file}")

    def _load_known_names(self):
        if not os.path.exists(self.params.KNOWN_NAMES_PATH):
            with open(self.params.KNOWN_NAMES_PATH, "w") as f:
                json.dump({}, f, indent=2)
            self.id_to_label = {}
        else:
            with open(self.params.KNOWN_NAMES_PATH, "r") as f:
                self.id_to_label = json.load(f)

    def _load_known_encodings(self):
        if not os.path.exists(self.params.KNOWN_ENCODINGS_PATH):
            with open(self.params.KNOWN_ENCODINGS_PATH, "w") as f:
                json.dump({}, f, indent=2)
            self.id_to_encoding = {}
        else:
            with open(self.params.KNOWN_ENCODINGS_PATH, "r") as f:
                data = json.load(f)
                self.id_to_encoding = {
                    pid: [np.array(enc) for enc in enc_list]
                    for pid, enc_list in data.items()
                }

    def _load_unknown_faces(self):
        self.unknown_encodings = {}
        if os.path.exists(self.params.UNKNOWN_ENCODINGS_PATH):
            with open(self.params.UNKNOWN_ENCODINGS_PATH, "r") as f:
                data = json.load(f)
                for gid, enc_list in data.items():
                    self.unknown_encodings[int(gid)] = [np.array(e) for e in enc_list]

    def _save_known_names(self):
        with open(self.params.KNOWN_NAMES_PATH, "w") as f:
            json.dump(self.id_to_label, f, indent=2)

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

    def _update_known_names_from_files(self):
        """
        Scan the known faces directory for new files.
        If the ID from a filename is not in known_names.json, add it.
        Filename format assumed: "<ID>_<Name>.jpg" or similar.
        """
        updated = False
        for filename in os.listdir(self.params.KNOWN_FACES_DIR):
            if not filename.lower().endswith(('.jpg', '.png', '.jpeg')):
                continue
            try:
                pid, name = os.path.splitext(filename)[0].split('_', 1)
            except ValueError:
                continue
            if pid not in self.id_to_label:
                self.id_to_label[pid] = name
                updated = True
        if updated:
            self._save_known_names()

    def find_faces(self, frame):
        s = self.params.FRAME_SCALE_FACTOR
        small = cv2.resize(frame, (0, 0), fx=s, fy=s)
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        faces = []

        for (top, right, bottom, left) in face_recognition.face_locations(rgb):
            loc_scaled = (left, top, right - left, bottom - top)
            face = self._identify_fallback(frame, rgb, loc_scaled)
            faces.append(face)

        return faces

    def _identify_fallback(self, orig_frame, scaled_rgb, loc_scaled):
        x_s, y_s, w_s, h_s = loc_scaled
        s = self.params.FRAME_SCALE_FACTOR
        x, y, w, h = int(x_s / s), int(y_s / s), int(w_s / s), int(h_s / s)
        loc_orig = (x, y, w, h)

        encodings = face_recognition.face_encodings(
            scaled_rgb,
            [(y_s, x_s + w_s, y_s + h_s, x_s)],
            num_jitters=self.params.ENCODING_JITTERS
        )

        if not encodings:
            return FaceManager.Face("UNKNOWN", loc_orig)

        enc = encodings[0]

        for pid, enc_list in self.id_to_encoding.items():
            matches = face_recognition.compare_faces(enc_list, enc,
                                                     tolerance=self.params.ENCODING_MATCH_TOLERANCE)
            if True in matches:
                self.id_to_encoding[pid].append(enc)
                self._save_known_encodings()
                return FaceManager.Face(self.id_to_label.get(pid, "UNKNOWN"), loc_orig)

        for gid, enc_list in self.unknown_encodings.items():
            matches = face_recognition.compare_faces(enc_list, enc,
                                                     tolerance=self.params.ENCODING_MATCH_TOLERANCE)
            if True in matches:
                self.unknown_encodings[gid].append(enc)
                self._save_unknown_encodings()
                return FaceManager.Face("UNKNOWN", loc_orig)

        new_gid = max(self.unknown_encodings.keys(), default=-1) + 1
        self.unknown_encodings[new_gid] = [enc]
        self._save_unknown_encodings()

        crop = orig_frame[y:y + h, x:x + w]
        self.database_manager.save_unknown_face(crop, new_gid)

        return FaceManager.Face("UNKNOWN", loc_orig)
