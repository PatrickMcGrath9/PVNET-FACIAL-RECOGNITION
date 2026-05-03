from uvicorn import run
from fastapi import FastAPI, WebSocket, responses, Request
from json import loads, dumps
from asyncio import create_task, gather, to_thread, sleep as asyncio_sleep
from contextlib import asynccontextmanager
from threading import Thread
from cv2 import imencode
from src.camera_handler import CameraHandler
from src.data_collections import IdentificationDataCollection

camera_handler = CameraHandler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    task1 = create_task(camera_handler.cycle_cameras())
    task2 = create_task(camera_handler.detect())
    try:
        yield
    finally:
        task1.cancel()
        task2.cancel()
        try:
            await task1
            await task2
        except Exception:
            pass

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"camera_handler":"OK"}

@app.get("/cameras")
async def get_cameras():
    return list(camera_handler.cameras.keys())

@app.get("/initial_video_settings")
async def get_initial(camera_id:str):
    if camera_id != "all" and camera_id not in camera_handler.cameras:
        return {"error": "Invalid camera ID"}
    cameras = camera_handler.cameras.values()
    if camera_id == "all":
        common_framerates = set([c.supported['framerate'] for c in cameras])
        framerate = min(common_framerates) if common_framerates else 0

        
        all_resolutions = []
        for camera in cameras:
            all_resolutions.extend(camera.supported["resolutions"])
        
        common_resolutions = []
        for resolution in all_resolutions:
            if all([resolution in c.supported["resolutions"] for c in cameras]) and resolution not in common_resolutions:
                common_resolutions.append(resolution)

        return {"framerate":framerate,"resolutions":common_resolutions}

    camera = camera_handler.cameras[camera_id]
    return camera.supported | {"gamma":camera.parameters.VIDEO_GAMMA, "contrast":camera.parameters.VIDEO_CONTRAST}

@app.put("/update_camera")
async def update_camera(request:Request, camera_id:str):
    try:
        data = await request.json()
        if camera_id is not None and camera_id in camera_handler.cameras.keys():
            camera = camera_handler.cameras[camera_id]
            if "width" in data:
                camera.parameters.FRAME_WIDTH = int(data["width"])
            if "height" in data:
                camera.parameters.FRAME_HEIGHT = int(data["height"])
            if "fps_target" in data:
                camera.parameters.FRAME_RATE_TARGET = int(data["fps_target"])
            if "contrast" in data:
                camera.parameters.VIDEO_CONTRAST = int(data["contrast"])
            if "gamma" in data:
                camera.parameters.VIDEO_GAMMA = int(data["gamma"])
            camera.release_capture()
            camera.get_capture()
        elif camera_id is not None and camera_id == "all":
            for camera in camera_handler.cameras.values():
                if "width" in data:
                    camera.parameters.FRAME_WIDTH = int(data["width"])
                if "height" in data:
                    camera.parameters.FRAME_HEIGHT = int(data["height"])
                if "fps_target" in data:
                    camera.parameters.FRAME_RATE_TARGET = int(data["fps_target"])
                if "contrast" in data:
                    camera.parameters.VIDEO_CONTRAST = int(data["contrast"])
                if "gamma" in data:
                    camera.parameters.VIDEO_GAMMA = int(data["gamma"])
                camera.release_capture()
                camera.get_capture()
        return responses.JSONResponse({"success":"OK"})
    except Exception as e:
        return responses.JSONResponse({"error":f"Failed to update camera {camera_id}: {e}"}, status_code=400)

@app.websocket("/ws/update")
async def websocket_update(websocket: WebSocket):
    await websocket.accept()
    async def receiver():
        while True:
            try:
                data = loads(await websocket.receive_text())
                identification_collection = IdentificationDataCollection.from_dict(data=data)
                camera = camera_handler.cameras[identification_collection.camera_id]
                camera.latest_identify_update = identification_collection
            except Exception as e:
                raise Exception(f"Error while receiving update: {e}")

    async def sender():
        while True:
            try:
                update:IdentificationDataCollection = await camera_handler.identify_queue.get()
                await websocket.send_text(dumps({"identify":update.to_dict()}))
            except Exception as e:
                raise Exception(f"Error while sending update: {e}")

    try:
        await gather(receiver(), sender())
    except Exception as e:
        print(f"Error at CH /ws/update: {e}")
    finally:
        await websocket.close()

@app.websocket("/ws/video_feed")
async def websocket_video(websocket: WebSocket, camera_id):
    await websocket.accept() #wait for websocket connection to be accepted
    try:
        if camera_id != "all" and camera_id not in camera_handler.cameras:
            await websocket.close(code=1008, reason="Invalid camera ID")
            return
        if camera_id == "all":
            while True:
                await websocket.send_bytes(imencode(".jpg", camera_handler.make_image_grid())[1].tobytes()) #send the current frame (with updates if applicable)
                await asyncio_sleep(1/5) #limit update to 5fps for grid
        elif camera_id in camera_handler.cameras:
            camera = camera_handler.cameras[camera_id]
            while True:
                if camera.current_frame is not None:
                    await websocket.send_bytes(imencode(".jpg", camera.draw_identity_update())[1].tobytes()) #send the current frame (with updates if applicable)
                await asyncio_sleep(1/camera.parameters.FRAME_RATE_TARGET if camera.parameters.FRAME_RATE_TARGET >= 1 else 0)
    except Exception as e:
        print(f"Client Websocket Error at /ws/video_feed: {e}")
    finally:
        try:
            try:
                await websocket.close()
            except RuntimeError:
                pass  # websocket already closed
        except Exception as e:
            print(f"Exception during connection closing: {e}")

if __name__ == "__main__":
    run(app, host="0.0.0.0", port=9253)