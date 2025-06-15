import json #for serializing objects
import gzip #for compression
import cv2 #for facial recognition
import numpy
import aiohttp #for creating a client to talk to DB

import asyncio
import fastapi
import uvicorn
from numpy import float32

import numpy as np
import face_recognition
import uuid

class FaceManager:
    class Face:
        def __init__(self, name, location):
            self.name = name
            self.location = location

class FaceManager: #TODO make singleton
    class params:
        FRAME_SCALE_FACTOR = 0.75  # Scale down for faster processing
        ENCODING_MATCH_TOLERANCE = 20.0 #how far apart should encodings be to qualify as matches
    
    def __init__(self):
        self.db_encodings = None
        self.db_labels = None
        self.set_identifier() #initialize face identifier model
    
    def __del__(self):
        if self.db_client is not None:
            self.db_client.close()
    
    def set_identifier(self, model:str):
        if model is None:
            with open("config.json") as cfg:
                model = json.load(cfg)["identifier_model_path"]
        self.embed_net = cv2.dnn.readNetFromONNX(model) #load recognition model
        #OpenCV must include CUDA support
        #self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
        #self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)

    def find_face(self, face_crop):
        #TODO: run the trained NN first, then use on fail encoding fall back
        #return self.identify_face(face_crop)
        return self.identify_face_fallback(face_crop) #on fail return id of face via encoding
                
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

        #TODO: REPLACE !!! instead of calling db at time of needing encodings, refresh local copy of encodings periodically or whenever DB has new encodings
        encodings = None
        async with facemanager.db_client.get(url=f"{facemanager.params.DATABASE_IP}/encodings") as resp:
            if resp.status == 200:
                encodings = await resp.json() #get list of all ids and their encodings
        
        match = -1

        for id,encoding in self.encodings.items(): #for every existing embeedding
            dist = numpy.linalg.norm(embedding-numpy.array(encoding, dtype=float32)) #calculate distance between that embedding and the current
            if dist < FaceManager.params.ENCODING_MATCH_TOLERANCE: #if below some tolerance
                match = id #found!
                break
        if match == -1: #if no match is found
            return None
        else:
            #TODO match found, update DB recent faces
            return match

global database
global face_manager
face_manager = FaceManager()
database = None
app = fastapi.FastAPI()

@app.get("/")
async def root():
    return fastapi.responses.PlainTextResponse("FaceManager is running.")

@app.post("/identify_faces")
async def identify_faces(request:fastapi.Request):
    data = await request.json()
    for each in data:
        face = each["face"]
        id = face_manager.find_face(numpy.array(face, dtype='uint8'))
        if id is None:
            new_uuid = str(uuid.uuid4())
            each["id"] = new_uuid
            face_manager.db_client.patch(url=f"{facemanager.param.DATABASE_IP}/identities", json=send)
            continue    
        each["label"] = self.db_labels[id]
    return fastapi.responses.JSONResponse(data)

@app.get("/database_setup")
async def database_setup(request:fastapi.Request,response:fastapi.Response,ip:str="",port:str=""):
    '''
    Called to setup the database, can accept two optional URL parameters:
        ip: the IP of a remote FaceManager that is already launched
        port: the port that the FaceManager is accepting requests to
    '''
    if ip == "": #if no IP specified
        try:
            database = Popen(['python', 'databasemanager.py'])
        except Exception as e:
            return fastapi.responses.PlainTextResponse(f"There was an issue with launching database locally:{e}", status_code=400)
        ip = "127.0.0.1" #set IP to localhost
        port = 9255
    else:
        try:
            pattern = r"^((?:\d{1,3}\.){3}\d{1,3}):(\d{1,5})$"  # used to find ip and port
            ip_port = re.match(pattern, f"{ip}:{port}") #search for it
            if ip_port is None: #if there is no match
                print(f"{ip}:{port} not valid")
                raise Exception("IP is invalid")
        except:
            return fastapi.responses.PlainTextResponse("IP & Port Invalid",status_code=400)
    url = f"http://{ip}:{port}"
    start = time.time()
    timeout = 300
    try:
        while time.time() < start + timeout: #keep trying to connect until the connection is timed out
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            start = -1
                            facemanager.params.DATABASE_IP = url
            except Exception as e:
                pass
        if start != -1:
            raise Exception("Connection timed out")
    except Exception as e:
        response.status_code = 400
        return fastapi.responses.PlainTextResponse(f"There was an issue connecting to database:{e}")
    client.db_client = aiohttp.ClientSession()
    return fastapi.responses.PlainTextResponse("Database Connected")

if __name__ == "__main__":
    uvicorn.run(app, port=9254)
