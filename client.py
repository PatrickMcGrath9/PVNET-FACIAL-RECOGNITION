import cv2 #OpenCV, computer vision library. TODO CPU ONLY!
import re #regex, for input validation
import json
from subprocess import Popen #for invoking facemanager
import fastapi
import uvicorn
import asyncio
import aiohttp
import time
import base64
from urllib.parse import parse_qs
import websockets
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

class Client:
    class params:
        FRAME_WIDTH = 640
        FRAME_HEIGHT = 480
        FRAME_RATE_SKIP = 0
        FRAME_RATE = 0
        FRAME_RATE_TARGET = 10
        FRAME_COUNTER = 0
        IMG_QUALITY = 75
        FM_IP = ""
        INITIALIZED = False

    def __init__(self):
        self.params.INITIALIZED = False
        self.set_detector()
        self.supported = self.get_supported()
        self.latest_fm_update = None
        self.params.INITIALIZED = True

    def __del__(self):
        if hasattr(self, "capture"):
            self.capture.release()
        if hasattr(self, "fm_client"):
            self.fm_client.close()
        self.params.INITIALIZED = False
        cv2.destroyAllWindows()

    def get_supported(self):
        supported = {"resolutions":[],"framerate":[]}
        self.capture = cv2.VideoCapture(0, cv2.CAP_ANY) #open video input(index 0), and auto detect input type(CAP_ANY)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1000000) #capture width
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 1000000) #capture height
        start_w = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        start_h = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

        for width in range(start_w, 0, -100):
            for height in range(start_h, 0, -100):
                self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, width) #capture width
                self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height) #capture height
                temp_w = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
                temp_h = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

                width = temp_w if temp_w < width else width
                height = temp_h if temp_h < height else height

                if {"width":temp_w,"height":temp_h} not in supported["resolutions"]:
                    supported["resolutions"].append({"width":temp_w,"height":temp_h})

        self.capture.set(cv2.CAP_PROP_FPS, self.params.FRAME_RATE_TARGET) #try and set target FPS
        max_framerate = int(self.capture.get(cv2.CAP_PROP_FPS)) #retrieve actual FPS
        supported["framerate"] = max_framerate

        self.capture.release()
        return supported

    def set_capture(self):
        self.capture = cv2.VideoCapture(0, cv2.CAP_ANY) #open video input(index 0), and auto detect input type(CAP_ANY)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.params.FRAME_WIDTH) #capture width
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.params.FRAME_HEIGHT) #capture height
        self.capture.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3)
        self.capture.set(cv2.CAP_PROP_FPS, self.params.FRAME_RATE_TARGET) #try and set target FPS
        self.params.FRAME_RATE = self.capture.get(cv2.CAP_PROP_FPS) #retrieve actual FPS
        self.params.FRAME_RATE_SKIP = int(self.params.FRAME_RATE / self.params.FRAME_RATE_TARGET) #calculate frame skip
        self.params.FRAME_RATE_SKIP = self.params.FRAME_RATE_SKIP if self.params.FRAME_RATE_SKIP > 0 else 1 #if no skip needed, resort to 1 rather than 0
        self.cycle() #cycle the first frame to reduce load time?

    def set_detector(self, model:str="", config:str="",score_threshold:float=0.9, nms_threshold:float=0.3, top_k:int=5000):
        if model == "":
            with open("config.json") as cfg:
                model = json.load(cfg)["detector_model_path"]
        
        input_size=(self.params.FRAME_WIDTH,self.params.FRAME_HEIGHT)
        self.detector = cv2.FaceDetectorYN.create(
            model, #path to model
            config,
            input_size, #size of input image(s)
            score_threshold, #threshold to filter out bounding boxes of score smaller than
            nms_threshold, #threshold to suppress bounding boxes of IoU (intersection over union) bigger than
            top_k #	keep top K bounding boxes before NMS
        )

    def detect_face_locations(self, scale = 0.25):
        img_h, img_w = self.current_frame.shape[:2]
        small_frame = cv2.resize(self.current_frame, (int(img_w * scale), int(img_h * scale)))
        
        # Update detector input size temporarily
        self.detector.setInputSize((int(img_w * scale), int(img_h * scale)))
        
        faces = self.detector.detect(small_frame)[1]
        if faces is not None: #if there are faces
            locations = []
            for i,face in enumerate(faces): #convert and truncate them to xywh format
                x,y,w,h = face[0]/scale,face[1]/scale,face[2]/scale,face[3]/scale
                if x < 0 or y < 0 or x+w > img_w or y+h > img_h:
                    continue
                locations.append((int(x),int(y),int(w),int(h)))
            return locations #return list of face locations
        else:
            return None

    def draw_face_box(self, location, label):
        (x, y, w, h) = location
        cv2.rectangle(self.current_frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
        cv2.rectangle(self.current_frame, (x, y), (x+w, y-35), (0, 0, 255), cv2.FILLED)
        cv2.putText(self.current_frame, label, (x, y), cv2.FONT_HERSHEY_DUPLEX, 1.25, (255, 255, 255), 1, bottomLeftOrigin=False)

    def extract_encoded_face_crops(self, locations):
        return [self.encode_image(self.current_frame[y:y+h, x:x+w]).decode("latin-1") for (x,y,w,h) in locations]

    def encode_image(self, image):
        _,jpg_frame = cv2.imencode('.jpg', image)
        return jpg_frame.tobytes()

    def cycle(self):
        if self.capture is None:
            return (False, None)
        
        has_frame, frame = self.capture.read()
        if not has_frame: #if there is no frame
            return (False, self.current_frame)

        if self.params.FRAME_COUNTER % self.params.FRAME_RATE_SKIP != 0: #if we need to skip the current frame
            self.params.FRAME_COUNTER += 1
            return (False, self.current_frame)
        if self.params.FRAME_COUNTER >= self.params.FRAME_RATE:
            self.params.FRAME_COUNTER = 0

        self.current_frame = frame
        self.params.FRAME_COUNTER += 1

        return (True, self.current_frame)

    async def fm_response_handler(self):
        while True:
            try:
                if isinstance(self.fm_client,bool):
                    return
                response = json.loads(await self.fm_client.recv())
                self.latest_fm_update = list(zip(response["locations"], response["labels"]))
            except Exception as e:
                print(f"FM response handler error: {e}")
                await asyncio.sleep(0)


global facemanager #global reference to facemanager process (if needed)
global client #global reference to client object
facemanager = None
client = Client()

app = fastapi.FastAPI()

# Mount static files (for CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup Jinja2 templates folder
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root(request: fastapi.Request):
    # Serve the HTML UI from template file, passing request for Jinja2
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/supported")
async def get_supported():
    return client.supported

@app.get("/facemanager_setup")
async def facemanager_setup(request:fastapi.Request,response:fastapi.Response,ip:str="",port:str=""):
    '''
    Called to setup the FaceManager, can accept two optional URL parameters:
        ip: the IP of a remote FaceManager that is already launched
        port: the port that the FaceManager is accepting requests to
    Sample Request: http://localhost:9253/facemanager_setup
    '''
    if client.params.FM_IP != "":
        return fastapi.responses.PlainTextResponse("Facemanager Connected")

    if ip == "" and port == "":
        try:
            facemanager = Popen(['python', 'facemanager.py'])
        except Exception as e:
            return fastapi.responses.PlainTextResponse(f"There was an issue with launching FaceManager locally:{e}", status_code=400)
        ip = "localhost"
        port = 9254
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
                            client.params.FM_IP = f"{ip}:{port}"
                            client.fm_client = True #set to a sentinel value, connecto desired endpoint when necessary
            except Exception as e:
                await asyncio.sleep(0.5)
        if start != -1:
            raise Exception("Connection timed out")
    except Exception as e:  
        response.status_code = 400
        return fastapi.responses.PlainTextResponse(f"There was an issue connecting to FaceManager:{e}")
    return fastapi.responses.PlainTextResponse("Facemanager Connected")

@app.get("/database_setup")
async def database_setup(request: fastapi.Request, response: fastapi.Response):
    '''
    Called to setup the DatabaseManager through the connected FaceManager.
    Assumes FaceManager is already running and available.
    '''
    if client.params.FM_IP == "":
        return fastapi.responses.PlainTextResponse("FaceManager not connected yet", status_code=400)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://{client.params.FM_IP}/database_setup") as resp:
                if resp.status == 200:
                    return fastapi.responses.PlainTextResponse("DatabaseManager Connected", status_code=200)
                else:
                    return fastapi.responses.PlainTextResponse(f"DatabaseManager setup failed: {await resp.text()}", status_code=resp.status)
    except Exception as e:
        return fastapi.responses.PlainTextResponse(f"Exception occurred while connecting to DatabaseManager: {e}", status_code=400)


@app.websocket("/ws/video_feed")
async def websocket_video(websocket: fastapi.WebSocket):
    await websocket.accept()
    query_params = parse_qs(websocket.url.query)
    width = int(query_params.get("width", [640])[0])
    height = int(query_params.get("height", [480])[0])
    fps_target = int(query_params.get("fps_target", [60])[0])
    identify = query_params.get("identify", ["false"])[0].lower() == "true"
    detect = query_params.get("detect", ["false"])[0].lower() == "true"
    client.params.FRAME_WIDTH, client.params.FRAME_HEIGHT = width,height
    client.params.FRAME_RATE_TARGET = fps_target
    client.set_capture()
    client.set_detector()
    if client.fm_client is not None:
        client.fm_client = await websockets.connect("ws://"+client.params.FM_IP+"/ws/identify")
        asyncio.create_task(client.fm_response_handler())
    try:
        while True:
            has_frame, _ = client.cycle()
            if not has_frame:
                continue
            locs = client.detect_face_locations()
            if (locs is not None) and (len(locs) != 0):
                if client.fm_client is not None:
                    send = {"faces":client.extract_encoded_face_crops(locs), "locations":locs, "time":time.time()}
                    await client.fm_client.send(json.dumps(send))
                    if client.latest_fm_update is not None:
                        for each in client.latest_fm_update:
                            loc = each[0]
                            label = each[1]
                            client.draw_face_box(loc, label)
                else:
                    for loc in locs:
                        client.draw_face_box(loc, "?")
            await websocket.send_bytes(client.encode_image(client.current_frame))
            await asyncio.sleep(0)
    except Exception as e:
        print(f"Client Websocket Error at /ws/video_feed: {e}")
    finally:
        if client.fm_client is not None:
            await client.fm_client.close()
            client.fm_client = True
        client.capture.release()
        await websocket.close()

if __name__ == "__main__":      
    uvicorn.run(app, host="0.0.0.0", port=9253)


# Don't redirect, make a GET request
# Use javascript (fetch)
# Have image tag point to video feed endpoint

