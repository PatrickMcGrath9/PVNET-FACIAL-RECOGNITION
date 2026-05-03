from src.image_encoding import encode_image, decode_image
from asyncio import to_thread, gather, Lock
from collections import deque
from cv2 import dnn
from numpy import float32, array, linalg, dot, std, mean, stack
from uuid import uuid4
from onnxruntime import InferenceSession, preload_dlls
from json import load
from dataclasses import dataclass
from src.data_collections import IdentificationDataCollection, Identity, IdentityCollection, ExpiringQueue

@dataclass
class Parameters:
    ENCODING_MATCH_TOLERANCE: float = 0.6
    ENCODING_MATCH_TOLERANCE_MINIMUM: float = 0.1
    ENCODING_STD_TOLERANCE:float = 0.2
    ENCODING_STD_TOLERANCE_MINIMUM:float = 0.1
    ENCODING_STD_CUTOFF:float = 0.05

    IDENTIFIER_INPUT_SIZE:tuple[int,int] = (0,0)
    IDENTIFIER_NAME: str = ""

class ProcessingHandler():
    def __init__(self):
        self.parameters = Parameters()
        self._identities_lock = Lock()
        self.identity_collection:IdentityCollection = IdentityCollection()
        self.update_queue = ExpiringQueue(max_age=0.1, maxsize=10)
        self.identify_queue = ExpiringQueue(max_age=0.1, maxsize=10)
        self.set_identifier() #initialize face identifier model
        self.recent_faces = deque(maxlen=20)

    def set_identifier(self, model: str = ""):
        if model == "":
            with open("config.json") as cfg:
                model = load(cfg)["identifier_model_path"]
        preload_dlls()
        execution_providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        self.identifier = InferenceSession(model, providers=execution_providers)        
        print(f"Using execution provider: {self.identifier.get_providers()[0]}")
        input_meta = self.identifier.get_inputs()[0]
        self.parameters.IDENTIFIER_INPUT_SIZE = tuple(input_meta.shape[2:])
        self.parameters.IDENTIFIER_NAME = input_meta.name
            
    async def identify_faces(self):
        def identify_face(face_crop):
            '''
            Identify face from crop using a trained model of captured, labeled, & audited faces. Returns a Face object of who was identified.
            '''
            pass #TODO

        def find_best_match(encoding):
            if len(self.identity_collection.identities) < 1:
                return (None, encoding)

            max_similarity = -100
            best_match_id = None
            max_similarity = max(dot(encoding, known) for known in [identity.encoding for identity in self.identity_collection.identities.values()])
            similarities = []
            print("Similarities:")
            for person_id in self.identity_collection.identities.keys():
                known_encoding = self.identity_collection.identities[person_id].encoding

                similarity = dot(encoding, known_encoding)
                similarities.append(similarity)
                print(similarity)
                if similarity > max_similarity:
                    max_similarity = similarity
                    best_match_id = person_id

            similarity_std = -1
            if len(similarities) > 1:
                similarity_std = std(similarities)
                print("Max Similarity:", max_similarity, "| Identity:", self.identity_collection.identities[best_match_id].label, "Deviation:", similarity_std)
            
            
            if max_similarity > self.parameters.ENCODING_MATCH_TOLERANCE:
                if similarity_std > self.parameters.ENCODING_STD_TOLERANCE:
                    print("Confident match")
                    return (True, best_match_id)  # Confident match
                else:
                    print("High similarity, but too similar to too many, not confident")
                    return (False, None)  # Too similar to too many, uncertain
            else:
                if similarity_std < self.parameters.ENCODING_STD_CUTOFF:  # <0.05 or something very tight
                    print("Low similarity, but too similar to too many, not confident")
                    return (False, None)  # Everything was close but low quality
                print("Confident new person")
                return (None, encoding)  # Truly novel

        def identify_face_fallback(face_crop):
            """
            Process multiple faces in a single inference call
            """
            try:
                if face_crop is None or face_crop.size == 0:
                    raise ValueError("Empty face crop")    

                blob = dnn.blobFromImage(image=face_crop, size=self.parameters.IDENTIFIER_INPUT_SIZE, swapRB=True)  # Convert to blob
                input_name = self.parameters.IDENTIFIER_NAME  # Get the input layer name of the model
                outputs = self.identifier.run(None, {input_name: blob})
                encoding = outputs[0]
                encoding = encoding.squeeze()
                norm_val = linalg.norm(encoding)
                if norm_val == 0:
                    raise ValueError("encoding norm is zero, invalid encoding")
                encoding /= norm_val 
                
                if len(self.identity_collection.identities) < 1:
                    return (None, encoding)

                return find_best_match(encoding=encoding)
            except Exception as e:
                print(f"failed to identify face crop: {e}")

        while True:
            try:
                identification_collection:IdentificationDataCollection = await self.identify_queue.get()

                async with self._identities_lock:
                    #TODO: run the trained NN first, then on fail use encoding fall back

                    results = await gather(
                        *[to_thread(identify_face_fallback, face_crop) for face_crop in identification_collection.get_face_crops()]
                    )

                    identity_updates:IdentityCollection = IdentityCollection()
                    for identification_data, (confidence, val) in zip(identification_collection.identities, results):
                        if confidence is True:
                            person_id = val
                            identification_data.label = self.identity_collection.identities[person_id].label
                        elif confidence is None:
                            new_id = uuid4().hex
                            encoding = val
                            self.identity_collection.put(Identity(person_id=new_id, encoding=encoding)) #identity w/o image to save on memory
                            identity_updates.put(Identity(person_id=new_id, encoding=encoding, image=identification_data.image)) #identity w/ image to send to db
                        identification_data.image = None

                update = {}
                update["identify"] = identification_collection.to_dict()
                if len(identity_updates.identities) > 0:
                    update["new_identities"] = identity_updates.to_list()
                print("Sending off update")
                await self.update_queue.put(update)
            except Exception as e:
                print(f"Error while identifying faces: {e}")
                return

    def calculate_dynamic_tolerances(self):
        similarities = []
        ids = list(self.identity_collection.identities.keys())

        for person_id in ids:
            enc1 = self.identity_collection.identities[person_id].encoding
            for other_person_id in ids:
                if person_id == other_person_id:
                    continue
                enc2 = self.identity_collection.identities[other_person_id].encoding
                similarity = dot(enc1, enc2)
                similarities.append(similarity)

        mean_sim = mean(similarities)
        std_sim = std(similarities)
        print("Proposed new similarity tolerance:", mean_sim - 2.5 * std_sim)
        print("Proposed new deviation tolerance:", std_sim * 0.75)
        self.parameters.ENCODING_MATCH_TOLERANCE = max(mean_sim - 2.5 * std_sim, self.parameters.ENCODING_MATCH_TOLERANCE_MINIMUM)
        self.parameters.ENCODING_STD_TOLERANCE = max(std_sim * 0.75, self.parameters.ENCODING_STD_TOLERANCE_MINIMUM)
        print(f"New Cosine Similarity Tolerance: {self.parameters.ENCODING_MATCH_TOLERANCE}, new Deviation Tolerance: {self.parameters.ENCODING_STD_TOLERANCE}")
        input()

