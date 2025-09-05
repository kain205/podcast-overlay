import asyncio
import websockets
import ffmpeg
from asyncio.subprocess import PIPE

async def handler(ws):
    print('Client connected')
    
    process = await asyncio.create_subprocess_exec(
        'ffmpeg',
        '-i', 'pipe:0',
        '-f', 'wav', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
        'pipe:1',
        stdin=PIPE, stdout=PIPE, stderr=PIPE
    )

    try:
        transcribe_reader, transcribe_writer = await asyncio.open_connection(
            'localhost', 43007
        )
        print("Connected to transcription server.")
    except ConnectionRefusedError:
        print("Connection to transcription server failed.")
        process.kill()
        await process.wait()
        return

    #Client -> FFMPEG
    async def forward_to_ffmpeg():
        try:
            async for message in ws:
                process.stdin.write(message)
                await process.stdin.drain()
        except Exception as e:
            print(f'[FORWARDER] Error: {e}')
        finally:
            process.stdin.close()

    #FFMPEG -> Transcription Server 
    async def forward_to_transcriber():
        try:
            while not process.stdout.at_eof():
                wav_data = await process.stdout.read(4096)
                if not wav_data:
                    break
                transcribe_writer.write(wav_data)
                await transcribe_writer.drain()
        except Exception as e:
            print(f'[TRANSCRIBER_SENDER] Error: {e}')
        finally:
            transcribe_writer.close()
            # await transcribe_writer.wait_closed() 

    #Transcription Server -> Client 
    async def receive_from_transcriber():
        try:
            while not transcribe_reader.at_eof():
                result_bytes = await transcribe_reader.read(1024)
                if not result_bytes:
                    break
                result = result_bytes.decode('utf-8', errors='ignore')
                if result:
                    print("Transcription:", result)
                    await ws.send(result)
        except Exception as e:
            print(f'[TRANSCRIBER_RECEIVER] Error: {e}')
    
    await asyncio.gather(
        forward_to_ffmpeg(),
        forward_to_transcriber(),
        receive_from_transcriber()
    )

    # Dọn dẹp
    await transcribe_writer.wait_closed() 
    stdout, stderr = await process.communicate()
    print("FFMPEG exited with code:", process.returncode)
    if stderr:
        print("FFMPEG stderr output:", stderr.decode())
    print("Client disconnected")


async def main():
    async with websockets.serve(handler, "0.0.0.0", 8765):
        print("listening ws://localhost:8765")
        await asyncio.Future()

asyncio.run(main())