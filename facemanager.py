import json #for serializing objects
import gzip #for compression
import cv2 #for facial recognition
import face_recognition #for facial recognition and encodings
import numpy

import asyncio
import fastapi
import socket #for retrieving host
import uvicorn

class FaceManager: #TODO make singleton
    class Face:
        def __init__(self, p_name, p_location, p_face_crop):
            self.name = p_name
            self.location = p_location
            self.frame = p_face_crop

    class params:
        FRAME_SCALE_FACTOR = 0.75  # Scale down for faster processing
        CONFIDENCE_TOLERANCE = 50 #how confident should match be to accept 
        ENCODING_NUM_JITTERS = 1 #increase to resample more times and thus make encodings more accurate, runs slower though
        ENCODING_MATCH_TOLERANCE = 0.6 #how far apart should encodings be to qualify as matches
        DB_IP = ""

    recent_faces:list[Face] = [] #array of recent faces

    def find_faces(self, frame) -> list[Face]:
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
        face_crop = frame_rgb[y:y+h, x:x+w]
        #TODO remove below. not likely to have exact matches?
        # if hash(str(encoding)) in self.id_to_label.keys():#convert encoding to ID, look for exact match
        #     # add new image to train model on
        #     return FaceManager.Face(self.id_to_label[hash(str(encoding))], (x,y,w,h))
        
        ids = [] #TODO request from DB
        id_to_encoding = {} #TODO request from DB
        id_to_label = {} #TODO request from DB

        #TODO compare encodings for close match
        for id in ids: #for every id
            if True in face_recognition.compare_faces(id_to_encoding[id], encoding, self.params.ENCODING_MATCH_TOLERANCE): #if one of the encodings match close enough
                return FaceManager.Face(id_to_label[id], (x,y,w,h), face_crop)

        face_audit = {} #TODO request from DB

        if str(encoding) not in face_audit.keys():
            pass #TODO send 'encoding' and 'face_crop'  to DB
            return FaceManager.Face("UNKNOWN", (x,y,w,h), face_crop)

face_manager = FaceManager()
app = fastapi.FastAPI()

@app.get("/")
async def root():
    return fastapi.responses.JSONResponse({"ip":socket.gethostbyname(socket.gethostname())})

@app.get("/recent_faces")
async def recent_faces():
    resp = {}
    for face in recent_faces:
        resp[face.label] = face.frame
    return fastapi.responses.JSONResponse(resp)

@app.post("/identify_faces")
async def identify_faces(request:fastapi.Request):
    data = await request.body()
    img_arr = numpy.frombuffer(data, numpy.uint8)
    frame = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
    resp = {}
    for face in face_manager.find_faces(frame):
        resp[face.name] = face.location
    return resp
    
if __name__ == "__main__":
    uvicorn.run(app, port=9254)