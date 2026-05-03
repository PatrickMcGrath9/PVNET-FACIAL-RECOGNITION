import cv2
from dataclasses import dataclass
from time import time, sleep as time_sleep
from threading import Lock
from src.data_collections import IdentificationDataCollection

def draw_face_box(image, location, label):
    if image is None:
        raise Exception("Image not set when trying to draw box")
    (x, y, w, h) = location #decompose location
    cv2.rectangle(image, (x, y), (x+w, y+h), (0, 0, 255), 2) #draw bounding box
    cv2.rectangle(image, (x, y), (x+w, y-35), (0, 0, 255), cv2.FILLED) #draw label box
    cv2.putText(image, label, (x + 5, max(0, y - 10)), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)

@dataclass
class Parameters():
    VIDEO_GAMMA:int = 0 #desired gamma for video (possibly 0-1000)
    VIDEO_CONTRAST:int = 0 #desired constrast for video (possibly 0-1000)
    FRAME_WIDTH:int = 0 #desired frame width
    FRAME_HEIGHT:int = 0 #desired frame height
    FRAME_RATE_TARGET:int = 0 #desired framerate
    FRAME_COUNTER:int = 0 #running counter of frame amts

class Camera():    
    def __init__(self, idx):
        try:
            self.parameters = Parameters()
            self.current_frame = None
            self.new_frame = False
            self.capture = None
            self.latest_identify_update:IdentificationDataCollection = None
            self.index = idx
            self.last_frame_time = 0
            self.video_backend_api = self.find_fastest_video_backend_api()
            self.supported = self.get_supported()
            self.get_default_video_values()
        except Exception as e:
            raise Exception(f"Failed initializing camera {idx}: {e}")

    def find_fastest_video_backend_api(self):
        try:
            if isinstance(self.index, str):
                return cv2.CAP_ANY
            min_time = -1
            best_api = None
            for api in cv2.videoio_registry.getCameraBackends() + (cv2.CAP_ANY,):
                start = time()
                cap = cv2.VideoCapture(self.index, api)
                if cap.isOpened():
                    time_taken = time()-start
                    if min_time == -1 or time_taken < min_time or api in [cv2.CAP_OBSENSOR]:
                        best_api = api
                        min_time = time_taken
                cap.release()
            return best_api if best_api is not None else cv2.CAP_ANY
        except Exception as e:
            print(f"Failed finding fastest video backend API for camera {self.index}: {e}")

    def get_supported(self):
        try:
            vid_cap = cv2.VideoCapture(self.index, self.video_backend_api)
            if not vid_cap.isOpened():
                raise Exception(f"Video capture not opened")
            # TODO tie camera to a unique identifier rather than index
            # settings_file = "camera_settings.json"
            # settings = {}
            # if os.path.exists(settings_file):
            #     with open(settings_file, 'r') as f:
            #         settings = load(f)
            #         if f"camera_{self.video_capture_index}" in settings:
            #             return settings[f"camera_{self.video_capture_index}"]

            supported = {"resolutions":[],"framerate":[]}
            vid_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1000000) #set to high value to later get max
            vid_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1000000) #set to high value to later get max
            start_w = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH)) #get the actual value
            start_h = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) #get the actual value
            print("Getting all supported resolutions, please wait...")
            for width in range(start_w, 0, -100): #increment down from the max
                for height in range(start_h, 0, -100): #increment down from the max
                    vid_cap.set(cv2.CAP_PROP_FRAME_WIDTH, width) #try setting the value
                    vid_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height) #try setting the value
                    temp_w = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH)) #get actual
                    temp_h = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) #get actual

                    width = temp_w if temp_w < width else width #if the current actual value is less than the last actual, store it (also effectively skips unnecessary decrementation)
                    height = temp_h if temp_h < height else height #if the current actual value is less than the last actual, store it (also effectively skips unnecessary decrementation)

                    if {"width":temp_w,"height":temp_h} not in supported["resolutions"]: #if the resolution is not in the list
                        supported["resolutions"].append({"width":temp_w,"height":temp_h}) #store it
            # TODO necessary if OpenCV's property is not reliable
            # print("Getting maximum supported framerate, please wait...")
            # for _ in range(10):
            #     vid_cap.read()

            # num_frames = 100
            # start = time()

            # for i in range(num_frames):
            #     ret, frame = vid_cap.read()

            # end = time()
            # seconds = end - start
            # max_framerate = int(num_frames / seconds)
            # supported["framerate"] = max_framerate #store it

            max_framerate = int(vid_cap.get(cv2.CAP_PROP_FPS))
            supported["framerate"] = max_framerate

            # TODO tie camera to unique identifier rather than index
            # settings[f"camera_{self.video_capture_index}"] = supported
            # with open(settings_file, 'w') as f:
            #     dump(settings, f, indent=1)
            if not supported["resolutions"]:
                raise Exception("No supported resolutions found")
            if not supported["framerate"]:
                raise Exception("No supported framerate found")
            return supported
        except Exception as e:
            raise Exception(f"Failed getting supported resolutions and framerate for camera {self.index}: {e}")
        finally:
            if vid_cap:
                vid_cap.release() #release video

    def get_default_video_values(self):
        try:
            vid_cap = cv2.VideoCapture(self.index, self.video_backend_api)
            self.parameters.FRAME_WIDTH, self.parameters.FRAME_HEIGHT = self.supported["resolutions"][0]["width"], self.supported["resolutions"][0]["height"]
            self.parameters.FRAME_RATE_TARGET = self.supported["framerate"]
            self.parameters.VIDEO_GAMMA = int(vid_cap.get(cv2.CAP_PROP_GAMMA))
            self.parameters.VIDEO_CONTRAST = int(vid_cap.get(cv2.CAP_PROP_CONTRAST))
            vid_cap.release()
        except Exception as e:
            print(f"Failed to get default video values for camera {self.index}: {e}")

    def get_capture(self):
        try:
            retries = 0
            while self.capture is not None and retries < 5:
                time_sleep(1)
                retries += 1
            if retries > 5:
                return
            vid_cap = cv2.VideoCapture(self.index, self.video_backend_api)
            vid_cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            vid_cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.parameters.FRAME_WIDTH) #set video width
            vid_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.parameters.FRAME_HEIGHT) #set video height
            vid_cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3)
            vid_cap.set(cv2.CAP_PROP_GAMMA, self.parameters.VIDEO_GAMMA)
            vid_cap.set(cv2.CAP_PROP_AUTO_WB, 1)
            vid_cap.set(cv2.CAP_PROP_CONTRAST, self.parameters.VIDEO_CONTRAST)
            vid_cap.set(cv2.CAP_PROP_FPS, self.parameters.FRAME_RATE_TARGET) #try and set target FPS
            self.parameters.FRAME_RATE = vid_cap.get(cv2.CAP_PROP_FPS) #retrieve actual FPS
            self.capture = vid_cap
        except Exception as e:
            print(f"Failed getting capture for camera {self.index}: {e}")

    def release_capture(self):
        try:
            if self.capture is not None:
                self.capture.release()
                self.capture = None
        except Exception as e:
            print(f"Error releasing capture for camera {self.index}: {e}")

    def get_latest_frame(self):
        try:
            if self.capture is None: #if capture is not set
                return False
            now = time()
            interval = 1.0 / max(1, self.parameters.FRAME_RATE_TARGET)

            if now - self.last_frame_time < interval:
                return False  # Too soon for next frame
                
            has_frame, frame = self.capture.read()
            if not has_frame:
                return False

            self.last_frame_time = now
            self.current_frame = frame
            self.new_frame = True
            return True
        except Exception as e:
            print(f"Error getting latest frame from camera {self.index}: {e}")

    def draw_identity_update(self):
        current_frame_copy = self.current_frame.copy()
        if self.latest_identify_update is not None:
            for identity in self.latest_identify_update.identities:
                draw_face_box(current_frame_copy, identity.location, identity.label)
        return current_frame_copy