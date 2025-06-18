# import os
# import cv2
# import fastapi
# import asyncio
# import uvicorn

# class DatabaseManager:
#     def __init__(self, audit_dir="DB/audit", known_dir="DB/known"):
#         """Initialize with directories for audit and known face images."""
#         self.audit_dir = audit_dir
#         self.known_dir = known_dir

#         os.makedirs(self.audit_dir, exist_ok=True)
#         os.makedirs(self.known_dir, exist_ok=True)

#     def save_unknown_face(self, image, group_id):
#         """
#         Save the face image to the audit directory with a unique filename
#         so we never overwrite earlier captures for the same unknown.
#         """
#         prefix = f"unknown_group_{group_id}"
#         filename = f"{prefix}.jpg"
#         filepath = os.path.join(self.audit_dir, filename)
#         cv2.imwrite(filepath, image)


# # ------------------- FastAPI Interface (Optional) -------------------

# app = fastapi.FastAPI()

# @app.get("/")
# async def index():
#     return fastapi.responses.PlainTextResponse("Database running")

# @app.get("/audit")
# async def audit_get():
#     image_file_name = os.listdir("DB/audit")[0]
#     id = image_file_name[len(image_file_name) - image_file_name[::-1].index("_"):image_file_name.index(".")]

#     image_path = "DB/audit/" + image_file_name
#     image = cv2.imread(image_path)

#     if image is None:
#         print(image_path)

#     return fastapi.responses.JSONResponse({id: image.tolist()})

# @app.put("/audit")
# async def audit_put(audit_id, database_id):
#     for image in os.listdir("DB/audit"):
#         if audit_id == image[len(image) - image[::-1].index("_"):image.index(".")]:
#             return fastapi.responses.PlainTextResponse("success")
#     return fastapi.responses.PlainTextResponse("id not found", status_code=404)

# if __name__ == "__main__":
#     uvicorn.run(app)

import os
import json
import cv2
import numpy
import fastapi
import asyncio
import uvicorn
import time

class DatabaseManager:
    def __init__(self, faces_dir="DB/faces", id_to_label_path="DB/id_to_label.json"):
        self.faces_dir = faces_dir
        self.id_to_label_path = id_to_label_path

        self.id_to_label = {}
        self.id_to_encoding = {}
        self.read_labels()
        self.read_encodings()        
        self.last_update_timestamp = time.time()

        

    def read_labels(self):
        if not os.path.exists(self.id_to_label_path):
            self.id_to_label = {}
            with open(self.id_to_label_path, "w") as f:
                json.dump({},f)
        else:
            with open(self.id_to_label_path, "r") as f:
                self.id_to_label = json.load(f)

    def read_encodings(self):
        if not os.path.exists(self.faces_dir):
            os.makedirs(self.faces_dir, exist_ok=True)

        for id in os.listdir(self.faces_dir):
            path = os.path.join(self.faces_dir, id)
            if not os.path.isdir(path):
                continue
            
            encoding_json = os.path.join(path, "encoding.json")
            if not os.path.exists(encoding_json):
                continue

            with open(encoding_json, "r") as f:
                if id.startswith("!_"):
                    id = id[2:]
                self.id_to_encoding[id] = json.load(f)

    def save_new_unknown(self, id, cropped_face_image, encoding):
        self.id_to_encoding[id] = encoding
        self.id_to_label[id] = "?"

        folder_path = os.path.join(self.faces_dir, "!_"+id)
        os.makedirs(folder_path, exist_ok=True)

        # onlyfiles = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f)) and os.path.join(folder_path, f).endswith(".jpg")]
        # for each in onlyfiles:
        #     print(each)

        lastindex = ""
        folder_path = os.path.join(self.faces_dir, "!_"+id)
        onlyjpgs = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f)) and f.endswith(".jpg")]
        if len(onlyjpgs) > 0:
            onlyjpgs.sort()
            lastindex = ''.join(char for char in onlyjpgs[-1] if char.isdigit())

        img_path = os.path.join(folder_path, f"face{lastindex}.jpg")
        cv2.imwrite(img_path, cropped_face_image)

        json_path = os.path.join(folder_path, "encoding.json")
        with open(json_path, "w") as f:
            json.dump([encoding], f, indent=2)

        with open(self.id_to_label_path, "w") as f:
            json.dump(self.id_to_label, f)

        self.last_update_timestamp = time.time()

global database
database = DatabaseManager()
app = fastapi.FastAPI()

@app.get("/")
async def root():
    return fastapi.responses.PlainTextResponse("DatabaseManager is running.")

@app.get("/identities")
async def get_identities(request:fastapi.Request):
    data = await request.json()
    if data["timestamp"] != database.last_update_timestamp:
        return fastapi.responses.JSONResponse({"encodings":database.id_to_encoding,"labels":database.id_to_label,"timestamp":database.last_update_timestamp})
    else:
        return fastapi.responses.Response(status_code=204)

@app.patch("/identities")
async def add_identity(request:fastapi.Request):
    data = await request.json()
    database.save_new_unknown(data["id"], numpy.array(data["face"], dtype='uint8'), data["encoding"])
    database.last_update_timestamp = time.time()
    return fastapi.responses.PlainTextResponse("Added identity")

@app.get("/database_setup")
async def database_setup(request:fastapi.Request,response:fastapi.Response,ip:str="",port:str=""):
    '''
    Called to setup the database, can accept two optional URL parameters:
        ip: the IP of a remote FaceManager that is already launched
        port: the port that the FaceManager is accepting requests to
    '''
    if ip == "": #if no IP specified
        try:
            database = Popen(['python', 'databasemanager.py'])
        except Exception as e:
            return fastapi.responses.PlainTextResponse(f"There was an issue with launching database locally:{e}", status_code=400)
        ip = "127.0.0.1" #set IP to localhost
        port = 9255
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
                        if resp.status == 200:
                            start = -1
                            facemanager.params.DATABASE_IP = url
            except Exception as e:
                pass
        if start != -1:
            raise Exception("Connection timed out")
    except Exception as e:
        response.status_code = 400
        return fastapi.responses.PlainTextResponse(f"There was an issue connecting to database:{e}")
    client.db_client = aiohttp.ClientSession()
    return fastapi.responses.PlainTextResponse("Database Connected")

if __name__ == "__main__":
    uvicorn.run(app, port=9255)
