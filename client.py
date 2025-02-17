import asyncio
import websockets
import tkinter as tk
import json
import subprocess

SERVER_IP = "127.0.0.1"  #! Quest 2 PC's IP

async def send_command(command):
    async with websockets.connect(f"ws://{SERVER_IP}:8765") as websocket:
        await websocket.send(json.dumps({"command": command}))
        response = await websocket.recv()
        print("Response:", json.loads(response))

def start_stream():
    asyncio.run(send_command("start_stream"))

def stop_stream():
    asyncio.run(send_command("stop_stream"))

def start_recording():
    asyncio.run(send_command("start_recording"))

def stop_recording():
    asyncio.run(send_command("stop_recording"))

def toggle_webcam():
    asyncio.run(send_command("toggle_webcam"))

def toggle_microphone():
    asyncio.run(send_command("toggle_microphone"))

# Create GUI
root = tk.Tk()
root.title("Remote Oculus Quest 2 Control")

buttons = [
    ("Start Streaming", start_stream),
    ("Stop Streaming", stop_stream),
    ("Start Recording", start_recording),
    ("Stop Recording", stop_recording),
    ("Turn On/Off Webcam", toggle_webcam),
    ("Turn On/Off Microphone", toggle_microphone)
]

for text, cmd in buttons:
    tk.Button(root, text=text, command=cmd, width=20, height=2).pack(pady=10)

root.mainloop()