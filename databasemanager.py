import os
import json
import cv2
import numpy
import fastapi
import asyncio
import uvicorn
import time

from uuid import uuid4
from base64 import b64encode, b64decode
import sqlite3

class DatabaseManager:
    def __init__(self, db_path="facial_recognition.db", face_images_path="DB/faces"):
        self.face_images_path = face_images_path
        os.makedirs(self.face_images_path, exist_ok=True)
        
        self.db_connection = sqlite3.connect(db_path)
        cursor = self.db_connection.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS people (
            person_id TEXT PRIMARY KEY,
            label TEXT NOT NULL,
            encoding TEXT UNIQUE NOT NULL, -- as JSON string
            known BOOL NOT NULL
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS faces (
            person_id TEXT PRIMARY KEY,
            image_path TEXT UNIQUE NOT NULL
        )
        ''')
        self.db_connection.commit()
        self.db_update_event = asyncio.Event()
        self.db_update_event.set()           

    def save_new_unknown(self, id, cropped_face_image, encoding):
        # === Setup Data to Save ===
        image_path = os.path.join(self.face_images_path, f"{id}_{uuid4().hex}.jpg")
        cv2.imwrite(image_path, cropped_face_image)
        encoding_json = json.dumps(encoding)

        # === Save to DB ===
        cursor = self.db_connection.cursor()
        cursor.execute('''
        INSERT INTO people (person_id, label, encoding, known)
        VALUES (?, ?, ?, ?)
        ''',(id, "?", encoding_json, False))
        cursor.execute('''
        INSERT INTO faces (person_id, image_path)
        VALUES (?, ?)
        ''',(id, image_path))
        
        self.db_connection.commit()
        self.last_update_timestamp = time.time()

    def get_first_unknown(self):
        cursor = self.db_connection.cursor()

        # === Get ID ===
        cursor.execute('''
        SELECT person_id
        FROM people
        WHERE known=0
        ''')
        id = cursor.fetchone()[0]
        # === Get Image ===
        cursor.execute('''
        SELECT image_path
        FROM faces
        WHERE person_id = ?
        ''',(id,))
        path = cursor.fetchone()[0]
        image = cv2.imread(path)
        image = self.encode_image(image)
        # === Return Formatted JSON ===
        return {"id":id, "image":f"data:image/jpeg;base64,{image}"}

    @staticmethod
    def decode_image(image):
        '''
        Convert image from B64 string
        '''
        return cv2.imdecode(numpy.frombuffer(b64decode(image), dtype=numpy.uint8), cv2.IMREAD_COLOR)

    @staticmethod
    def encode_image(image):
        '''
        Convert image to B64 string
        '''
        return b64encode(cv2.imencode('.jpg', image)[1]).decode('utf-8')

    def get_encodings(self):
        cursor = self.db_connection.cursor()
        cursor.execute('''
        SELECT person_id, encoding
        FROM people   
        ''')
        return numpy.array([(res[0],res[1]) for res in cursor.fetchall()])

    def get_labels(self):
        cursor = self.db_connection.cursor()
        cursor.execute('''
        SELECT person_id, label
        FROM people   
        ''')
        return {res[0]:res[1] for res in cursor.fetchall()}

global database
database = DatabaseManager()
app = fastapi.FastAPI()

@app.get("/")
async def root():
    return fastapi.responses.PlainTextResponse("DatabaseManager is running.")

@app.websocket("/ws/identities")
async def identities(websocket: fastapi.WebSocket):
    await websocket.accept()

    async def receiver():
        while True:
            data = json.loads(await websocket.receive_text())
            database.save_new_unknown(data["id"], database.decode_image(data["face"]), data["encoding"])
            database.db_update_event.set()
    async def sender():
        while True:
            await database.db_update_event.wait()

            encodings = []
            for person_id, encoding_json in database.get_encodings():
                encoding = json.loads(encoding_json)  # turn JSON string into list
                encodings.append([person_id, encoding])
            
            labels = database.get_labels()


            await websocket.send_text(json.dumps({
                "encodings": encodings,
                "labels": labels
            }))
            database.db_update_event.clear()
    try:
        await asyncio.gather(receiver(), sender())
    except Exception as e:
        print(f"DB WebSocket error at /ws/identities: {e}")
    finally:
        await websocket.close()
        print("Client disconnected.")            

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

@app.get("/get_unknown")
async def audit_get(request: fastapi.Request, response: fastapi.Response):
    try:
        # Get one unknown from the database
        unknown = database.get_first_unknown()  # you need this helper
        return unknown  # will be returned as JSON
    except Exception as e:
        return {"error":str(e)}

@app.patch("/update_unknown")
async def update_unknown(request: fastapi.Request):
    print("!!")
    data = await request.json()
    person_id = data.get("id")
    new_label = data.get("label")

    if not person_id or not new_label:
        return fastapi.responses.JSONResponse({"error": "Missing 'id' or 'label'"}, status_code=400)

    cursor = database.db_connection.cursor()
    try:
        cursor.execute('''
            UPDATE people
            SET label = ?, known = 1
            WHERE person_id = ?
        ''', (new_label, person_id))
        database.db_connection.commit()
        print(person_id, new_label)
        return {"message": "Label updated successfully"}
    except Exception as e:
        return fastapi.responses.JSONResponse({"error": str(e)}, status_code=500)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9255)
