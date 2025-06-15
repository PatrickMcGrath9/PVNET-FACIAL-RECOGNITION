import json #for serializing objects
import gzip #for compression
import cv2 #for facial recognition
import numpy
import aiohttp #for creating a client to talk to DB
from subprocess import Popen #for invoking databasemanager
import time

import asyncio
import fastapi
import uvicorn
from numpy import float32

import uuid

class FaceManager: #TODO make singleton
    class params:
        FRAME_SCALE_FACTOR = 0.75  # Scale down for faster processing
        ENCODING_MATCH_TOLERANCE = 27.0 #how far apart should encodings be to qualify as matches
        DATABASE_IP = ""
    
    def __init__(self):
        self.db_client = None
        self.db_encodings = {}
        self.db_labels = {}
        self.last_update_timestamp = None
        self.set_identifier() #initialize face identifier model
    
    def __del__(self):
        if self.db_client is not None:
            self.db_client.close()
    
    def set_identifier(self, model:str=""):
        if model == "":
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
        if face_crop is None or face_crop.size == 0:
            raise ValueError("Empty face crop")

        blob = cv2.dnn.blobFromImage(image=face_crop, size=(112,112), swapRB=True) # turn image into 'blob' for DNN input#, scalefactor=self.params.FRAME_SCALE_FACTOR
        self.embed_net.setInput(blob) #set the input
        embedding = self.embed_net.forward() #get embedding        
        
        match = -1

        for id,encoding in self.db_encodings.items(): #for every existing embeedding
            dist = numpy.linalg.norm(embedding-numpy.array(encoding, dtype=float32)) #calculate distance between that embedding and the current
            print(dist)
            if dist < FaceManager.params.ENCODING_MATCH_TOLERANCE: #if below some tolerance
                match = id #found!
                break
        if match == -1: #if no match is found
            return (None,embedding)
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

@app.post("/encodings")
async def update_encodings(request:fastapi.Request):
    encodings = await resp.json() #get list of all ids and their encodings

@app.post("/identify_faces")
async def identify_faces(request:fastapi.Request):
    if face_manager.db_client is None:
        return fastapi.responses.PlainTextResponse("Database not connected to identify people", status_code=400)

    data = await request.json()

    async with face_manager.db_client.get(url=f"{face_manager.params.DATABASE_IP}/identities", json={"timestamp":face_manager.last_update_timestamp}) as resp:
        if resp.status == 200:
            identities = await resp.json()
            face_manager.db_encodings = identities["encodings"]
            face_manager.db_labels = identities["labels"]
            face_manager.last_update_timestamp = identities["timestamp"]
    
    for each in data:
        face = each["face"]
        id = face_manager.find_face(numpy.array(face, dtype='uint8'))
        if id[0] is None:
            new_uuid = str(uuid.uuid4())
            each["id"] = new_uuid
            each["encoding"] = id[1].tolist()
            if face_manager.db_client is not None:
                each["label"] = "?"
                async with face_manager.db_client.patch(url=f"{face_manager.params.DATABASE_IP}/identities", json=each) as resp:
                    pass
            face_manager.db_encodings[new_uuid] = id[1].tolist()
            face_manager.db_labels[new_uuid] = "?"
            continue
        each["label"] = face_manager.db_labels[id]
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
                            face_manager.params.DATABASE_IP = url
            except Exception as e:
                pass
        if start != -1:
            raise Exception("Connection timed out")
    except Exception as e:
        response.status_code = 400
        return fastapi.responses.PlainTextResponse(f"There was an issue connecting to database:{e}")
    face_manager.db_client = aiohttp.ClientSession()
    async with face_manager.db_client.get(url+"/identities", json={"timestamp":-1}) as resp:
        data = await resp.json()
        face_manager.db_encodings = data["encodings"]
        face_manager.db_labels = data["labels"]
        face_manager.last_update_timestamp = data["timestamp"]
    return fastapi.responses.PlainTextResponse("Database Connected")

if __name__ == "__main__":
    uvicorn.run(app, port=9254)
