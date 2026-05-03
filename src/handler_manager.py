from asyncio import create_task
from aiohttp import ClientSession, WSMsgType
from json import loads, dumps
from random import choice
from uuid import uuid4
from src.database_handler import DatabaseHandler
from src.image_encoding import decode_image
from src.data_collections import Identity, IdentityCollection, IdentificationDataCollection

class HandlerManager:
    camera_handlers = {} #{id:{"ip":...,"ws":...}..}
    processing_handlers = {}#{id:{"ip":...,"ws":...}..}
    database_handler = DatabaseHandler()
    session = None

    async def add_handler(self, handler_type, ip):
        new_id = uuid4().hex
        if self.session is None:
            self.session = ClientSession()
        ws = await self.session.ws_connect(f"ws://{ip}/ws/update")
        if handler_type == "camera_handler":
            self.camera_handlers[new_id] = {"ip":ip, "ws":ws}
        elif handler_type == "processing_handler":
            self.processing_handlers[new_id] = {"ip":ip, "ws":ws}
            db_identity_collection = self.database_handler.get_identities()
            if len(db_identity_collection.identities)>0:
                await ws.send_str(dumps({"identities":db_identity_collection.to_list()}))
        else:
            raise Exception("Invalid handler type")
        create_task(self.ws_listener(new_id, handler_type, ws))

    async def remove_handler(self, handler_id):
        if handler_id in self.camera_handlers:
            handler = self.camera_handlers[handler_id]
            await handler["ws"].close()
            del handler
        elif handler_id in self.processing_handlers:
            handler = self.processing_handlers[handler_id]
            await handler["ws"].close()
            del handler
        else:
            print(f"Handler ID {handler_id} not found.")
            return

    async def send_to_handler(self, handler_id, data:dict):
        try:
            handler_collection = self.camera_handlers if handler_id in self.camera_handlers else self.processing_handlers if handler_id in self.processing_handlers else None
            if handler_collection is None:
                raise Exception(f"Invalid handler ID")
            handler = handler_collection.get(handler_id)
            if not handler:
                raise Exception(f"Couldn't get handler by ID {id}")
            ws = handler["ws"]
            await ws.send_str(dumps(data))
        except Exception as e:
            print(f"Error sending to handler: {e}")

    async def ws_listener(self, handler_id, handler_type, ws):
        print(f"Starting listener for {handler_id}")

        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    data = loads(msg.data)
                    if handler_type == "camera_handler":
                        if "identify" in data:
                            if len(self.processing_handlers) > 0:
                                identify:IdentificationDataCollection = IdentificationDataCollection.from_dict(data["identify"])
                                identify.camera_handler_id = handler_id
                                data["identify"] = identify.to_dict()
                                random_processing_handler_id = choice(list(self.processing_handlers.keys()))
                                await self.send_to_handler(random_processing_handler_id, data)
                            else:
                                pass
                        if "identify" not in data:
                            raise Exception("Invalid data sent from camera handler")
                    elif handler_type == "processing_handler":
                        if "identify" in data:
                            identify:IdentificationDataCollection = IdentificationDataCollection.from_dict(data["identify"])
                            camera_handler_id = identify.camera_handler_id
                            await self.send_to_handler(camera_handler_id, data["identify"])
                        if "new_identities" in data:
                            print("got new identities")
                            for new_identity in IdentityCollection.from_list(data["new_identities"]).identities.values():
                                self.database_handler.save_new_unknown(new_identity.person_id, new_identity.image, new_identity.encoding)
                        if "identify" not in data and "new_identities" not in data:
                            raise Exception("Invalid data sent from processing handler")

        except Exception as e:
            print(f"Error during websocket listening for {handler_id}: {e}")
        finally:
            await self.remove_handler(handler_id)

    async def db_update_sender(self):
        while True:
            await self.database_handler.db_update_event.wait()
            print("update event")
            db_identity_collection:IdentityCollection = self.database_handler.get_identities()
            print("got identities")
            if len(db_identity_collection.identities)>0:
                print("more than 0")
                for handler_id in self.processing_handlers.keys():
                    print("SENT IDENTITIES TO", handler_id)
                    await self.send_to_handler(handler_id, {"identities":db_identity_collection.to_list()})
            self.database_handler.db_update_event.clear()