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
import numpy as np

class DatabaseManager:
    def __init__(self, faces_dir="DB/faces", id_to_label_path="DB/id_to_label.json"):
        self.faces_dir = faces_dir
        self.id_to_label_path = id_to_label_path

        os.makedirs(self.faces_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.id_to_label_path), exist_ok=True)

        self._create_id_to_label_file()

    def _create_id_to_label_file(self):
        if not os.path.exists(self.id_to_label_path):
            with open(self.id_to_label_path, "w") as f:
                json.dump({}, f, indent=2)

    def load_all_faces(self):
        faces_encodings = {}

        for folder in os.listdir(self.faces_dir):
            folder_path = os.path.join(self.faces_dir, folder)
            if not os.path.isdir(folder_path):
                continue

            json_path = os.path.join(folder_path, "encoding.json")
            if not os.path.exists(json_path):
                print(f"Warning: Missing encoding file in {folder_path}, skipping")
                continue

            with open(json_path, "r") as f:
                enc_list = json.load(f)
                faces_encodings[folder] = [np.array(e) for e in enc_list]

        return faces_encodings

    def save_new_unknown(self, folder, cropped_face_image, encoding):
        folder_path = os.path.join(self.faces_dir, folder)
        os.makedirs(folder_path, exist_ok=True)

        img_path = os.path.join(folder_path, f"{folder}.jpg")
        cv2.imwrite(img_path, cropped_face_image)

        json_path = os.path.join(folder_path, "encoding.json")
        with open(json_path, "w") as f:
            json.dump([encoding.tolist()], f, indent=2)
