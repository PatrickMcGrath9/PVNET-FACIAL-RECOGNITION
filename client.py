# === Selective Imports ===
from re import match #input validation
from json import load,loads, dumps #converting data to and from json
from subprocess import Popen #invoking subprocesses
from fastapi import FastAPI, Request, Response, responses, WebSocket #runs back/front end
from uvicorn import run #runs server upon file execution
from asyncio import sleep, create_task #asynchronous tasks
from aiohttp import ClientSession #connecting to endpoints to test if up
from urllib.parse import parse_qs #parsing websocket URL params
from websockets import connect #providing websocket clients
from time import time #for timeouts
from base64 import b64encode, b64decode #encoding images

# === WebUI ===
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

import cv2 #computer vision library


class Client:
    '''
    Client-side interface for the facial recognition project
    '''
    class params:
        '''
        Struct of parameters necessary for client to function
        '''
        FRAME_WIDTH = 640 #desired frame width
        FRAME_HEIGHT = 480 #desired frame height
        FRAME_RATE_SKIP = 0 #how many frames to skip
        FRAME_RATE = 0 #actual framerate
        FRAME_RATE_TARGET = 10 #desired framerate
        FRAME_COUNTER = 0 #running counter of frame amts
        FM_IP = "" #IP of FaceManager
        DB_IP = "" #IP of DatabaseManager

    def __init__(self):
        self.supported = self.get_supported() #return list of camera's supported resolutions and max framerate
        self.latest_fm_update = None #buffer of latest update from FaceManager

    def __del__(self):
        if hasattr(self, "capture"): #if video capture is set
            if not isinstance(self.capture,bool): #and not a sentinel
                self.capture.release() #release vide capture
        if hasattr(self, "fm_client"): #if FaceManager client is set
            if not isinstance(self.fm_client,bool): #and not a sentinel
                self.fm_client.close() #close connection

    def get_supported(self):
        '''
        Returns a list of main camera's supported resolutions and max frame rate
        '''
        # #FOR TESTING ONLY
        # return {"resolutions":[{"width":1280,"height":720},{"width":960,"height":540},{"width":848,"height":480},{"width":640,"height":360},{"width":424,"height":240},{"width":320,"height":180},{"width":640,"height":480},{"width":352,"height":288},{"width":320,"height":240}],"framerate":30}
        # #FOR TESTING ONLY

        supported = {"resolutions":[],"framerate":[]}
        self.capture = cv2.VideoCapture(0, cv2.CAP_ANY) #open video input(index 0), and auto detect input type(CAP_ANY)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1000000) #set to high value to later get max
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 1000000) #set to high value to later get max
        start_w = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)) #get the actual value
        start_h = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)) #get the actual value
        for width in range(start_w, 0, -100): #increment down from the max
            for height in range(start_h, 0, -100): #increment down from the max
                self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, width) #try setting the value
                self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height) #try setting the value
                temp_w = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)) #get actual
                temp_h = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)) #get actual

                width = temp_w if temp_w < width else width #if the current actual value is less than the last actual, store it (also effectively skips unnecessary decrementation)
                height = temp_h if temp_h < height else height #if the current actual value is less than the last actual, store it (also effectively skips unnecessary decrementation)

                if {"width":temp_w,"height":temp_h} not in supported["resolutions"]: #if the resolution is not in the list
                    supported["resolutions"].append({"width":temp_w,"height":temp_h}) #store it

        self.capture.set(cv2.CAP_PROP_FPS, self.params.FRAME_RATE_TARGET) #try and set target FPS
        max_framerate = int(self.capture.get(cv2.CAP_PROP_FPS)) #retrieve actual FPS
        supported["framerate"] = max_framerate #store it

        self.capture.release() #release video
        return supported

    def set_capture(self):
        '''
        Initialize the camera's resolution and frame rate
        '''
        self.capture = cv2.VideoCapture(0, cv2.CAP_ANY) #open video input(index 0), and auto detect input type(CAP_ANY)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.params.FRAME_WIDTH) #set video width
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.params.FRAME_HEIGHT) #set video height
        self.capture.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3)
        self.capture.set(cv2.CAP_PROP_FPS, self.params.FRAME_RATE_TARGET) #try and set target FPS
        self.params.FRAME_RATE = self.capture.get(cv2.CAP_PROP_FPS) #retrieve actual FPS
        self.params.FRAME_RATE_SKIP = int(self.params.FRAME_RATE / self.params.FRAME_RATE_TARGET) #calculate frame skip based on difference between target and actual
        self.params.FRAME_RATE_SKIP = self.params.FRAME_RATE_SKIP if self.params.FRAME_RATE_SKIP > 0 else 1 #if no skip needed, resort to 1 rather than 0
        self.cycle() #cycle the first frame to reduce load time of video feed

    def set_detector(self, model:str="", config:str="",score_threshold:float=0.9, nms_threshold:float=0.3, top_k:int=5000):
        '''
        Initializes face detector
        '''
        if model == "":
            with open("config.json") as cfg:
                model = load(cfg)["detector_model_path"] #load the face detection model from config
        
        input_size=(self.params.FRAME_WIDTH,self.params.FRAME_HEIGHT) #set the models input based on video's 
        self.detector = cv2.FaceDetectorYN.create( #create face detector
            model, #path to model
            config,
            input_size, #size of input image(s)
            score_threshold, #threshold to filter out bounding boxes of score smaller than
            nms_threshold, #threshold to suppress bounding boxes of IoU (intersection over union) bigger than
            top_k #	keep top K bounding boxes before NMS
        )

    def detect_face_locations(self, image=None, img_scale_factor = 1.0):
        '''
        Detects faces within the current frame
            img_scale_factor:float | Controls the scale of the image to reduce computation
        '''
        if image == None:
            image = self.current_frame
        locations = []
        img = image
        img_h, img_w = img.shape[:2] #get the current size of the image
        if img_scale_factor != 1.0: #if we want to change the scale of the image
            img = cv2.resize(img, (int(img_w * img_scale_factor), int(img_h * img_scale_factor))) #resize the image
            self.detector.setInputSize((int(img_w * img_scale_factor), int(img_h * img_scale_factor))) # update detector input size temporarily
        
        faces = self.detector.detect(img)[1] #detect faces, return locations
        if faces is not None: #if there are faces
            for i,face in enumerate(faces):
                x,y,w,h = face[0]/img_scale_factor,face[1]/img_scale_factor,face[2]/img_scale_factor,face[3]/img_scale_factor #convert and truncate them to xywh format, scale locations based on scale
                if x < 0 or y < 0 or x+w > img_w or y+h > img_h: #if location is within the bounds of the image
                    if x < 0: #if left side is too far left
                        x = 0 #clamp to left most side
                    if y < 0: #if top side is too far up
                        y = 0 #clamp to top most side
                    if x+w > img_w: #if right side is too far right
                        w -= img_w - (x+w) #reduce the width to clamp it to the right
                    if y+h > img_h: #if bottom side it too far down
                        h -= img_h - (y+h) #reduce the height to clamp it to the bottom
                locations.append((int(x),int(y),int(w),int(h))) #add to the list
        
        return locations #return list of face locations

    def draw_face_box(self, location, label):
        '''
        Draw box around location with given label
        '''
        (x, y, w, h) = location #decompose location
        cv2.rectangle(self.current_frame, (x, y), (x+w, y+h), (0, 0, 255), 2) #draw bounding box
        cv2.rectangle(self.current_frame, (x, y), (x+w, y-35), (0, 0, 255), cv2.FILLED) #draw label box
        cv2.putText(self.current_frame, label, (x, y), cv2.FONT_HERSHEY_DUPLEX, 1.25, (255, 255, 255), 1, bottomLeftOrigin=False) #draw label

    @staticmethod
    def extract_face_crops(image, locations):
        '''
        Slices current frame into face crops and turns them into transfer-ready strings
        '''
        return [image[y:y+h, x:x+w] for (x,y,w,h) in locations]

    @staticmethod
    def extract_encoded_face_crops(image, locations):
        return [Client.encode_image(face_crop) for face_crop in Client.extract_face_crops(image, locations)]

    @staticmethod
    def decode_image(image):
        '''
        Convert image from B64 string
        '''
        return cv2.imdecode(numpy.frombuffer(b64decode(image), dtype=numpy.uint8), cv2.IMREAD_COLOR)

    @staticmethod
    def encode_image(image):
        '''
        Convert image to B64 string
        '''
        return b64encode(cv2.imencode('.jpg', image)[1]).decode('utf-8')

    def cycle(self):
        '''
        Cycles the video capture, returns whether there was an update and the updated frame
        '''
        if self.capture is None: #if capture is not set
            return (False, None)
        
        has_frame, frame = self.capture.read() #read video input
        if not has_frame: #if there is no frame
            return (False, self.current_frame) #return last frame

        if self.params.FRAME_COUNTER % self.params.FRAME_RATE_SKIP != 0: #if we need to skip the current frame
            self.params.FRAME_COUNTER += 1
            return (False, self.current_frame)
        if self.params.FRAME_COUNTER >= self.params.FRAME_RATE: #reset the frame counter
            self.params.FRAME_COUNTER = 0

        self.current_frame = frame #set new frame if skip isn't needed
        self.params.FRAME_COUNTER += 1 #increase frame counter

        return (True, self.current_frame)

    async def fm_response_handler(self):
        '''
        Handles responses from the FaceManager and queues to display information
        '''
        while True:
            try:
                if isinstance(self.fm_client,bool): #if FaceManager disconnected
                    return #stop handler
                response = loads(await self.fm_client.recv()) #wait to recieve data
                self.latest_fm_update = list(zip(response["locations"], response["labels"])) #set the buffer
            except Exception as e:
                print(f"FM response handler error: {e}")
                await sleep(0)

