import cv2 #OpenCV, computer vision library. TODO CPU ONLY!
import ttsmanager
import facemanager

class Client: #TODO make singleton
    class params:
        SHOW_LIVE_FEED = True #whether webcam should be shown, or just the faces as captured
        FRAME_WIDTH = 1280
        FRAME_HEIGHT = 720
        FRAME_FPS = 10 #may not work
        FRAME_SKIP = 1 #skip x frames, process x+1
        FRAME_COUNTER = 0
        RETRY_TIMEOUT = 10 #TODO used with async.timeout
        DB_PATH = "DB/encoding"
        STOP_TIME = ["11:59", "12:59", "13:59", "14:59", "15:59", "16:59", "17:59"] #when client should shut down??? TODO remove this lol. If necessary make program self destruct after x time

    def __init__(self):
        self.current_frame = None
        self.face_manager = facemanager.FaceManager() #TODO remove, instead query user on startup ip of facemanager
        #self.tts_manager = ttsmanager.TTSManager()
        self.window = cv2.VideoCapture(0, cv2.CAP_ANY) #open video input(index 0), and auto detect input type(CAP_ANY)
        self.set_window()

    def __del__(self):
        #del self.tts_manager
        self.window.release()
        cv2.destroyAllWindows()
        del self.face_manager

    def get_frame(self):
        has_frame, frame = self.window.read()
        self.current_frame =  None if not has_frame else frame

    def set_window(self):
        self.window.set(cv2.CAP_PROP_FRAME_WIDTH, self.params.FRAME_WIDTH) #window width
        self.window.set(cv2.CAP_PROP_FRAME_HEIGHT, self.params.FRAME_HEIGHT) #window height
        self.window.set(cv2.CAP_PROP_FPS, self.params.FRAME_FPS) #window framerate
        self.window.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3) # set auto exposure factor TODO necessary?

    def draw_face_box(self, location, name):
        (x, y, w, h) = location
        cv2.rectangle(self.current_frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
        cv2.rectangle(self.current_frame, (x, y), (x+w, y-35), (0, 0, 255), cv2.FILLED)
        cv2.putText(self.current_frame, name, (x, y), cv2.FONT_HERSHEY_DUPLEX, 1.25, (255, 255, 255), 1, bottomLeftOrigin=False)

    def show_face_crop(self, location):
        (x, y, w, h) = location
        cv2.imshow(f"{x} {y} {w} {h}", self.current_frame[y:y+h, x:x+w])

    def cycle(self):
        #apply frame skip
        if self.params.FRAME_COUNTER % self.params.FRAME_SKIP != 0:
            self.params.FRAME_COUNTER = 0
            return
        self.params.FRAME_COUNTER += 1
        
        self.get_frame()

        #signal face manager to find faces
        for face in self.face_manager.find_faces(self.current_frame):
            self.draw_face_box(face.location, face.name)
            if not self.params.SHOW_LIVE_FEED:
                self.show_face_crop(face.location) #TODO needs to be implemented better than just spam
            #do whatever else with the face identity, like tts
        
        if self.params.SHOW_LIVE_FEED:
            cv2.imshow('Video', self.current_frame) #display video input + changes to monitor
        cv2.waitKey(1)
        self.frame = None
        #TODO web ui that shows live feed AND most recent faces

if __name__ == "__main__":
    client = Client()
    while True:
        client.cycle()