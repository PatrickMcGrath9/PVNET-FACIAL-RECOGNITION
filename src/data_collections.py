from asyncio import Queue
from json import loads, dumps
from time import time
from src.image_encoding import encode_image, decode_image, encode_ndarray, decode_ndarray

import numpy

class Identity:
    def __init__(self, person_id:str, encoding:numpy.ndarray, label:str="UNKNOWN", image:numpy.ndarray=None):
        self.person_id:str = person_id
        norm_val = numpy.linalg.norm(encoding)
        if not numpy.isclose(norm_val, 1.0):
            encoding /= norm_val
        self.encoding:numpy.ndarray = encoding
        self.label:str = label
        self.image:numpy.ndarray=image

    def to_dict(self):
        try:
            dct = {
                "person_id":self.person_id,
                "label":self.label,
                "encoding":encode_ndarray(self.encoding)
            }
            if self.image is not None:
                dct["image"] = encode_image(self.image)
            return dct
        except Exception as e:
            print(f"Error creating 'dict' from 'Identity' object: {e}")

    @classmethod
    def from_dict(cls, data:dict):
        try:
            person_id = data.get("person_id")
            if not isinstance(person_id, str):
                raise ValueError("Invalid or missing 'person_id' in dictionary")
            
            encoding = decode_ndarray(data.get("encoding"),dtype=numpy.float32)
            if not isinstance(encoding, numpy.ndarray):
                raise ValueError("Invalid or missing 'encoding' in dictionary")

            label = data.get("label")
            if not isinstance(label, str) and label is not None:
                raise ValueError("Invalid 'label' in dictionary")

            image_data = data.get("image")
            image = None
            if image_data:
                image = decode_image(image_data)
            if not isinstance(image, numpy.ndarray) and image is not None:
                raise ValueError("Invalid 'image' in dictionary")

            return cls(person_id=person_id, encoding=encoding, label=label, image=image)
        except Exception as e:
            print(f"Error creating 'Identity' object from 'dict': {e}")

    @classmethod
    def from_db(cls, person_id:str, encoding_b64:str, label:str):
        try:
            return cls(person_id=person_id, encoding=decode_ndarray(encoding_b64, dtype=numpy.float32), label=label)
        except Exception as e:
            print(f"Error creating 'Identity' object from database data: {e}")

class IdentityCollection:
    def __init__(self, identities:dict[str, Identity]=None):
        self.identities:dict[str, Identity] = identities if identities is not None else {}

    def put(self, identity:Identity):
        try:
            if identity.person_id in self.identities:
                self.identities[identity.person_id].encoding = numpy.mean((self.identities[identity.person_id].encoding, identity.encoding), axis=0)
            else:
                self.identities[identity.person_id] = identity
        except Exception as e:
            print(f"Error putting 'Identity' into 'IdentityCollection': {e}")

    def update(self, new_collection:list[Identity]):
        try:
            self.identities = {identity.person_id:identity for identity in new_collection}
        except Exception as e:
            print(f"Error updating 'IdentityCollection.identities': {e}")

    def to_list(self):
        try:
            return [identity.to_dict() for identity in self.identities.values()]
        except Exception as e:
            print(f"Error creating 'list' from 'IdentityCollection': {e}")

    @classmethod
    def from_list(cls, data:list[dict]):
        try:
            identities:dict[str, Identity] = {}
            for identity_dict in data:
                identity = Identity.from_dict(identity_dict)
                identities[identity.person_id] = identity
            return cls(identities=identities)
        except Exception as e:
            print(f"Error creating 'IdentityCollection' object from 'list': {e}")

    @staticmethod
    def get_collection_for_update(data:list[dict]):
        try:
            new_collection:list[Identity] = []
            for identity_dict in data:
                new_collection.append(Identity.from_dict(identity_dict))
            return new_collection
        except Exception as e:
            print(f"Error getting collection for updating another 'IdentityCollection': {e}")

