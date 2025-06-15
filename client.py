import cv2 #OpenCV, computer vision library. TODO CPU ONLY!
import re #regex, for input validation
import json

from subprocess import Popen #for invoking facemanager

#TODO WebUI
import fastapi
import uvicorn
import asyncio
import aiohttp
import time

class Client:
    class params:
        FRAME_WIDTH = 640
        FRAME_HEIGHT = 480
        FRAME_RATE_SKIP = 0
        FRAME_RATE = 0
        FRAME_RATE_TARGET = 10
        FRAME_COUNTER = 0
        FACEMANAGER_IP = ""
        INITIALIZED = False

    def __init__(self):
        self.params.INITIALIZED = False
        self.current_frame = None
        self.set_detector()
        self.params.INITIALIZED = True

    def __del__(self):
        if self.capture is not None:
            self.capture.release()
        if self.fm_client is not None:
            self.fm_client.close()
        self.params.INITIALIZED = False
        cv2.destroyAllWindows()
        
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

    def detect_face_locations(self, img):
        faces = self.detector.detect(img)[1] #detect face locations
        if faces is not None: #if there are faces
            locations = []
            for i,face in enumerate(faces): #convert and truncate them to xywh format
                locations.append((int(face[0]),int(face[1]),int(face[2]),int(face[3])))
            return locations #return list of face locations
        else:
            return None

    def get_face_crops(self, img, locations):
        return [img[y:y+h, x:x+w] for (x,y,w,h) in locations]

    def draw_face_box(self, location, label):
        (x, y, w, h) = location
        cv2.rectangle(self.current_frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
        cv2.rectangle(self.current_frame, (x, y), (x+w, y-35), (0, 0, 255), cv2.FILLED)
        cv2.putText(self.current_frame, label, (x, y), cv2.FONT_HERSHEY_DUPLEX, 1.25, (255, 255, 255), 1, bottomLeftOrigin=False)

    def cycle(self):
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

global facemanager #global reference to facemanager process (if needed)
global client #global reference to client object
facemanager = None
client = Client()

app = fastapi.FastAPI()

@app.get("/")
async def root():
    return fastapi.responses.PlainTextResponse("Client is running.")

@app.get("/video_feed")
async def video_feed(request:fastapi.Request,response:fastapi.Response, width:int=640, height:int=480,fps_target:int=60,identify:bool=False,detect:bool=False):
    '''
    Called to to display a stream of frames from the camera. Can specify optional URL parameters:
        width: the desired width of the video capture
        height: the desired height of the video capture
        fps_target: the desired framerate for the video capture
        identify: should faces be detected and identified?
        detect: should client try detect faces?
    Sample request: http://localhost:9253/video_feed?width=1280&height=720&fps_target=5&identify=true
    '''
    if identify and client.params.FACEMANAGER_IP == "":
        #TODO tell front end to redirect to facemanager setup page
        return fastapi.responses.PlainTextResponse("Cannot identify, FaceManager not connected", status_code=400)
    
    if client.params.INITIALIZED: #initialize client if not already
        client.params.FRAME_WIDTH, client.params.FRAME_HEIGHT = width,height
        client.params.FRAME_RATE_TARGET = fps_target
        client.set_capture()
        client.set_detector()
    else:
        return fastapi.responses.PlainTextResponse(f"Client not initialized", status_code=400)

    async def stream_mpeg():
        while True: #until something disrupts the connection
            try:
                if await request.is_disconnected():
                    raise Exception("Client disconnected")

                #capture frame
                has_frame, _ = client.cycle()
                if not has_frame:
                    continue
                
                if identify: #if request for identifying
                    locs = client.detect_face_locations(client.current_frame)
                    if locs is not None:
                        crops = client.get_face_crops(client.current_frame,locs)
                        send = [{"face":face.tolist(),"location":loc} for face,loc in zip(crops, locs)]
                        try:
                            async with client.fm_client.post(url=f"{client.params.FACEMANAGER_IP}/identify_faces", json=send) as resp: 
                                if resp.status == 200:
                                    data = await resp.json() #get back data
                                    for each in data:
                                        location = each["location"]
                                        label = each["label"]
                                        client.draw_face_box(location, label) #draw boxes around faces
                                elif resp.status == 400:
                                    raise Exception("there was an error with reaching the facemanager")
                        except aiohttp.client_exceptions.InvalidUrlClientError: #if facemanager not launched
                            pass
                        except Exception as e:
                            raise Exception(f"Issue identifying faces: {e}")
                elif detect:
                    locs = client.detect_face_locations(client.current_frame)
                    if locs is not None:
                        client.draw_face_box(loc, "?")

                img_bytes = cv2.imencode('.jpg', client.current_frame)[1].tobytes()
                # write frame as part of multipart back to client
                yield b'--frame\r\n' + b'Content-Type: image/jpeg\r\n\r\n' + img_bytes + b'\r\n'
                await asyncio.sleep(0.000000001)  #allow buffer to flush
            except Exception as e:
                print(f"Error streaming video: {e}")
                client.capture.release()
                break #client probably just disconnected

    response.headers["Content-Type"] = "multipart/x-mixed-replace; boundary=frame"
    stream = fastapi.responses.StreamingResponse(stream_mpeg(), media_type="multipart/x-mixed-replace; boundary=frame")
    return stream

@app.get("/facemanager_setup")
async def facemanager_setup(request:fastapi.Request,response:fastapi.Response,ip:str="",port:str=""):
    '''
    Called to setup the FaceManager, can accept two optional URL parameters:
        ip: the IP of a remote FaceManager that is already launched
        port: the port that the FaceManager is accepting requests to
    Sample Request: http://localhost:9253/facemanager_setup
    Note: Remote FaceManager has not been tested yet
    '''
    if ip == "": #if no IP specified
        try:
            facemanager = Popen(['python', 'facemanager.py']) #run the facemanager
        except Exception as e:
            return fastapi.responses.PlainTextResponse(f"There was an issue with launching FaceManager locally:{e}", status_code=400)
        ip = "127.0.0.1" #set IP to localhost
        port = 9254
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
                        if resp.status == 200: #if facemanager responds, then set the IP
                            start = -1
                            client.params.FACEMANAGER_IP = url
            except Exception as e:
                pass
        if start != -1:
            raise Exception("Connection timed out")
    except Exception as e:
        response.status_code = 400
        return fastapi.responses.PlainTextResponse(f"There was an issue connecting to FaceManager:{e}")
    client.fm_client = aiohttp.ClientSession()
    return fastapi.responses.PlainTextResponse("Facemanager Connected")

if __name__ == "__main__":      
    uvicorn.run(app, port=9253)