global facemanager
global client
facemanager = None
client = Client()

app = FastAPI() #initialize the API

# Mount static files (for CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root(request: Request):
    # Serve the HTML UI from template file, passing request for Jinja2
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/supported")
async def get_supported():
    '''
    Return the supported resolutions and framerate
    '''
    return client.supported

@app.get("/facemanager_setup")
async def facemanager_setup(request:Request,response:Response,ip:str="",port:str=""):
    '''
    Called to setup the FaceManager, can accept two optional URL parameters:
        ip: the IP of a remote FaceManager that is already launched
        port: the port that the FaceManager is accepting requests to
    Sample Request: http://localhost:9253/facemanager_setup
    '''
    if client.params.FM_IP != "": #if FaceManager IP is bound already
        return "FaceManager Connected"

    if ip == "" and port == "": #if IP and Port are not provided
        try:
            facemanager = Popen(['python', 'facemanager.py']) #create FaceManager subprocess
        except Exception as e:
            response.status_code = 400
            return f"There was an issue with launching FaceManager locally:{e}"
        ip = "localhost" #IP is local
        port = 9254 #Port is default
    else:
        try:
            if ip == "" or port == "": #if either IP or Port are unassigned, we cannot connect
                raise Exception("IP or port is invalid")
            pattern = r"^((?:\d{1,3}\.){3}\d{1,3}):(\d{1,5})$"  # used to find ip and port
            ip_port = match(pattern, f"{ip}:{port}") #search for it
            if ip_port is None: #if there is no match
                raise Exception(f"{ip_port} is invalid")
        except:
            response.status_code = 400
            return "IP and/or port Invalid"
    
    url = f"http://{ip}:{port}"
    start = time()
    timeout = 60 #minute long timeout
    try:
        while time() < start + timeout: #keep trying to connect until the connection is timed out
            try:
                async with ClientSession() as session:
                    async with session.get(url) as resp: #try to fetch the FaceManager index
                        if resp.status == 200: #if facemanager responds, then set the IP
                            start = -1
                            client.params.FM_IP = f"{ip}:{port}"
                            client.fm_client = True #set to a sentinel value to show client may connect to desired endpoint when necessary
            except Exception as e:
                await sleep(0.5)
        if start != -1:
            raise Exception("Connection timed out")
    except Exception as e:  
        response.status_code = 400
        return f"There was an issue connecting to FaceManager:{e}"
    return "FaceManager Connected"