class IdentificationData:
    def __init__(self, label:str, location:tuple[int,int,int,int], image:numpy.ndarray=None):
        self.location:tuple[int,int,int,int] = location
        self.label:str = label
        self.image:numpy.ndarray=image

    def to_dict(self):
        try:
            dct = {
                "location":self.location,
                "label":self.label
            }
            if self.image is not None:
                dct["image"] = encode_image(self.image)
            return dct
        except Exception as e:
            print(f"Error creating 'dict' from 'IdentificationData': {e}")

    @classmethod
    def from_dict(cls, data: dict):
        try:
            label = data.get("label")
            if not isinstance(label, str):
                raise ValueError("Invalid or missing 'label' in dictionary")

            location = data.get("location")
            if not (isinstance(location, (list, tuple)) and len(location) == 4 and all(isinstance(x, int) for x in location)):
                raise ValueError("Invalid or missing 'location' in dictionary")

            image_data = data.get("image")
            image = None
            if image_data:
                image = decode_image(image_data)

            return cls(label=label, location=tuple(location), image=image)
        except Exception as e:
            print(f"Error creating 'IdentificationData' object from 'dict': {e}")

    def set_face_crop(self, frame:numpy.ndarray):
        try:
            (x,y,w,h) = self.location
            self.image:numpy.ndarray=frame[y:y+h, x:x+w]
        except Exception as e:
            print(f"Error setting image of 'IdentificationData': {e}")

class IdentificationDataCollection:
    def __init__(self, time:float, camera_id:str, identities:list[IdentificationData]=None, frame:numpy.ndarray=None, camera_handler_id:str=None):
        self.frame:numpy.ndarray = frame
        self.identities:list[IdentificationData] = identities
        self.time:float = time
        self.camera_id:str = camera_id
        self.camera_handler_id:str = camera_handler_id

    def to_dict(self):
        try:
            dct = {
                "time":self.time,
                "camera_id":self.camera_id,
                "identities":[identity.to_dict() for identity in self.identities]
            }
            if self.frame is not None:
                dct["frame"] = encode_image(self.frame)
            if self.camera_handler_id is not None:
                dct["camera_handler_id"] = self.camera_handler_id
            return dct
        except Exception as e:
            print(f"Error creating 'dict' from 'IdentificationDataCollection': {e}")

    @classmethod
    def from_dict(cls, data:dict):
        try:
            camera_handler_id = data.get("camera_handler_id")
            if not isinstance(camera_handler_id, str) and camera_handler_id is not None:
                raise ValueError("Invalid or missing 'camera_handler_id' in dictionary")

            camera_id = data.get("camera_id")
            if not isinstance(camera_id, str):
                raise ValueError("Invalid or missing 'camera_id' in dictionary")

            time = data.get("time")
            if not isinstance(time, float):
                raise ValueError("Invalid or missing 'time' in dictionary")

            identities = [IdentificationData.from_dict(identity) for identity in data.get("identities")]
            if not isinstance(identities, list) and not all(isinstance(identity, IdentificationData) for identity in identities):
                raise ValueError("Invalid or missing 'identities' in dictionary")

            frame_data = data.get("frame")
            frame = None
            if frame_data:
                frame = decode_image(frame_data)
            if not isinstance(frame, numpy.ndarray) and frame is not None:
                raise ValueError("Invalid 'frame' in dictionary")

            return cls(time=time, camera_id=camera_id, identities=identities, frame=frame, camera_handler_id=camera_handler_id)
        except Exception as e:
            print(f"Error creating 'IdentificationDataCollection' from 'dict':{e}")

    def get_face_crops(self):
        try:
            return [identity.image for identity in self.identities]
        except Exception as e:
            print(f"Error getting face crops from 'IdentificationDataCollection': {e}")

    def set_data(self, new_data:list[IdentificationData]):
        self.identities = new_data

    def set_face_crops(self):
        for identity in self.identities:
            identity.set_face_crop(frame=self.frame)

class ExpiringQueue(Queue):
    def __init__(self, max_age: float, maxsize=0):
        super().__init__(maxsize=maxsize)
        self.max_age = max_age

    async def put(self, item):
        # Optionally clean old items before adding
        await self._remove_old_items()
        if super().full():
            await super().get()
        await super().put({"put_item":item, "put_time":time()})

    async def get(self):
        await self._remove_old_items()
        item = await super().get()
        return item["put_item"]

    async def _remove_old_items(self):
        items = []
        while not self.empty():
            item = await super().get()
            if time() - item["put_time"] <= self.max_age:
                items.append(item)
        for item in items:
            await super().put(item)