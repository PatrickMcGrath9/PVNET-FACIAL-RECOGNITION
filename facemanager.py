import json #for serializing objects
import gzip #for compression
import cv2 #for facial recognition
import numpy

import asyncio
import fastapi
import socket #for retrieving host
import uvicorn
from numpy import float32


class FaceManager: #TODO make singleton
    class params:
        FRAME_SCALE_FACTOR = 0.75  # Scale down for faster processing
        ENCODING_MATCH_TOLERANCE = 20.0 #how far apart should encodings be to qualify as matches
        DB_IP = ""
    
    def __init__(self):
        self.set_identifier()
        self.recents = {}
        self.current_recent = 0    
    
    def set_identifier(self, model:str="models/arcfaceresnet100-8.onnx"):
        self.embed_net = cv2.dnn.readNetFromONNX(model) #load recognition model
        #OpenCV must include CUDA support
        #self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
        #self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)

    def find_face(self, face_crop):
        return self.identify_face_fallback(face_crop) #use embedding/fallback Neural Net (for now as main)
                
    
    def identify_face(self, face_crop):
        '''
        Identify face from crop using a trained model of captured, labeled, & audited faces. Returns a Face object of who was identified.
        '''
        pass #TODO

    def identify_face_fallback(self, face_crop):
        '''
        Identify face from crop by extracting embeddings. Returns a Face object of who was identified.
        '''
        blob = cv2.dnn.blobFromImage(image=face_crop, size=(112,112), swapRB=True) # turn image into 'blob' for DNN input#, scalefactor=self.params.FRAME_SCALE_FACTOR
        self.embed_net.setInput(blob) #set the input
        embedding = self.embed_net.forward() #get embedding
        
        #TODO Replace. Use embeddings & labels from DB, compare each embedding, return Face object with label & crop
        match = -1
        for id,face in self.recents.items(): #for every existing embeedding
            dist = numpy.linalg.norm(embedding-numpy.array(face['embedding'], dtype=float32)) #calculate distance between that embedding and the current
            if dist < FaceManager.params.ENCODING_MATCH_TOLERANCE: #if below some tolerance
                match = id #found!
                break
        if match == -1: #if no match is found
            self.current_recent+=1
            self.recents[self.current_recent] = {'crop': face_crop.tolist(), 'name':str(self.current_recent), 'embedding': embedding.tolist()} #add embedding to list #TODO instead append to audit
            return None
        else:
            return self.recents[match]


face_manager = FaceManager()
app = fastapi.FastAPI()

@app.get("/")
async def root():
    return fastapi.responses.JSONResponse({"ip":socket.gethostbyname(socket.gethostname())})

@app.post("/identify_faces")
async def identify_faces(request:fastapi.Request):
    data = await request.json()
    resp = {}
    for idx,(location, crop) in data.items():
        face = face_manager.find_face(numpy.array(crop, dtype='uint8'))
        if face is None:
            continue
        face['location'] = location
        resp[idx] = face
    return fastapi.responses.JSONResponse(content=resp)
    
if __name__ == "__main__":
    uvicorn.run(app, port=9254)