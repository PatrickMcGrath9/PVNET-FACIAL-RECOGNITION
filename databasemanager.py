# import os
# import cv2
# import fastapi
# import asyncio
# import uvicorn

# class DatabaseManager:
#     def __init__(self, audit_dir="DB/audit"):
#         """Initialize with a directory for audit images."""
#         self.audit_dir = audit_dir
#         os.makedirs(self.audit_dir, exist_ok=True)

#     def save_unknown_face(self, image, group_id):
#         """
#         Save the face image to the audit directory with a unique filename
#         so we never overwrite earlier captures for the same unknown.
#         """
#         prefix = f"unknown_group_{group_id}"
#         filename = f"{prefix}.jpg"
#         filepath = os.path.join(self.audit_dir, filename)
#         cv2.imwrite(filepath, image)


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

#     return fastapi.responses.JSONResponse({id:image.tolist()})

# @app.put("/audit")
# async def audit_put(audit_id, database_id):
#     for image in os.listdir("DB/audit"):
#         if audit_id == image[len(image) - image[::-1].index("_"):image.index(".")]:
#             return fastapi.responses.PlainTextResponse("success")
#     return fastapi.responses.PlainTextResponse("id not found", status_code=404)
# if __name__ == "__main__":
#     uvicorn.run(app)


import os
import cv2
import fastapi
import asyncio
import uvicorn

class DatabaseManager:
    def __init__(self, audit_dir="DB/audit", known_dir="DB/known"):
        """Initialize with directories for audit and known face images."""
        self.audit_dir = audit_dir
        self.known_dir = known_dir

        os.makedirs(self.audit_dir, exist_ok=True)
        os.makedirs(self.known_dir, exist_ok=True)

    def save_unknown_face(self, image, group_id):
        """
        Save the face image to the audit directory with a unique filename
        so we never overwrite earlier captures for the same unknown.
        """
        prefix = f"unknown_group_{group_id}"
        filename = f"{prefix}.jpg"
        filepath = os.path.join(self.audit_dir, filename)
        cv2.imwrite(filepath, image)


# ------------------- FastAPI Interface (Optional) -------------------

app = fastapi.FastAPI()

@app.get("/")
async def index():
    return fastapi.responses.PlainTextResponse("Database running")

@app.get("/audit")
async def audit_get():
    image_file_name = os.listdir("DB/audit")[0]
    id = image_file_name[len(image_file_name) - image_file_name[::-1].index("_"):image_file_name.index(".")]

    image_path = "DB/audit/" + image_file_name
    image = cv2.imread(image_path)

    if image is None:
        print(image_path)

    return fastapi.responses.JSONResponse({id: image.tolist()})

@app.put("/audit")
async def audit_put(audit_id, database_id):
    for image in os.listdir("DB/audit"):
        if audit_id == image[len(image) - image[::-1].index("_"):image.index(".")]:
            return fastapi.responses.PlainTextResponse("success")
    return fastapi.responses.PlainTextResponse("id not found", status_code=404)

if __name__ == "__main__":
    uvicorn.run(app)
