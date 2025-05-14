import cv2 #OpenCV, computer vision library. TODO CPU ONLY!
import re #regex, for input validation
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
        FRAME_HEIGHT = 360
        FRAME_RATE_SKIP = 0
        FRAME_RATE = 0
        FRAME_RATE_TARGET = 10
        FRAME_COUNTER = 0
        RETRY_TIMEOUT = 10 #TODO used with async.timeout
        FACEMANAGER_IP = ""
        INITIALIZED = False

    def __init__(self):
        self.params.INITIALIZED = False
        self.current_frame = None
        self.capture = cv2.VideoCapture(0, cv2.CAP_ANY) #open video input(index 0), and auto detect input type(CAP_ANY)
        self.params.INITIALIZED = True

    def __del__(self):
        if self.capture is not None:
            self.capture.release()
        if self.fm_client is not None:
            self.fm_client.close()
        self.params.INITIALIZED = False
        cv2.destroyAllWindows()
        
    def set_capture(self):
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.params.FRAME_WIDTH) #capture width
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.params.FRAME_HEIGHT) #capture height
        self.capture.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3)
        self.capture.set(cv2.CAP_PROP_FPS, self.params.FRAME_RATE_TARGET) #try and set target FPS
        self.params.FRAME_RATE = self.capture.get(cv2.CAP_PROP_FPS) #retrieve actual FPS
        self.params.FRAME_RATE_SKIP = int(self.params.FRAME_RATE / self.params.FRAME_RATE_TARGET) #calculate frame skip
        self.params.FRAME_RATE_SKIP = self.params.FRAME_RATE_SKIP if self.params.FRAME_RATE_SKIP > 0 else 1 #if no skip needed, resort to 1 rather than 0
        self.cycle() #cycle the first frame to reduce load time?

    def set_detector(self, model:str="models/face_detection_yunet_2023mar.onnx", config:str="",score_threshold:float=0.9, nms_threshold:float=0.3, top_k:int=5000):
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
        faces = self.detector.detect(img)[1]
        if faces is not None:
            ret = []
            for i,face in enumerate(faces):
                ret.append((int(face[0]),int(face[1]),int(face[2]),int(face[3])))#x,y,w,h
            return ret
        else:
            return None

    def get_face_crops(self, img, locations):
        return [img[y:y+h, x:x+w] for (x,y,w,h) in locations]

    def draw_face_box(self, location, name):
        '''
        Not needed since switching to WebUI which will display face crops rather than drawing box around faces
        '''
        (x, y, w, h) = location
        cv2.rectangle(self.current_frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
        cv2.rectangle(self.current_frame, (x, y), (x+w, y-35), (0, 0, 255), cv2.FILLED)
        cv2.putText(self.current_frame, name, (x, y), cv2.FONT_HERSHEY_DUPLEX, 1.25, (255, 255, 255), 1, bottomLeftOrigin=False)

    def cycle(self):
        has_frame, frame = self.capture.read()
        if not has_frame: #if there is no frame
            return (False, self.current_frame)

        if self.params.FRAME_COUNTER % self.params.FRAME_RATE_SKIP != 0:
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

@app.get("/video_feed")
async def video_feed(request:fastapi.Request,response:fastapi.Response, width:int=640, height:int=480,fps_target:int=60,identify:bool=False,detect:bool=True):
    '''
    Called to display a stream of frames from the camera. Can specify four optional URL parameters:
        width: the desired width of the video capture (depends on what resolutions camera supports) (larger resolutions reduce framerate)
        height: the desired height of the video capture (depends on what resolutions camera supports) (larger resolutions reduce framerate)
        fps_target: the desired framerate for the video capture (depends on what framerates camera supports)
        identify: should frames be sent to FaceManager and identified?
    Sample request: http://localhost:9253/video_feed?width=1280&height=720&fps_target=5&identify=true
    Note: you must close the old tab and open a new one for each request
    '''
    if client.params.INITIALIZED: #initialize client if not already
        client.params.FRAME_WIDTH, client.params.FRAME_HEIGHT = width,height
        client.params.FRAME_RATE_TARGET = fps_target
        client.set_capture()
        client.set_detector()
    else:
        response.status_code = 400
        return fastapi.responses.PlainTextResponse(f"Client not initialized")
    if identify and client.params.FACEMANAGER_IP == "":
        response.status_code = 400
        return fastapi.responses.PlainTextResponse("Cannot identify, FaceManager not connected")
    
    async def stream_mpeg():
        while True: #until something disrupts the connection
            try:
                if await request.is_disconnected():
                    raise Exception("Client disconnected")

                #capture frame
                has_frame, _ = client.cycle()
                if not has_frame:
                    continue
                
                if identify:
                    data = get_face_locations_and_crops()
                    if data is not None:
                        #data['frame'] = cv2.imencode('.jpg', client.current_frame)[1].tolist() 
                        try:
                            async with client.fm_client.post(url=f"{client.params.FACEMANAGER_IP}/identify_faces", json=data) as resp: #send image to face manager
                                if resp.status == 200:
                                    data = await resp.json() #get back data
                                    for _,face in data.items():
                                        client.draw_face_box(face['location'], face['name']) #draw boxes around faces
                        except aiohttp.client_exceptions.InvalidUrlClientError: #if facemanager not launched
                            print("FaceManager not connected")
                        except Exception as e:
                            print(f"Issue identifying faces: {e}")
                        
                elif detect:
                    locs = client.detect_face_locations(client.current_frame)
                    if locs is not None:
                        for location in locs:
                            client.draw_face_box(location, "")
                
                img_bytes = cv2.imencode('.jpg', client.current_frame)[1].tobytes()
                # write frame as part of multipart back to client
                yield b'--frame\r\n' + b'Content-Type: image/jpeg\r\n\r\n' + img_bytes + b'\r\n'
                await asyncio.sleep(0.000000001)  #allow buffer to flush
            except Exception as e:
                print(f"Error streaming video: {e}")
                break #client probably just disconnected
    
    def get_face_locations_and_crops():
        '''
        Returns a dictionary of face location and crops ({location:crop}) tuples 
        '''
        locs = client.detect_face_locations(client.current_frame)
        if locs is None:
            return None
        crops = client.get_face_crops(client.current_frame, locs)
        return {idx:(loc,crop.tolist()) for idx,(loc,crop) in enumerate(zip(locs,crops))} 
    
    response.headers["Content-Type"] = "multipart/x-mixed-replace; boundary=frame"
    stream = fastapi.responses.StreamingResponse(stream_mpeg(), media_type="multipart/x-mixed-replace; boundary=frame")
    return stream

@app.get("/recent_faces")
async def recent_faces(response:fastapi.Response):
    #ask face manager for list of recent faces
    return fastapi.responses.PlainTextResponse("Recent faces data placeholder")

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