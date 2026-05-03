from fastapi import FastAPI, Request, responses, WebSocket
from uuid import uuid4
from websockets import connect
from aiohttp import ClientSession, WSMsgType
from uvicorn import run
from asyncio import Lock, create_task
from contextlib import asynccontextmanager
from src.handler_manager import HandlerManager

# === WebUI ===
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

'''
Central API that routes traffic around the Facial Recognition system, houses the WebUI
'''

handler_manager = HandlerManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = create_task(handler_manager.db_update_sender())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except Exception:
            pass

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "cameras":await get_cameras()}) #TODO pass all ids of cameras

@app.get("/video_feed/cameras")
async def get_cameras():
    '''
    returns [{handler_id1:[camera_id1,...],{handler_id2:[camera_id1,...]}}]
    '''
    try:
        cameras = {}
        camera_handler_ids = list(handler_manager.camera_handlers.keys())
        for id in camera_handler_ids:
            async with ClientSession() as session:
                async with session.get("http://"+handler_manager.camera_handlers[id]["ip"]+f"/cameras") as resp:
                    cameras.update({id:await resp.json()})
        print(cameras)
        return cameras
    except Exception as e:
        return responses.JSONResponse({"error":f"Error getting cameras: {e}"}, status_code=400)

@app.get("/video_feed/initial_video_settings")
async def get_initial(request: Request, handler_id, camera_id):
    try:
        if handler_id is None or camera_id is None:
            raise Exception("Handler and camera ID needed")
        if handler_id not in handler_manager.camera_handlers:
            raise Exception("Invalid handler ID")
        camera_handler_ip = handler_manager.camera_handlers[handler_id]["ip"]
        if camera_handler_ip is None:
            raise Exception(f"Couldn't get IP of {handler_id}")
        async with ClientSession() as session:
            async with session.get("http://"+camera_handler_ip+f"/initial_video_settings?camera_id={camera_id}") as resp:
                return await resp.json()
    except Exception as e:
        return responses.JSONResponse({"error":f"Error getting initial settings: {e}"}, status_code=400)

@app.put("/video_feed/update_camera")
async def update_camera(request: Request, handler_id, camera_id):
    try:
        if handler_id is None or camera_id is None:
            raise Exception("Handler and camera ID needed")
        if handler_id not in handler_manager.camera_handlers:
            raise Exception("Invalid handler ID")
        data = await request.json()
        camera_handler_ip = handler_manager.camera_handlers[handler_id]["ip"]
        if camera_handler_ip is None:
            raise Exception(f"Couldn't get IP of {handler_id}")
        async with ClientSession() as session:
            async with session.put("http://"+camera_handler_ip+f"/update_camera?camera_id={camera_id}",json=data) as resp:
                return await resp.json()
    except Exception as e:
        return responses.JSONResponse({"error":f"Error getting initial settings: {e}"}, status_code=400)

@app.websocket("/video_feed")
async def ws_video_feed(websocket: WebSocket, handler_id, camera_id):
    await websocket.accept()
    try:
        if handler_id is None or camera_id is None:
            raise Exception("Handler and camera ID needed")
        if handler_id not in handler_manager.camera_handlers:
            raise Exception("Invalid handler ID")
        handler_ip = handler_manager.camera_handlers[handler_id]["ip"]
        if handler_ip is None:
            raise Exception(f"Couldn't get IP of {handler_id}")
        async with ClientSession() as session:
            async with session.ws_connect(f"ws://{handler_ip}/ws/video_feed?camera_id={camera_id}") as ws:
                async for msg in ws:
                    if msg.type == WSMsgType.BINARY:
                        await websocket.send_bytes(msg.data)
    except Exception as e:
        print(f"Error at /video_feed websocket: {e}")

@app.get("/recents")
async def get_recents():
    return list(handler_manager.database_handler.recent_faces)

@app.get("/audit")
async def audit_page(request: Request):
    return templates.TemplateResponse("auditor.html", {"request": request, "unknowns":handler_manager.database_handler.get_unknowns()})

@app.get("/audit/known_labels")
async def get_known_labels():
    return handler_manager.database_handler.get_known_labels()

@app.patch("/audit/unknowns")
async def update_unknown(request: Request):
    try:
        data = await request.json()
        if "delete" in data.keys():
            person_id = data.get("id")
            handler_manager.database_handler.remove_identity(person_id)
        person_id = data.get("id")
        new_label = data.get("label")
        if person_id and new_label:
            handler_manager.database_handler.update_unknown(person_id, new_label)
            return responses.JSONResponse({"success":"OK"})
        old_id = data.get("old_id")
        new_id = data.get("new_id")
        if old_id and new_id:
            print("transfer")
            handler_manager.database_handler.transfer_person_info(old_id, new_id)
            return responses.JSONResponse({"success":"OK"})
        raise Exception("'id' and 'label' necessary for updating unknown or 'old_id' and 'new_id' necessary for transfer")
    except Exception as e:
        return responses.JSONResponse({"error":f"Error updating unknown: {e}"}, status_code=400)

@app.put("/handlers")
async def add_handler(request: Request):
    try:
        new_ip = None
        data = await request.json()
        if "handler_type" in data and "ip" in data:
            async with ClientSession() as session:
                async with session.get("http://"+data["ip"]) as resp:
                    if resp.status == 200:
                        r = await resp.json()
                        if data["handler_type"] in r:
                            new_ip = data["ip"]
            if new_ip != None:
                await handler_manager.add_handler(data["handler_type"], new_ip)
                return {"success":"OK"}
    except Exception as e:
        return responses.JSONResponse({"error":f"Failed to add handler: {e}"}, status_code=400)

@app.delete("/handlers")
async def remove_camera_handler(request: Request):
    try:
        data = await request.json()
        if "id" in data:
            await handler_manager.remove_handler(data["id"])
            return {"success":"OK"}
        raise Exception("Invalid ID")
    except Exception as e:
        return responses.JSONResponse({"error":f"Failed to remove handler: {e}"}, status_code=400)


if __name__ == "__main__":      
    run(app, host="0.0.0.0", port=8000)


                # async with connect("ws://"+client.params.FM_IP+"/ws/identify") as updater:
                #     async def receiver():
                #         while True:
                #             msg = await updater.recv()
                #             data = loads(msg)
                #             self.latest_fm_update = list(zip(data["locations"], data["labels"]))
                #     async def sender():
                #         while True:
                #             identity = await self.identify_queue.get()
                #             await updater.send(identity)
                #     await gather(receiver(), sender())