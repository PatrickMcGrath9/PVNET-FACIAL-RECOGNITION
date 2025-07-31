import os
import json
import cv2
import numpy
import fastapi
import asyncio
import uvicorn
import time
import threading

from uuid import uuid4
from base64 import b64encode, b64decode
from contextlib import contextmanager
import sqlite3

class DatabaseManager:
    def __init__(self, db_path="DB/", face_images_path="faces/", db_file="facial_recognition.db"):
        self.db_path = db_path
        self.face_images_path = os.path.join(db_path, face_images_path)
        self.db_file_path = os.path.join(db_path, db_file)
        self._lock = threading.Lock()
        self.init_db()
        self.db_update_event = asyncio.Event()
        self.db_update_event.set()      

    @staticmethod
    def decode_image(image):
        return cv2.imdecode(numpy.frombuffer(b64decode(image), dtype=numpy.uint8), cv2.IMREAD_COLOR)

    @staticmethod
    def encode_image(image):
        return b64encode(cv2.imencode('.jpg', image)[1]).decode('utf-8')

    @contextmanager
    def get_cursor(self):
        with self._lock:
            conn = sqlite3.connect(self.db_file_path, timeout=60)
            cursor = conn.cursor()
            try:
                yield cursor
            finally:
                cursor.close()
                conn.commit()
                conn.close()

    def init_db(self):
        os.makedirs(self.db_path, exist_ok=True)
        os.makedirs(self.face_images_path, exist_ok=True)
        with self.get_cursor() as cursor:
            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS people (
                    person_id TEXT PRIMARY KEY,
                    label TEXT NOT NULL,
                    known BOOL NOT NULL
                )
                '''
            )
            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS encodings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    person_id TEXT NOT NULL,
                    encoding TEXT NOT NULL
                )
                '''
            )
            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS face_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    person_id TEXT NOT NULL,
                    image_path TEXT NOT NULL
                )
                '''
            )

    def get_encodings(self):
        with self.get_cursor() as cursor:
            cursor.execute('''SELECT person_id, encoding FROM encodings''')
            return cursor.fetchall()
    
    def get_labels(self):
        with self.get_cursor() as cursor:
            cursor.execute('''SELECT person_id, label FROM people''')
            return cursor.fetchall()

    def get_first_unknown(self):
        with self.get_cursor() as cursor:
            cursor.execute(
                '''
                SELECT person_id FROM people
                WHERE known = FALSE
                '''
            )
            result = cursor.fetchone()
            if result is None:
                raise Exception("No unknown faces available")
            id = result[0]
            cursor.execute(
                '''
                SELECT image_path FROM face_images
                WHERE person_id = ?
                ''',
                (id,)
            )
            path = cursor.fetchone()[0]
            image = self.encode_image(cv2.imread(path))
            return {"id": id, "image": f"data:image/jpeg;base64,{image}"}

    def get_known_labels(self):
        with self.get_cursor() as cursor:
            cursor.execute(
                '''
                SELECT person_id, label FROM people
                WHERE known = TRUE
                '''
            )
            return cursor.fetchall()

    def save_new_unknown(self, id, face_image, encoding):
        image_path = os.path.join(self.face_images_path, f"{id}_{uuid4().hex}.jpg")
        cv2.imwrite(image_path, face_image)
        encoding_json = json.dumps(encoding)
        with self.get_cursor() as cursor:
            cursor.execute(
                '''
                INSERT INTO people (person_id, label, known)
                VALUES (?,?,?)
                ''',
                (id, "?", False,)
            )
            cursor.execute(
                '''
                INSERT INTO encodings (person_id, encoding)
                VALUES (?,?)
                ''',
                (id, encoding_json,)
            )
            cursor.execute(
                '''
                INSERT INTO face_images (person_id, image_path)
                VALUES (?,?)
                ''',
                (id, image_path,)
            )
        self.db_update_event.set()

    def update_unknown(self, person_id, new_label):
        with self.get_cursor() as cursor:
            cursor.execute(
                '''
                UPDATE people
                SET label = ?, known = TRUE
                WHERE person_id = ?
                ''',
                (new_label, person_id,)
            )
        self.db_update_event.set()

    def transfer_person_info(self, old_id, new_id):
        with self.get_cursor() as cursor:
            cursor.execute(
                '''
                UPDATE encodings
                SET person_id = ?
                WHERE person_id = ?
                ''',
                (new_id, old_id,)
            )
            cursor.execute(
                '''
                UPDATE face_images
                SET person_id = ?
                WHERE person_id = ?
                ''',
                (new_id, old_id,)
            )
            cursor.execute('''DELETE FROM people WHERE person_id = ?''', (old_id,))
            cursor.execute('''DELETE FROM encodings WHERE person_id = ?''', (old_id,))
            cursor.execute('''DELETE FROM face_images WHERE person_id = ?''', (old_id,))
        self.db_update_event.set()

global database
database = DatabaseManager()
app = fastapi.FastAPI()

@app.get("/")
async def root():
    return fastapi.responses.JSONResponse({"success":"DatabaseManager is running."})

@app.websocket("/ws/identities")
async def identities(websocket: fastapi.WebSocket):
    await websocket.accept()
    async def receiver():
        while True:
            data = json.loads(await websocket.receive_text())
            database.save_new_unknown(data["id"], database.decode_image(data["face_image"]), data["encoding"])
    async def sender():
        while True:
            await database.db_update_event.wait()
            await websocket.send_text(json.dumps({
                "encodings": database.get_encodings(),
                "labels": database.get_labels()
            }))
            database.db_update_event.clear()
    try:
        await asyncio.gather(receiver(), sender())
    except Exception as e:
        print(f"DB WebSocket error at /ws/identities: {e}")
    finally:
        await websocket.close()
        print("Client disconnected.")

@app.get("/audit/labels")
async def get_known_labels():
    return database.get_known_labels()
    
@app.get("/unknown")
async def audit_get():
    try:
        return database.get_first_unknown()
    except Exception as e:
        return fastapi.responses.JSONResponse({"error":"Error getting unknown/No unknowns left"}, status_code=400)

@app.patch("/unknown")
async def update_unknown(request: fastapi.Request):
    try:
        data = await request.json()
        person_id = data.get("id")
        new_label = data.get("label")
        if person_id and new_label:
            database.update_unknown(person_id, new_label)
            return fastapi.responses.JSONResponse({"success":"OK"})
        old_id = data.get("old_id")
        new_id = data.get("new_id")
        if old_id and new_id:
            database.transfer_person_info(old_id, new_id)
            return fastapi.responses.JSONResponse({"success":"OK"})
        response.status_code = 400
        return fastapi.responses.JSONResponse({"error":"'id' and 'label' necessary for updating unknown or 'old_id' and 'new_id' necessary for transfer"}, status_code=400)
    except Exception as e:
        return fastapi.responses.JSONResponse({"error":f"Error updating unknown: {e}"}, status_code=400)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9255)