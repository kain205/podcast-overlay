# websocket.py (đã sửa đổi)
import asyncio
import websockets
import ffmpeg
from asyncio.subprocess import PIPE

# --- THAY ĐỔI 1: Tạo một "danh bạ" global cho các client ---
CONNECTED_CLIENTS = set()

async def handler(ws):
    # --- THAY ĐỔI 2: Thêm client vào danh bạ khi kết nối ---
    CONNECTED_CLIENTS.add(ws)
    print(f'New client connected. Total clients: {len(CONNECTED_CLIENTS)}')
    
    try:
        process = await asyncio.create_subprocess_exec(
            'ffmpeg',
            '-i', 'pipe:0',
            '-f', 'wav', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
            'pipe:1',
            stdin=PIPE, stdout=PIPE, stderr=PIPE
        )

        try:
            transcribe_reader, transcribe_writer = await asyncio.open_connection(
                'localhost', 43007 # Đảm bảo port này đúng với server SimulStreaming
            )
            print("Connected to transcription server.")
        except ConnectionRefusedError:
            print("Connection to transcription server failed.")
            process.kill()
            await process.wait()
            return

        async def forward_to_ffmpeg():
            try:
                # Vòng lặp này sẽ chỉ nhận audio từ client nào thực sự gửi
                async for message in ws:
                    process.stdin.write(message)
                    await process.stdin.drain()
            except websockets.exceptions.ConnectionClosedError:
                # Client ngắt kết nối là bình thường, không cần báo lỗi
                pass
            except Exception as e:
                print(f'[FORWARDER] Error: {e}')
            finally:
                if not process.stdin.is_closing():
                    process.stdin.close()

        async def forward_to_transcriber():
            try:
                while not process.stdout.at_eof():
                    wav_data = await process.stdout.read(4096)
                    if not wav_data: break
                    transcribe_writer.write(wav_data)
                    await transcribe_writer.drain()
            except Exception as e:
                print(f'[TRANSCRIBER_SENDER] Error: {e}')
            finally:
                if not transcribe_writer.is_closing():
                    transcribe_writer.close()

        async def receive_from_transcriber():
            try:
                while not transcribe_reader.at_eof():
                    result_bytes = await transcribe_reader.read(1024)
                    if not result_bytes: break
                    result = result_bytes.decode('utf-8', errors='ignore')
                    if result:
                        print("Transcription:", result)
                        # --- THAY ĐỔI 3: Gửi kết quả cho TẤT CẢ client ---
                        websockets.broadcast(CONNECTED_CLIENTS, result)
            except Exception as e:
                print(f'[TRANSCRIBER_RECEIVER] Error: {e}')
        
        await asyncio.gather(
            forward_to_ffmpeg(),
            forward_to_transcriber(),
            receive_from_transcriber()
        )

        await transcribe_writer.wait_closed() 
        stdout, stderr = await process.communicate()
        print("FFMPEG exited with code:", process.returncode)
        if stderr:
            print("FFMPEG stderr output:", stderr.decode())
        print(f"Handler for a client finished.")

    finally:
        # --- THAY ĐỔI 4: Xóa client khỏi danh bạ khi ngắt kết nối ---
        CONNECTED_CLIENTS.remove(ws)
        print(f'Client disconnected. Total clients: {len(CONNECTED_CLIENTS)}')


async def main():
    async with websockets.serve(handler, "0.0.0.0", 8765):
        print("listening ws://localhost:8765")
        await asyncio.Future()

asyncio.run(main())