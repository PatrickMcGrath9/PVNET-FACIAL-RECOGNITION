import cv2
import re
import json
from subprocess import Popen
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
        if hasattr(self, "fm_client") and not isinstance(self.fm_client, bool):
            self.fm_client.close()
        self.params.INITIALIZED = False
        cv2.destroyAllWindows()

    def get_supported(self):
        return {"resolutions":[{"width":1280,"height":720},{"width":960,"height":540},{"width":848,"height":480},
                {"width":640,"height":360},{"width":424,"height":240},{"width":320,"height":180},
                {"width":640,"height":480},{"width":352,"height":288},{"width":320,"height":240}],
                "framerate":30}

    def set_capture(self):
        self.capture = cv2.VideoCapture(0, cv2.CAP_ANY)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.params.FRAME_WIDTH)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.params.FRAME_HEIGHT)
        self.capture.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3)
        self.capture.set(cv2.CAP_PROP_FPS, self.params.FRAME_RATE_TARGET)
        self.params.FRAME_RATE = self.capture.get(cv2.CAP_PROP_FPS)
        self.params.FRAME_RATE_SKIP = max(1, int(self.params.FRAME_RATE / self.params.FRAME_RATE_TARGET))
        self.cycle()

    def set_detector(self, model:str="", config:str="", score_threshold=0.9, nms_threshold=0.3, top_k=5000):
        if model == "":
            with open("config.json") as cfg:
                model = json.load(cfg)["detector_model_path"]
        input_size=(self.params.FRAME_WIDTH,self.params.FRAME_HEIGHT)
        self.detector = cv2.FaceDetectorYN.create(
            model, config, input_size, score_threshold, nms_threshold, top_k
        )

    def detect_face_locations(self, scale=0.25):
        img_h, img_w = self.current_frame.shape[:2]
        small_frame = cv2.resize(self.current_frame, (int(img_w * scale), int(img_h * scale)))
        self.detector.setInputSize((int(img_w * scale), int(img_h * scale)))
        faces = self.detector.detect(small_frame)[1]
        if faces is not None:
            locations = []
            for face in faces:
                x, y, w, h = face[0]/scale, face[1]/scale, face[2]/scale, face[3]/scale
                if x < 0 or y < 0 or x+w > img_w or y+h > img_h:
                    continue
                locations.append((int(x), int(y), int(w), int(h)))
            return locations
        return None

    def draw_face_box(self, location, label):
        x, y, w, h = location
        cv2.rectangle(self.current_frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
        cv2.rectangle(self.current_frame, (x, y), (x+w, y-35), (0, 0, 255), cv2.FILLED)
        cv2.putText(self.current_frame, label, (x, y), cv2.FONT_HERSHEY_DUPLEX, 1.25, (255, 255, 255), 1)

    def extract_encoded_face_crops(self, locations):
        return [self.encode_image(self.current_frame[y:y+h, x:x+w]).decode("latin-1") for (x,y,w,h) in locations]

    def encode_image(self, image):
        _, jpg_frame = cv2.imencode('.jpg', image)
        return jpg_frame.tobytes()

    def cycle(self):
        if self.capture is None:
            return (False, None)
        has_frame, frame = self.capture.read()
        if not has_frame:
            return (False, self.current_frame)
        if self.params.FRAME_COUNTER % self.params.FRAME_RATE_SKIP != 0:
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
                if isinstance(self.fm_client, bool):
                    return
                response = json.loads(await self.fm_client.recv())
                self.latest_fm_update = list(zip(response["locations"], response["labels"]))
            except Exception as e:
                print(f"FM response handler error: {e}")
                await asyncio.sleep(0)

global facemanager
global client
facemanager = None
client = Client()

app = fastapi.FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root(request: fastapi.Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/supported")
async def get_supported():
    return client.supported

@app.get("/facemanager_setup")
async def facemanager_setup(request: fastapi.Request, response: fastapi.Response, ip: str = "", port: str = ""):
    if client.params.FM_IP != "":
        return fastapi.responses.PlainTextResponse("Facemanager Connected")
    if ip == "" and port == "":
        try:
            facemanager = Popen(['python', 'facemanager.py'])
        except Exception as e:
            return fastapi.responses.PlainTextResponse(f"Error launching FaceManager: {e}", status_code=400)
        ip, port = "localhost", 9254
    else:
        try:
            if not re.match(r"^((?:\d{1,3}\.){3}\d{1,3}):(\d{1,5})$", f"{ip}:{port}"):
                raise Exception("IP/port invalid")
        except:
            return fastapi.responses.PlainTextResponse("IP and/or port Invalid", status_code=400)

    url = f"http://{ip}:{port}"
    try:
        for _ in range(30):  # Retry for ~15 seconds
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            client.params.FM_IP = f"{ip}:{port}"
                            client.fm_client = True
                            return fastapi.responses.PlainTextResponse("Facemanager Connected")
            except:
                await asyncio.sleep(0.5)
        raise Exception("Timeout")
    except Exception as e:
        response.status_code = 400
        return fastapi.responses.PlainTextResponse(f"Failed to connect to FaceManager: {e}")

@app.get("/database_setup")
async def database_setup(request: fastapi.Request, response: fastapi.Response):
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
        return fastapi.responses.PlainTextResponse(f"Exception: {e}", status_code=400)

@app.websocket("/ws/video_feed")
async def websocket_video(websocket: fastapi.WebSocket):
    await websocket.accept()
    query_params = parse_qs(websocket.url.query)
    width = int(query_params.get("width", [640])[0])
    height = int(query_params.get("height", [480])[0])
    fps_target = int(query_params.get("fps_target", [30])[0])
    identify = query_params.get("identify", ["false"])[0].lower() == "true"
    detect = query_params.get("detect", ["false"])[0].lower() == "true"

    client.params.FRAME_WIDTH = width
    client.params.FRAME_HEIGHT = height
    client.params.FRAME_RATE_TARGET = fps_target
    try:
        client.set_capture()
        if detect:
            client.set_detector()
        if identify and client.fm_client is not None:
            client.fm_client = await websockets.connect("ws://" + client.params.FM_IP + "/ws/identify")
            asyncio.create_task(client.fm_response_handler())
    except Exception as e:
        print(f"Video stream init error: {e}")

    try:
        while True:
            has_frame, _ = client.cycle()
            if not has_frame:
                continue

            if detect:
                locs = client.detect_face_locations()
                if locs:
                    if identify and client.fm_client is not None:
                        send = {"faces": client.extract_encoded_face_crops(locs), "locations": locs, "time": time.time()}
                        await client.fm_client.send(json.dumps(send))
                        if client.latest_fm_update:
                            for loc, label in client.latest_fm_update:
                                client.draw_face_box(loc, label)
                    else:
                        for loc in locs:
                            client.draw_face_box(loc, "?")

            await websocket.send_bytes(client.encode_image(client.current_frame))
            await asyncio.sleep(0)

    except Exception as e:
        print(f"Client Websocket Error at /ws/video_feed: {e}")
    finally:
        try:
            if client.fm_client is not None and not isinstance(client.fm_client, bool):
                await client.fm_client.close()
                client.fm_client = True
        except Exception as e:
            print(f"FM close error: {e}")
        if hasattr(client, "capture"):
            client.capture.release()
        try:
            await websocket.close()
        except Exception as e:
            print(f"WebSocket close error: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9253)



# # Don't redirect, make a GET request
# # Use javascript (fetch)
# # Have image tag point to video feed endpoint