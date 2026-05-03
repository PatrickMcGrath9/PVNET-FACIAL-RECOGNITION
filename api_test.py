import aiohttp
import asyncio
import time

central_ip = "http://localhost:8000"

async def add_handler(handler_type,ip):
    async with aiohttp.ClientSession() as session:
        async with session.put(central_ip+"/handlers", json={"handler_type":handler_type, "ip":ip}) as resp:
            print(await resp.json())

async def get_cameras():
    async with aiohttp.ClientSession() as session:
        async with session.get(central_ip+"/video_feed/cameras") as resp:
            print(await resp.json())

asyncio.run(add_handler("camera_handler","localhost:9253"))
time.sleep(1)
asyncio.run(add_handler("processing_handler","localhost:9254"))