import json #for serializing objects
import gzip #for compression
import cv2

class FaceManager: #TODO make singleton
    class Face:
        def __init__(self, p_encoding, p_name, p_location):
            self.encoding = p_encoding
            self.name = p_name
            self.location = p_location

    class params:
        CONFIDENCE_NEEDED = 50

    faces = []

    def __init__():
        pass

    def __del__():
        pass

    def load_encodings_from_file():
        if os.path.exists(encodings_path):
            with open(encodings_path, "rt") as f:
                faces = json.load(f)
            faces = []

    def write_encodings_to_file():
        with open(encodings_path, 'wt') as file:
            file.write(json.dump(faces))

    async def find_faces(self, frame): #TODO
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        face_rectangles = face_cascade.detectMultiScale(gray)

        async for face in self.add_faces(gray, face_rectangles):
            yield face
            
    async def create_faces(self, frame, rectangles):
        for location in rectangles:
            #TODO capture image solely of face and store it
            face = FaceManager.Face(await self.encode_face(), await self.identify_face(gray, location), location)
            yield face

    async def encode_face(self, face:FaceManager.Face):
        pass

    async def identify_face(self, frame, location)->str:
        (x,y,w,h) = location
        face_fisher_recognizer = cv2.face.FisherFaceRecognizer_create()
        label, confidence = face_fisher_recognizer.predict(frame[y:y+h, x:x+w])
        if confidence >= FaceManager.params.CONFIDENCE_NEEDED:
            return label