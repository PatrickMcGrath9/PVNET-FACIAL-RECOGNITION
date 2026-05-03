from fastapi import FastAPI, WebSocket
from uvicorn import run
from json import loads, dumps
from time import time
from threading import Thread
from asyncio import gather, to_thread, create_task
from numpy import array, linalg, float32
from contextlib import asynccontextmanager
from src.processing_handler import ProcessingHandler
from src.data_collections import IdentificationDataCollection, IdentityCollection

processing_handler = ProcessingHandler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = create_task(processing_handler.identify_faces())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except Exception:
            pass

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"processing_handler":"OK"}

@app.websocket("/ws/update")
async def update(websocket: WebSocket):
    await websocket.accept()
    async def receiver():
        while True:
            try:
                data = loads(await websocket.receive_text())
                if "identities" in data:
                    print("Got identities from database!")
                    async with processing_handler._identities_lock:
                        processing_handler.identity_collection.update(IdentityCollection.get_collection_for_update(data["identities"]))
                        processing_handler.calculate_dynamic_tolerances()
                if "identify" in data:
                    print("Got data to be identified from central!")
                    identity_collection = IdentificationDataCollection.from_dict(data["identify"])
                    await processing_handler.identify_queue.put(identity_collection)
            except Exception as e:
                raise Exception(f"Error while receiving update: {e}")

    async def sender():
        while True:
            try:
                update = await processing_handler.update_queue.get()
                await websocket.send_text(dumps(update))
                print("Sending back data to central!")
            except Exception as e:
                raise Exception(f"Error while sending update: {e}")
            
    try:
        await gather(receiver(), sender())
    except Exception as e:
        print(f"Error at PH /ws/update: {e}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    run(app, host="0.0.0.0", port=9254)