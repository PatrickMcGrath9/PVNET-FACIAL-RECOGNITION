import json #for serializing objects
import gzip #for compression
import cv2 #for facial recognition
import face_recognition #for facial recognition and encodings
import os #for finding files

class FaceManager: #TODO make singleton
    class Face:
        def __init__(self, p_name, p_location):
            self.name = p_name
            self.location = p_location

    class params:
        FACE_IDS_PATH = ""
        AUDIT_FACES_PATH = ""
        CONFIDENCE_TOLERANCE = 50 #how confident should match be to accept 
        ENCODING_NUM_JITTERS = 1 #increase to resample more times and thus make encodings more accurate, runs slower though
        ENCODING_MATCH_TOLERANCE = 0.6 #how far apart should encodings be to qualify as matches

    face_ids = {} # {encoding : label}
    faces_to_audit = {} # {encoding : image to audit}

    def __init__(self):
        #load ID to Label DB
        if os.path.exists(self.params.FACE_IDS_PATH):
            with open(self.params.FACE_IDS_PATH, "rt") as f:
                self.face_ids = json.load(f)

        #load faces to audit
        if os.path.exists(self.params.AUDIT_FACES_PATH):
            with open(self.params.AUDIT_FACES_PATH, "rt") as f:
                self.faces_to_audit = json.load(f)

    def __del__(self):
        #save ID to Label DB
        if len(self.face_ids) > 0:
            with open(self.params.FACE_IDS_PATH, "wt") as f:
                json.dump(self.face_ids, f)
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
        #TODO scale frame serverside rather than client side
        faces = []
        #TODO more complicated model first that can detect many angles

        #frontal only face_recognition as fallback
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        for loc in face_recognition.face_locations(frame_rgb):
            faces.append(self.identify_face_fallback(frame_rgb, loc))
        return faces
        
    def identify_face(self, frame) -> Face:
        pass
        # face_fisher_recognizer = cv2.face.FisherFaceRecognizer_create() #load facial recognition model
        # label, confidence = face_fisher_recognizer.predict(?) #who is this face? how confident are you
        # if confidence >= FaceManager.params.CONFIDENCE_TOLERANCE: #if confident enough
        #    return FaceManager.Face(label, ?)

    def identify_face_fallback(self, frame_rgb, location) -> Face:
        (y,w,h,x) = location
        encoding = face_recognition.face_encodings(frame_rgb, [location])[0]
        if str(encoding) in self.face_ids.keys():#if exact match
            # add new image to train model on
            return FaceManager.Face(self.face_ids[str(encoding)], (x,y,w,h))
        #TODO compare encodings for audited close match
        # for i,match in enumerate(face_recognition.compare_faces(self.face_ids.keys(),encoding,self.params.ENCODING_MATCH_TOLERANCE)):
        #     if match: #if close match
        #         #add new image to train model on
        #         return FaceManager.Face(self.face_ids.values()[i], (x,y,w,h))
        elif str(encoding) in self.faces_to_audit.keys(): #exact match found pending audit
            return FaceManager.Face(str(encoding), (x,y,w,h))
        #TODO compare encodings for close match pending audit
        else:
            self.faces_to_audit[str(encoding)] = frame_rgb[y:y+h, x:x+w] #add photo for auditing
            return FaceManager.Face("UNKNOWN", (x,y,w,h))
        