@app.get("/database_setup")
async def database_setup(request: Request, response: Response):
    '''
    Called to setup the DatabaseManager through the connected FaceManager.
    Assumes FaceManager is already running and available.
    '''
    if client.params.FM_IP == "": #if the FaceManager IP is not set
        response.status_code = 400
        return "FaceManager not connected"
    try:
        async with ClientSession() as session:
            async with session.get(f"http://{client.params.FM_IP}/database_setup") as resp: #fetch the FaceManager's database setup endpoint
                if resp.status == 200:
                    return "DatabaseManager Connected"
                else:
                    response.status_code=resp.status
                    return f"DatabaseManager setup failed: {await resp.text()}"
    except Exception as e:
        response.status_code = 400
        return f"Exception occurred while connecting to DatabaseManager: {e}"

@app.get("/audit")
async def audit(request: Request, response: Response):
    async with ClientSession() as session:
        async with session.get(f"http://{client.params.FM_IP}/db_ip") as resp:
            client.params.DB_IP = (await resp.text()).strip("\"")

    return "PLACEHOLDER"

    #load front end
    
@app.get("/audit/get_unknown")
async def get_unknown(request: Request, response:Response):
    try:
        async with ClientSession() as session:
            async with session.get(f"http://{client.params.DB_IP}/get_unknown") as resp:
                return await resp.json()
    except Exception as e:
        response.status_code = 400
        return f"CL Error:{e}"
    

