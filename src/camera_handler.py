from uuid import uuid4
from time import time
from src.camera import Camera
from asyncio import to_thread, sleep as asyncio_sleep
from src.image_encoding import encode_image, decode_image
from json import load
from threading import Thread
from math import ceil, sqrt
from dataclasses import dataclass
from numpy import full, uint8, ndarray
from src.data_collections import IdentificationDataCollection, IdentificationData, ExpiringQueue
import cv2

class CameraHandler():
    def __init__(self):
        self.identify_queue = ExpiringQueue(max_age=0.1, maxsize=10)
        self.detect_queue = ExpiringQueue(max_age=0.1, maxsize=10)
        self.set_detector()
        self.cameras = {uuid4().hex:cam for cam in self.get_cameras() or []}

    def set_detector(self, model:str="", config:str="",score_threshold:float=0.8, nms_threshold:float=0.3, top_k:int=500):
        try:
            if model == "":
                with open("config.json") as cfg:
                    model = load(cfg)["detector_model_path"] #load the face detection model from config
            input_size = (0,0)
            self.detector = cv2.FaceDetectorYN.create( #create face detector
                model,
                config,
                input_size,
                score_threshold, #threshold to filter out bounding boxes of confidence smaller than
                nms_threshold, #threshold to suppress bounding boxes of IoU (intersection over union) [aka supress bounding boxes inside one another] bigger than
                top_k #	keep top K bounding boxes
            )
        except Exception as e:
            print(f"Failed to set detector: {e}")

    def get_cameras(self):
        try:
            available_devices = []
            index = 0
            failures = 0
            while failures < 5:
                cap = cv2.VideoCapture(index, cv2.CAP_ANY)
                if cap is not None and cap.isOpened():
                    print(f"Found video device at index: {index}")
                    cap.release()
                    available_devices.append(Camera(index))
                    failures = 0  # Reset failure counter on success
                else:
                    failures += 1
                cap.release()
                index += 1
            return available_devices
        except Exception as e:
            print(f"Failed to get cameras: {e}")

    def detect_face_locations(self, image, img_scale_factor = 1.0):
        try:
            if image is None:
                raise Exception("Image not set when trying to detect face locations")
            locations = []
            img_h, img_w = image.shape[:2] #get the current size of the image
            if img_scale_factor != 1.0: #if we want to change the scale of the image
                image = cv2.resize(image, (int(img_w * img_scale_factor), int(img_h * img_scale_factor))) #resize the image
                
            self.detector.setInputSize((int(img_w * img_scale_factor), int(img_h * img_scale_factor))) # update detector input size temporarily
            faces = self.detector.detect(image)[1] #detect faces, return locations
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
        except Exception as e:
            print(f"Failed to detect face locations: {e}")

    def make_image_grid(self):
        images = [camera.draw_identity_update() for camera in self.cameras.values() if camera.draw_identity_update() is not None] 
        if not images:
            return cv2.zeros((480, 640, 3), dtype=uint8)
        n = len(images)
        cols = int(ceil(sqrt(n)))
        rows = int(ceil(n / cols))
        h, w = images[0].shape[:2]
        target_dtype = images[0].dtype
        grid_h = rows * h + (rows - 1)
        grid_w = cols * w + (cols - 1)
        grid_image = full((grid_h, grid_w, 3), (0,0,0), dtype=target_dtype)

        # Paste each image into grid
        for idx, img in enumerate(images):
            if idx >= rows * cols:
                break

            # Resize image
            img_resized = cv2.resize(img, (w, h))

            row = idx // cols
            col = idx % cols
            y = row * h
            x = col * w

            grid_image[y:y+h, x:x+w] = img_resized
        return grid_image

    async def detect(self):
        while True:
            try:
                identification_collection:IdentificationDataCollection = await self.detect_queue.get()
                camera = self.cameras[identification_collection.camera_id]
                face_locations = await to_thread(self.detect_face_locations, identification_collection.frame)
                if len(face_locations) > 0:
                    identification_collection.set_data([IdentificationData(label="UNKNOWN", location=loc) for loc in face_locations])
                    identification_collection.set_face_crops()
                    identification_collection.frame = None
                    await self.identify_queue.put(identification_collection)
            except Exception as e:
                print(f"Client error when detect: {e}")
            await asyncio_sleep(0.0001)

    async def cycle_cameras(self):
        try:
            for camera in self.cameras.values():
                camera.get_capture()
            while True:
                for (camera_id, camera) in self.cameras.items():
                    try:
                        if camera.get_latest_frame():
                            await self.detect_queue.put(IdentificationDataCollection(frame=camera.current_frame, time=time(), camera_id=camera_id))
                    except Exception as e:
                        print(f"Error while cycling camera {camera_id}: {e}")
                    await asyncio_sleep(0.0001)
        finally:
            camera.release_capture()
