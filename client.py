import asyncio #for making program asynchronous
import cv2 #OpenCV, computer vision library. TODO CPU ONLY!

import ttsmanager
import facemanager

class Client: #TODO make singleton
    class params:
        FRAME_WIDTH = 1280
        FRAME_HEIGHT = 720
        FRAME_FPS = 20
        FRAME_SKIP = 0
        FRAME_COUNTER = 0
        SCALE_FACTOR = .75  # Scale down for faster processing
        RETRY_TIMEOUT = 10
        DB_PATH = "C:/Users/Educa/Documents/GitHub/PVNET-FACIAL-RECOGNITION/Database/encodings.json"
        STOP_TIME = ["11:59", "12:59", "13:59", "14:59", "15:59", "16:59", "17:59"] #when client should shut down??? TODO remove this lol. If necessary make program self destruct after x time

    def __init__(self):
        self.face_manager = facemanager.FaceManager()
        self.tts_manager = ttsmanager.TTSManager()
        self.window = cv2.VideoCapture(0, cv2.CAP_ANY) #open video input(index 0), and auto detect input type(CAP_ANY)
        self.set_window()

    def __del__(self):
        del self.tts_manager
        self.window.release()
        cv2.destroyAllWindows()
        del self.face_manager

    @property
    def current_frame(self):
        has_frame, frame = self.window.read()
        return None if not has_frame else frame

    def set_window():
        self.window.set(cv2.CAP_PROP_FRAME_WIDTH, self.params.FRAME_WIDTH) #window width
        self.window.set(cv2.CAP_PROP_FRAME_HEIGHT, self.params.FRAME_HEIGHT) #window height
        self.window.set(cv2.CAP_PROP_FPS, self.params.FRAME_FPS) #window framerate
        self.window.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75) # set auto exposure factor TODO necessary?

    def draw_face_box(self, bounds, name):
        top = int(bounds[0] / self.params.SCALE_FACTOR)
        right = int(bounds[1] / self.params.SCALE_FACTOR)
        bottom = int(bounds[2] / self.params.SCALE_FACTOR)
        left = int(bounds[3] / self.params.SCALE_FACTOR)

        cv2.rectangle(self.current_frame, (left, top), (right, bottom), (0, 0, 255), 2)
        cv2.rectangle(self.current_frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
        font_scale = (bottom - top) / 150
        cv2.putText(self.current_frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, font_scale, (255, 255, 255), 1)

    async def cycle(self):
        if self.params.FRAME_COUNTER == self.params.FRAME_SKIP:
            self.params.FRAME_COUNTER = 0
            return
        self.params.FRAME_COUNTER += 1

        try:
            async with asyncio.timeout(self.params.RETRY_TIMEOUT):
                while self.current_frame is None:
                    set_window()
        except TimeoutError:
            print("Setting window timed out")

        small_frame = cv2.resize(self.current_frame, (0,0), fx=self.params.SCALE_FACTOR, fy=self.params.SCALE_FACTOR)#automatically scale down image by (fx, fy)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB) #convert frame from BGR to RGB TODO necessary?
        
        for face in await self.face_manager.find_faces(small_frame):
            for (top, right, bottom, left), name in (face.lo, face.name):
                self.draw_face_box((top, right, bottom, left), name)
        
        cv2.imshow('Video', self.current_frame) #display video input + changes to monitor


