import json #for serializing objects
import gzip #for compression
import cv2 #for facial recognition
import face_recognition #for facial recognition and encodings
import os #for finding files
from databasemanager import DatabaseManager

#TODO Web UI for Audit

class FaceManager: #TODO make singleton
    class Face:
        def __init__(self, p_name, p_location):
            self.name = p_name
            self.location = p_location

    class params:
        FRAME_SCALE_FACTOR = 0.75  # Scale down for faster processing
        IDS_ENCODINGS_PATH = "db/encodings"
        FACE_IDS_PATH = "DB/faceids"
        AUDIT_FACES_PATH = "DB/audit"
        CONFIDENCE_TOLERANCE = 50 #how confident should match be to accept 
        ENCODING_NUM_JITTERS = 1 #increase to resample more times and thus make encodings more accurate, runs slower though
        ENCODING_MATCH_TOLERANCE = 0.6 #how far apart should encodings be to qualify as matches

    id_to_encoding = {} #{ID : encoding}
    id_to_label = {} # {ID : label}
    faces_to_audit = {} # {ID : image to audit}

    def __init__(self):
        # Load known encodings and labels
        if os.path.exists(self.params.IDS_ENCODINGS_PATH):
            with open(self.params.IDS_ENCODINGS_PATH, "rt") as f:
                self.id_to_encoding = json.load(f)  # {ID: [encoding_list]}
                # Convert lists back to numpy arrays
                for id in self.id_to_encoding:
                    self.id_to_encoding[id] = [np.array(enc) for enc in self.id_to_encoding[id]]
        else:
            self.id_to_encoding = {}

        if os.path.exists(self.params.FACE_IDS_PATH):
            with open(self.params.FACE_IDS_PATH, "rt") as f:
                self.id_to_label = json.load(f)  # {ID: label}
        else:
            self.id_to_label = {}

        # Initialize unknown faces tracking
        self.unknown_encodings = []  # List of lists, each containing encodings for an unknown group
        self.faces_to_audit = {}  # Optional: keep for compatibility, but not used for saving here

        # Initialize DatabaseManager
        self.database_manager = DatabaseManager()

    def __del__(self):
        #save ID to Label DB
        if len(self.id_to_encoding) > 0:
            with open(self.params.IDS_ENCODINGS_PATH, "wt") as f:
                json.dump(self.id_to_encoding, f)
        else:
            if os.path.exists(self.params.IDS_ENCODINGS_PATH):  
                os.remove(self.params.IDS_ENCODINGS_PATH)

        #save ID to Label DB
        if len(self.id_to_label) > 0:
            with open(self.params.FACE_IDS_PATH, "wt") as f:
                json.dump(self.id_to_label, f)
        else:
            if os.path.exists(self.params.FACE_IDS_PATH):
                os.remove(self.params.FACE_IDS_PATH)

        #save ID to Label DB
        if len(self.faces_to_audit) > 0:
            with open(self.params.AUDIT_FACES_PATH, "wt") as f:
                json.dump(self.faces_to_audit, f)
        else:
            if os.path.exists(self.params.AUDIT_FACES_PATH):
                os.remove(self.params.AUDIT_FACES_PATH)

    def find_faces(self, frame):
        """Detect faces in the frame and return Face objects."""
        scaled_frame = cv2.resize(frame, (0, 0), fx=self.params.FRAME_SCALE_FACTOR, fy=self.params.FRAME_SCALE_FACTOR)
        frame_rgb = cv2.cvtColor(scaled_frame, cv2.COLOR_BGR2RGB)
        faces = []
        for loc in face_recognition.face_locations(frame_rgb):
            (t, r, b, l) = loc
            loc_scaled = (l, t, r - l, b - t)  # x, y, w, h in scaled coordinates
            face = self.identify_face_fallback(frame, frame_rgb, loc_scaled)
            faces.append(face)
        return faces
        
    def identify_face(self, frame) -> Face:
        pass
        # face_fisher_recognizer = cv2.face.FisherFaceRecognizer_create() #load facial recognition model
        # label, confidence = face_fisher_recognizer.predict(?) #who is this face? how confident are you
        # if confidence >= FaceManager.params.CONFIDENCE_TOLERANCE: #if confident enough
        #    return FaceManager.Face(label, ?)

    def identify_face_fallback(self, original_frame, scaled_frame_rgb, location_scaled):
        """Identify a face, grouping unknowns and saving their images."""
        (x_scaled, y_scaled, w_scaled, h_scaled) = location_scaled
        s = self.params.FRAME_SCALE_FACTOR
        # Convert to original coordinates
        x = int(x_scaled / s)
        y = int(y_scaled / s)
        w = int(w_scaled / s)
        h = int(h_scaled / s)
        location_original = (x, y, w, h)

        # Compute encoding from scaled frame
        encoding = face_recognition.face_encodings(scaled_frame_rgb, 
            [(y_scaled, x_scaled + w_scaled, y_scaled + h_scaled, x_scaled)])[0]

        # Check known faces
        for id in self.id_to_label:
            known_encs = self.id_to_encoding.get(id, [])
            if any(face_recognition.compare_faces(known_encs, encoding, 
                tolerance=self.params.ENCODING_MATCH_TOLERANCE)):
                return FaceManager.Face(self.id_to_label[id], location_original)

        # Check unknown faces
        for i, unknown_encs in enumerate(self.unknown_encodings):
            if any(face_recognition.compare_faces(unknown_encs, encoding, 
                tolerance=self.params.ENCODING_MATCH_TOLERANCE)):
                # Add to existing unknown group
                self.unknown_encodings[i].append(encoding)
                return FaceManager.Face("UNKNOWN", location_original)

        # New unknown face: create a group and save the image
        self.unknown_encodings.append([encoding])
        group_id = len(self.unknown_encodings) - 1
        face_image = original_frame[y:y+h, x:x+w]  # Extract from original BGR frame
        self.database_manager.save_unknown_face(face_image, group_id)
        return FaceManager.Face("UNKNOWN", location_original)