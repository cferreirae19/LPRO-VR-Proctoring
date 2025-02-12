import asyncio
import websockets
import tkinter as tk
import json
import subprocess

SERVER_IP = "192.168.1.129"  #! Quest 2 PC's IP

async def send_command(command):
    async with websockets.connect(f"ws://{SERVER_IP}:8765") as websocket:
        await websocket.send(json.dumps({"command": command}))
        response = await websocket.recv()
        print("Response:", json.loads(response))

def start_stream():
    asyncio.run(send_command("start_stream"))

def stop_stream():
    asyncio.run(send_command("stop_stream"))

def toggle_webcam():
    asyncio.run(send_command("toggle_webcam"))

def toggle_microphone():
    asyncio.run(send_command("toggle_microphone"))
    
def view_quest2():
    subprocess.Popen(["vlc", f"rtsp://{SERVER_IP}:8554/quest2"])

def view_webcam():
    subprocess.Popen(["vlc", f"rtsp://{SERVER_IP}:8554/webcam"])

def listen_microphone():
    subprocess.Popen(["vlc", f"rtsp://{SERVER_IP}:8554/microphone"])

# Create GUI
root = tk.Tk()
root.title("Remote Oculus Quest 2 Control")

buttons = [
    ("Start Streaming", start_stream),
    ("Stop Streaming", stop_stream),
    ("Turn On/Off Webcam", toggle_webcam),
    ("Turn On/Off Microphone", toggle_microphone),
    ("View Quest 2 Stream", view_quest2),
    ("View Webcam Stream", view_webcam),
    ("Listen to Microphone", listen_microphone)
]

for text, cmd in buttons:
    tk.Button(root, text=text, command=cmd, width=25, height=2).pack(pady=5)

root.mainloop()