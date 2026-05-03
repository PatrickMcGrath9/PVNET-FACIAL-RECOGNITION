from src.image_encoding import decode_image, encode_image, decode_ndarray, encode_ndarray
from contextlib import contextmanager
from threading import Lock
from sqlite3 import connect
from numpy import mean, array, ndarray
from asyncio import Event
from json import loads, dumps, load
from collections import deque
from uuid import uuid4
from cv2 import imwrite, imread
from src.data_collections import Identity, IdentityCollection
import os

class DatabaseHandler:
    def __init__(self):
        self._lock = Lock()
        self.read_config()
        self.init_db()
        self.recents = deque(maxlen=10)
        self.db_update_event = Event()

    def read_config(self, config_file='config.json'):
        with open(config_file, 'r') as f:
            config = load(f)

        self.db_path = os.path.abspath(config['db_path'])
        self.db_file_path = os.path.join(self.db_path, config['db_file_path'])
        self.face_images_path = os.path.join(self.db_path, config['face_images_path'])

    @contextmanager
    def get_cursor(self):
        with self._lock:
            conn = connect(self.db_file_path, timeout=60)
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
                    encoding_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    person_id TEXT NOT NULL,
                    encoding TEXT NOT NULL,
                    relevant_image_id TEXT NOT NULL
                )
                '''
            )

            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS face_images (
                    image_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    person_id TEXT NOT NULL,
                    image_path TEXT NOT NULL
                )
                '''
            )
    
    def get_identities(self):
        with self.get_cursor() as cursor:
            cursor.execute(
                '''
                SELECT people.person_id, people.label, encodings.encoding
                FROM people
                JOIN encodings ON people.person_id = encodings.person_id 
                '''
            )
            identities:IdentityCollection = IdentityCollection()
            for (person_id, label, encoding_b64) in cursor.fetchall():
                try:
                    identities.put(Identity.from_db(person_id=person_id, encoding_b64=encoding_b64, label=label))
                except Exception as e:
                    print(f"Failure getting identities: {e}")
            return identities

    def get_unknowns(self):
        with self.get_cursor() as cursor:
            cursor.execute(
                '''
                SELECT people.person_id, face_images.image_path
                FROM people
                JOIN face_images ON people.person_id = face_images.person_id
                WHERE NOT people.known
                '''
            )
            return [{"id":person_id, "image":f"data:image/jpeg;base64,{encode_image(imread(path))}"} for (person_id,path) in cursor.fetchall()]
    
    def get_known_labels(self):
        with self.get_cursor() as cursor:
            cursor.execute(
                '''
                SELECT person_id, label FROM people
                WHERE known = TRUE
                '''
            )
            return cursor.fetchall()

    def save_new_unknown(self, person_id:str, face_image:ndarray, encoding:ndarray):
        with self.get_cursor() as cursor:
            try:
                cursor.execute(
                    '''
                    INSERT INTO people (person_id, label, known)
                    VALUES (?,?,?)
                    ''',
                    (person_id, "UNKNOWN", False,)
                )
            except:
                return
        image_path = os.path.join(self.face_images_path, f"{person_id}_{uuid4().hex}.jpg")
        imwrite(image_path, face_image)
        encoding_b64 = encode_ndarray(encoding)
        with self.get_cursor() as cursor:
            cursor.execute(
                '''
                INSERT INTO face_images (person_id, image_path)
                VALUES (?,?)
                ''',
                (person_id, image_path,)
            )
            cursor.execute(
                '''
                INSERT INTO encodings (person_id, encoding, relevant_image_id)
                VALUES (?,?,?)
                ''',
                (person_id, encoding_b64,cursor.lastrowid,)
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
        self.remove_identity(old_id, transfer=True)
        self.db_update_event.set()
    
    def remove_identity(self, person_id, transfer:bool=False):
        with self.get_cursor() as cursor:
            if not transfer:
                cursor.execute('SELECT image_path FROM face_images WHERE person_id = ?', (person_id,))
                image_paths = cursor.fetchall()
                for (path,) in image_paths:
                    if os.path.exists(path):
                        os.remove(path)

                cursor.execute('''DELETE FROM encodings WHERE person_id = ?''', (person_id,))
                cursor.execute('''DELETE FROM face_images WHERE person_id = ?''', (person_id,))
                cursor.execute('''DELETE FROM people WHERE person_id = ?''', (person_id,))
            else:
                cursor.execute('''DELETE FROM people WHERE person_id = ?''', (person_id,))
        self.db_update_event.set()