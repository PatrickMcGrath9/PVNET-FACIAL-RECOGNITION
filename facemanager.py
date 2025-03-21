import json #for serializing objects
import gzip #for compression
import cv2 #for facial recognition
import face_recognition #for facial recognition and encodings
import os #for finding files

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
        #load Encoding to ID DB
        if os.path.exists(self.params.IDS_ENCODINGS_PATH):
            with open(self.params.IDS_ENCODINGS_PATH, "rt") as f:
                self.id_to_label = json.load(f)

        #load ID to Label DB
        if os.path.exists(self.params.FACE_IDS_PATH):
            with open(self.params.FACE_IDS_PATH, "rt") as f:
                self.id_to_label = json.load(f)

        #load faces to audit
        if os.path.exists(self.params.AUDIT_FACES_PATH):
            with open(self.params.AUDIT_FACES_PATH, "rt") as f:
                self.faces_to_audit = json.load(f)

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

    def find_faces(self, frame) -> [Face]:
        scaled_frame = cv2.resize(frame, (0,0), fx=self.params.FRAME_SCALE_FACTOR, fy=self.params.FRAME_SCALE_FACTOR)#automatically scale down image by (fx, fy)
        #TODO make async so that faces are sent as they are identified. Only useful for multiple faces
        faces = []
        #TODO more complicated model first that can detect many angles

        #frontal only face_recognition as fallback
        frame_rgb = cv2.cvtColor(scaled_frame, cv2.COLOR_BGR2RGB)
        for loc in face_recognition.face_locations(frame_rgb):
            (t,r,b,l) = loc
            loc = (l, t, r-l, b-t) #x,y,w,h
            faces.append(self.identify_face_fallback(frame_rgb, loc))
        return faces
        
    def identify_face(self, frame) -> Face:
        pass
        # face_fisher_recognizer = cv2.face.FisherFaceRecognizer_create() #load facial recognition model
        # label, confidence = face_fisher_recognizer.predict(?) #who is this face? how confident are you
        # if confidence >= FaceManager.params.CONFIDENCE_TOLERANCE: #if confident enough
        #    return FaceManager.Face(label, ?)

    def identify_face_fallback(self, frame_rgb, location) -> Face:
        (x,y,w,h) = location
        x = int(x / self.params.FRAME_SCALE_FACTOR)
        y = int(y / self.params.FRAME_SCALE_FACTOR)
        w = int(w / self.params.FRAME_SCALE_FACTOR)
        h = int(h / self.params.FRAME_SCALE_FACTOR)
        encoding = face_recognition.face_encodings(frame_rgb, [location])[0]
        #TODO remove below. not likely to have exact matches?
        # if hash(str(encoding)) in self.id_to_label.keys():#convert encoding to ID, look for exact match
        #     # add new image to train model on
        #     return FaceManager.Face(self.id_to_label[hash(str(encoding))], (x,y,w,h))
        
        #TODO compare encodings for close match
        #TODO at beginning of facemanager: go through entire database and store encoding of each face. Attempt to compare distance of current embedding and stored ones
        for i,id in enumerate(self.id_to_encoding.keys()): #for every id
            if True in face_recognition.compare_faces(self.id_to_encoding[id], encoding, self.params.ENCODING_MATCH_TOLERANCE): #if one of the encodings match close enough
                return FaceManager.Face(self.id_to_label[id], (x,y,w,h))

        if str(encoding) in self.faces_to_audit.keys(): #exact match found pending audit
            return FaceManager.Face(hash(str(encoding)), (x,y,w,h))
        #TODO compare encodings for close match pending audit
        else:
            self.faces_to_audit[str(encoding)] = frame_rgb[y:y+h, x:x+w] #add photo for auditing
            return FaceManager.Face("UNKNOWN", (x,y,w,h))