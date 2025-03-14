import asyncio
from client import Client

async def main():
    client = Client()
    print("Facial recognition system started. Press 'q' to quit.")

    while True:
        await client.cycle()
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    del client
    print("Facial recognition system terminated.")

if __name__ == "__main__":
    asyncio.run(main())
