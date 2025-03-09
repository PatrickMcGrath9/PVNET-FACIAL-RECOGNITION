import json #for serializing embeddings
import pyttsx3 #for the text to speech engine
import asyncio #for making program asynchronous

import threading #TODO remove? try to use async rather than threading
import queue #TODO remove? for communicating between threads
import cv2 #OpenCV, computer vision library. TODO CPU ONLY!

#import gzip #for compressing JSON file with encodings

class FaceHandler: #TODO make singleton
    class Face:
        def __init__(self, p_encoding, p_name, p_images):
            self.encoding = p_encoding
            self.name = p_name
            self.image = p_images #TODO if necessary

    faces = []

    def __init__():
        pass

    def __del__():
        pass

    def load_encodings():
        if os.path.exists(encodings_path):
            with open(encodings_path, "rt") as f:
                faces = json.load(f)
        else:
            faces = []

    def write_encodings():
        with open(encodings_path, 'wt') as file:
            file.write(json.dump(faces))

    def name_face(face:self.Face): #TODO give faces names. Can edit 'faces' directly or needs return?
        pass


class TTS: #TODO make singleton
    catchphrases = { #TODO load from file instead
        "Tiffany" : "borbnation will flourish.",
        "Patrick" : "slayer of bugnation.",
        "Tyler" : "ruler of the monkeys."
    }

    class params:
        SPEAK_INTERVAL = 300 # TODO ?
        UNKNOWN_SPEAK_INTERVAL = 60 # TODO ?
        DETECTION_TIME_REQUIRED = 0.3 # Time required for known faces, stops random objects being recognized as faces TODO necessary?
        UNKNOWN_DETECTION_TIME_REQUIRED = 0.75 # Time required for unknown faces, stops random objects being recongized as faces TODO necessary?

    def __init__(self):  
        self.engine = pyttsx3.init() #intialize TTS engine
        self.queue = queue.Queue()
        self.last_spoken_time = {} # TODO ?
        self.face_detection_time = {} #TODO ?
    
    def __del__(self): #TODO
        pass

    def speech_request(speech): #TODO
        pass


class Client: #TODO make singleton
    class params:
        FRAME_WIDTH = 1280
        FRAME_HEIGHT = 720
        FRAME_FPS = 30 #TODO reduce frame rate rather than frame skip?
        FRAME_SKIP = 2 #TODO ^?
        FRAME_COUNT = 0
        SCALE_FACTOR = .75  # Scale down for faster processing
        DB_PATH = "C:/Users/Educa/Documents/GitHub/PVNET-FACIAL-RECOGNITION/Database/encodings.json"
        STOP_TIME = ["11:59", "12:59", "13:59", "14:59", "15:59", "16:59", "17:59"] #when client should shut down??? TODO remove this lol. If necessary make program self destruct after x time

    def __init__(self):
        self.window = cv2.VideoCapture(0, cv2.CAP_ANY) #open video input(index 0), and auto detect input type(CAP_ANY)
        self.set_window()

    def __del__(self):
        del TTS.instance #TODO make TTS singleton
        self.window.release()
        cv2.destroyAllWindows()
        del FaceHandler.instance #TODO make FaceHandler singleton

    @property
    def current_frame(self):
        has_frame, frame = self.window.read()
        return None if not has_frame else frame

    def set_window():
        self.window.set(cv2.CAP_PROP_FRAME_WIDTH, self.params.FRAME_WIDTH) #window width
        self.window.set(cv2.CAP_PROP_FRAME_HEIGHT, self.params.FRAME_HEIGHT) #window height
        self.window.set(cv2.CAP_PROP_FPS, self.params.FRAME_FPS) #window framerate
        self.window.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75) # set auto exposure factor TODO necessary?

    def find_face_locations(frame): #TODO
        pass

    def encode_face(frame, face_location): #TODO
        pass

    def draw_face_box(self, bounds, name):
        top = int(top / scaling_factor)
        right = int(right / scaling_factor)
        bottom = int(bottom / scaling_factor)
        left = int(left / scaling_factor)

        cv2.rectangle(self.current_frame, (left, top), (right, bottom), (0, 0, 255), 2)
        cv2.rectangle(self.current_frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
        font_scale = (bottom - top) / 150
        cv2.putText(self.current_frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, font_scale, (255, 255, 255), 1)

    def cycle(self):
        if self.current_frame is None:
            #try set_window(), if failed loop trying again every 2 seconds for x amount of times
            pass

        small_frame = cv2.resize(self.current_frame, (0,0), fx=self.params.SCALE_FACTOR, fy=self.params.SCALE_FACTOR)#automatically scale down image by (fx, fy)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB) #convert frame from BGR to RGB TODO necessary?
        
        for face_location in await self.find_face_locations(small_frame): #TODO
            face = FaceHandler.Face(await self.encode_face(small_frame, face_location), None, None)
            FaceHandler.name_face(current_faces) #TODO make handler static
            for (top, right, bottom, left), name in (face_location, face.name):
                self.draw_face_box((top, right, bottom, left), name)
        
        cv2.imshow('Video', self.current_frame) #display video input + changes to monitor


