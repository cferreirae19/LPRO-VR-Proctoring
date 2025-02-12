import asyncio
import subprocess
import websockets
import json
import datetime
import cv2
import pyaudio
import threading

# Initialize global variables
scrcpy_process = None
ffmpeg_process = None
webcam_process = None
rtsp_process = None
mic_process = None
is_recording = False
is_streaming = False
is_webcam_on = False
is_microphone_on = False

SERVER_IP = "192.168.1.129"

# Function to start streaming
def start_stream():
    global scrcpy_process, rtsp_process, is_streaming
    if not is_streaming:
        scrcpy_process = subprocess.Popen(["scrcpy", "--max-fps=30", "--video-bit-rate=8M"])
        
        # Start RTSP streaming using FFmpeg
        rtsp_process = subprocess.Popen([
            "ffmpeg", "-f", "gdigrab", "-i", "title=Quest 2",
            "-r", "30", "-c:v", "libx264", "-preset", "ultrafast",
            "-f", "rtsp", f"rtsp://{SERVER_IP}:8554/quest2"
        ])
        
        is_streaming = True
        print("Streaming started")

# Function to toggle webcam
def toggle_webcam():
    global is_webcam_on, webcam_process

    if is_webcam_on:
        is_webcam_on = False
        print("Webcam turned off.")
    else:
        is_webcam_on = True
        webcam_process = subprocess.Popen([
            "ffmpeg", "-f", "vfwcap", "-i", "0", "-r", "30",
            "-c:v", "libx264", "-preset", "ultrafast",
            "-f", "rtsp", f"rtsp://{SERVER_IP}:8554/webcam"
        ])
        print("Webcam streaming started.")

# Function to toggle microphone
def toggle_microphone():
    global is_microphone_on, mic_process
    if is_microphone_on:
        is_microphone_on = False
        print("Microphone turned off.")
    else:
        is_microphone_on = True
        mic_process = subprocess.Popen([
            "ffmpeg", "-f", "dshow", "-i", "audio=Microphone",
            "-acodec", "aac", "-b:a", "128k", "-f", "rtsp",
            f"rtsp://{SERVER_IP}:8554/microphone"
        ])
        print("Microphone streaming started.")

# Function to stop streaming
def stop_stream():
    global scrcpy_process, rtsp_process, is_streaming
    if scrcpy_process:
        scrcpy_process.terminate()
    if rtsp_process:
        rtsp_process.terminate()
    is_streaming = False
    print("Streaming stopped.")

# WebSocket server handler (Supports multiple clients)
async def websocket_handler(websocket):
    async for message in websocket:
        data = json.loads(message)
        command = data.get("command")

        if command == "start_stream":
            start_stream()
        elif command == "stop_stream":
            stop_stream()
        elif command == "toggle_webcam":
            toggle_webcam()
        elif command == "toggle_microphone":
            toggle_microphone()

        response = {"status": "success", "command": command}
        await websocket.send(json.dumps(response))

# Start the WebSocket server (allow multiple clients)
async def start_websocket_server():
    print("Starting WebSocket server on ws://0.0.0.0:8765")
    async with websockets.serve(websocket_handler, "0.0.0.0", 8765):
        await asyncio.Future()

# Run the WebSocket server
asyncio.run(start_websocket_server())