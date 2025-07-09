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
import websockets

class FaceManager: #TODO make singleton
    class params:
        FRAME_SCALE_FACTOR = 0.75  # Scale down for faster processing
        ENCODING_MATCH_TOLERANCE = 27.0 #how far apart should encodings be to qualify as matches
        DB_IP = ""
    
    def __init__(self):
        self.db_encodings = {}
        self.db_labels = {}
        self.update_queue = asyncio.Queue()
        self.set_identifier() #initialize face identifier model
    
    def __del__(self):
        if hasattr(self, "db_client"):
            self.db_client.close()
    
    @staticmethod
    def decode_image(image):
        return cv2.imdecode(numpy.frombuffer(image, numpy.uint8), cv2.IMREAD_COLOR)

    @staticmethod
    def encode_image(image):
        _,jpg_frame = cv2.imencode('.jpg', image)
        return jpg_frame.tobytes()

    @staticmethod
    def convert_face_crops(faces):
        return [FaceManager.decode_image(face.encode("latin-1")) for face in faces]

    def set_identifier(self, model:str=""):
        if model == "":
            with open("config.json") as cfg:
                model = json.load(cfg)["identifier_model_path"]
        self.embed_net = cv2.dnn.readNetFromONNX(model) #load recognition model
        #OpenCV must include CUDA support
        #self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
        #self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)

    async def db_update(self):
        #TODO make function async and run it from within database setup
        while True:
            if self.params.DB_IP == "":
                await asyncio.sleep(1)
                continue
            try:
                async with websockets.connect("ws://"+self.params.DB_IP+"/ws/identities") as updater:
                    async def receiver():
                        while True:
                            msg = await updater.recv()
                            data = json.loads(msg)
                            self.db_encodings = data["encodings"]
                            self.db_labels = data["labels"]
                            print("FaceManager updated from DB.")

                    async def sender():
                        while True:
                            update = await self.update_queue.get()
                            await updater.send(update)
                            print("Sent update to server")
                    
                    await asyncio.gather(receiver(), sender())
            except Exception as e:
                print(f"FaceManager Websocket Error when db_update: {e}")
                await asyncio.sleep(0)

    def identify_faces(self, faces):
        labels = []
        #TODO: run the trained NN first, then use on fail encoding fall back
        #return self.identify_face(face_crop)
        for face in faces:
            id = self.identify_face_fallback(face)

            if id[0] is None: #if no match
                update = {
                    "id": str(uuid.uuid4()),
                    "encoding": id[1].tolist(),
                    "face": self.encode_image(face).decode('latin-1'),
                    "label":"?"
                }
                self.update_queue.put_nowait(json.dumps(update))
                labels.append("?")
            else:
                labels.append(self.db_labels[id])
        return labels
                
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

        id_time = time.time()
        blob = cv2.dnn.blobFromImage(image=face_crop, size=(112,112), swapRB=True) # turn image into 'blob' for DNN input#, scalefactor=self.params.FRAME_SCALE_FACTOR
        self.embed_net.setInput(blob) #set the input
        embedding = self.embed_net.forward() #get embedding        
        
        match = -1

        for id,encoding in self.db_encodings.items(): #for every existing embeedding
            dist = numpy.linalg.norm(embedding-numpy.array(encoding, dtype=float32)) #calculate distance between that embedding and the current
            if dist < FaceManager.params.ENCODING_MATCH_TOLERANCE: #if below some tolerance
                match = id #found!
                break
        if match == -1: #if no match is found
            print(f"Facemanager ID Time: {time.time()-id_time}")
            return (None,embedding)
        else:
            #TODO match found, update DB recent faces
            print(f"Facemanager ID Time: {time.time()-id_time}")
            return match

global database
global facemanager
facemanager = FaceManager()
database = None
app = fastapi.FastAPI()

@app.get("/")
async def root():
    return fastapi.responses.PlainTextResponse("FaceManager is running.")

@app.post("/encodings")
async def update_encodings(request:fastapi.Request):
    encodings = await resp.json() #get list of all ids and their encodings

@app.websocket("/ws/identify")
async def identify(websocket: fastapi.WebSocket):
    await websocket.accept()
    try:
        while True:
            payload = json.loads(await websocket.receive_text())
            if time.time()-payload["time"] > 1:
                continue
            payload["labels"] = facemanager.identify_faces(facemanager.convert_face_crops(payload["faces"]))
            del payload["faces"]
            await websocket.send_text(json.dumps(payload))
    except Exception as e:
        print(f"FaceManager Websocket Error at /ws/identify:{e}")

@app.get("/database_setup")
async def database_setup(request:fastapi.Request,response:fastapi.Response,ip:str="",port:str=""):
    '''
    Called to setup the database, can accept two optional URL parameters:
        ip: the IP of a remote FaceManager that is already launched
        port: the port that the FaceManager is accepting requests to
    '''

    if ip == "" and port == "":
        try:
            database = Popen(['python', 'databasemanager.py'])
        except Exception as e:
            return fastapi.responses.PlainTextResponse(f"There was an issue with launching DatabaseManager locally:{e}", status_code=400)
        ip = "localhost"
        port = 9255
    else:
        try:
            if ip == "" or port == "":
                raise Exception("IP or port is invalid")
            pattern = r"^((?:\d{1,3}\.){3}\d{1,3}):(\d{1,5})$"  # used to find ip and port
            ip_port = re.match(pattern, f"{ip}:{port}") #search for it
            if ip_port is None: #if there is no match
                raise Exception(f"{ip_port} is invalid")
        except:
            return fastapi.responses.PlainTextResponse("IP and/or port Invalid",status_code=400)
    
    url = f"http://{ip}:{port}"
    start = time.time()
    timeout = 10
    try:
        while time.time() < start + timeout: #keep trying to connect until the connection is timed out
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        if resp.status == 200: #if facemanager responds, then set the IP
                            start = -1
                            facemanager.params.DB_IP = f"{ip}:{port}"
                            facemanager.db_client = True #set to a sentinel value, connecto desired endpoint when necessary
                            asyncio.create_task(facemanager.db_update())
            except Exception as e:
                await asyncio.sleep(0.5)
        if start != -1:
            raise Exception("Connection timed out")
    except Exception as e:
        return fastapi.responses.PlainTextResponse(f"There was an issue connecting to DatabaseManager:{e}", status_code = 400)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9254)
