import asyncio  # for making program asynchronous
import cv2  # OpenCV, computer vision library. TODO CPU ONLY!

import ttsmanager
import facemanager

class Client:  # TODO make singleton
    class params:
        FRAME_WIDTH = 1280
        FRAME_HEIGHT = 720
        FRAME_FPS = 20
        FRAME_SKIP = 0
        FRAME_COUNTER = 0
        SCALE_FACTOR = 0.75  # Scale down for faster processing
        RETRY_TIMEOUT = 10
        DB_PATH = "encodings.json"

    def __init__(self):
        self.face_manager = facemanager.FaceManager()
        self.tts_manager = ttsmanager.TTSManager()
        self.window = cv2.VideoCapture(0, cv2.CAP_ANY)  # open video input (index 0), and auto detect input type (CAP_ANY)
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

    def set_window(self):
        self.window.set(cv2.CAP_PROP_FRAME_WIDTH, self.params.FRAME_WIDTH)  # window width
        self.window.set(cv2.CAP_PROP_FRAME_HEIGHT, self.params.FRAME_HEIGHT)  # window height
        self.window.set(cv2.CAP_PROP_FPS, self.params.FRAME_FPS)  # window framerate

    def draw_face_box(self, bounds, name):
        top, right, bottom, left = bounds
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
                    self.set_window()
        except TimeoutError:
            print("Setting window timed out")

        small_frame = cv2.resize(self.current_frame, (0, 0), fx=self.params.SCALE_FACTOR, fy=self.params.SCALE_FACTOR)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        async for face, name in self.face_manager.find_faces(rgb_small_frame):
            self.draw_face_box(face, name)
            await self.tts_manager.request_speak(f"Hello, {name}!")

        cv2.imshow('Video', self.current_frame)