@app.websocket("/ws/video_feed")
async def websocket_video(websocket: WebSocket):
    '''
    The endpoint which supplies video feed to the client via a websocket, has many url parameters:
        width:int | the desired width for the video capture
        height:int | the desired height for the video capture
        fps_target:int | the desired framerate
        identify:bool | should the faces be identified?
        detect:bool | should faces be detected?
    '''
    await websocket.accept() #wait for websocket connection to be accepted
    query_params = parse_qs(websocket.url.query) #get the query's url
    # === GETTING PARAMETERS ===
    width = int(query_params.get("width", [640])[0])
    height = int(query_params.get("height", [480])[0])
    fps_target = int(query_params.get("fps_target", [30])[0])
    identify = query_params.get("identify", ["false"])[0].lower() == "true"
    detect = query_params.get("detect", ["false"])[0].lower() == "true"
    # === SETTING PARAMETERS ===
    client.params.FRAME_WIDTH, client.params.FRAME_HEIGHT = width,height
    client.params.FRAME_RATE_TARGET = fps_target

    client.set_detector() #initialize the facial detection
    if client.fm_client is not None: #if the FaceManager isn't connected
        client.fm_client = await connect("ws://"+client.params.FM_IP+"/ws/identify") #connect to it
        create_task(client.fm_response_handler()) #offload handling and queueing responses to background

    client.set_capture()
    try:
        while True:
            has_frame, _ = client.cycle() #get frame
            if not has_frame:
                continue
            
            if identify or detect: #if user wants to identify or detect faces
                locs = client.detect_face_locations() #detect face locations
                if identify and client.fm_client is not None: #if identifying and FaceManager connection made
                    send = {"faces":client.extract_encoded_face_crops(client.current_frame, locs), "locations":locs, "time":time()} #organize data to send
                    await client.fm_client.send(dumps(send)) #convert to string and send it
                    if client.latest_fm_update is not None: #whatever the latest update from FaceManager is
                        for each in client.latest_fm_update: #draw each
                            loc = each[0]
                            label = each[1]
                            client.draw_face_box(loc, label)
                else:
                    for loc in locs: #for each location
                        client.draw_face_box(loc, "?") #person is not identified    
            await websocket.send_bytes(cv2.imencode(".jpg", client.current_frame)[1].tobytes()) #send the current frame (with updates if applicable)
            await sleep(0)
    except Exception as e:
        print(f"Client Websocket Error at /ws/video_feed: {e}")
    finally:
        try:
            if client.fm_client is not None:
                await client.fm_client.close()
                client.fm_client = True
            if client.capture is not None:
                client.capture.release()
            try:
                await websocket.close()
            except RuntimeError:
                pass  # websocket already closed
        except Exception as e:
            print(f"Exception during cleanup: {e}")

if __name__ == "__main__":      
    run(app, host="0.0.0.0", port=9253)

# # Don't redirect, make a GET request
# # Use javascript (fetch)
# # Have image tag point to video feed endpoint