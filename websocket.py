import asyncio
import websockets

async def handler(ws):
    print('Client connected')
    async for message in ws:
        print('Received chunk, size:', len(message))
        # TODO: processing chunk here
    await ws.send('hj e')

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8765):
        print("listening ws://localhost:8765")
        await asyncio.Future()

asyncio.run(main())