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
mic_process = None
is_recording = False
is_streaming = False
is_webcam_on = False
is_microphone_on = False

# Webcam and Microphone Settings
webcam_index = 0  #? Multiple webcams
mic_index = 1      #? Multiple microphones / not detected

# Function to generate timestamped filename
def generate_filename(prefix="recording"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f"{prefix}_{timestamp}.mp4"

# Function to start streaming
def start_stream():
    global scrcpy_process, is_streaming
    if not is_streaming:
        scrcpy_process = subprocess.Popen(["scrcpy", "--max-fps=30", "--video-bit-rate=8M"])
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
        threading.Thread(target=show_webcam, daemon=True).start()
        print("Webcam turned on.")

# Function to show webcam feed
def show_webcam():
    cap = cv2.VideoCapture(webcam_index)
    while is_webcam_on:
        ret, frame = cap.read()
        if ret:
            cv2.imshow("Webcam Feed", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()

# Function to toggle microphone
def toggle_microphone():
    global is_microphone_on
    if is_microphone_on:
        is_microphone_on = False
        print("Microphone turned off.")
    else:
        is_microphone_on = True
        threading.Thread(target=play_microphone_audio, daemon=True).start()
        print("Microphone turned on.")

# Function to play microphone audio
def play_microphone_audio():
    pa = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True,
                     input_device_index=mic_index, frames_per_buffer=1024)
    while is_microphone_on:
        data = stream.read(1024)
        print(".", end="", flush=True)  # Simulating audio playback
    stream.stop_stream()
    stream.close()
    pa.terminate()

# Function to start/stop recording (including webcam & microphone)
def toggle_recording():
    global ffmpeg_process, is_recording, is_streaming, is_webcam_on, is_microphone_on

    if is_streaming:
        if is_recording:
            ffmpeg_process.stdin.write(b"q")
            ffmpeg_process.stdin.flush()
            ffmpeg_process.wait()
            print("Recording stopped.")
        else:
            filename = generate_filename()
            cmd = [
                "ffmpeg",
                "-f", "gdigrab", "-i", "title=Quest 2",
                "-framerate", "30", "-b:v", "5000k", "-c:v", "libx264"
            ]

            # Include webcam if enabled
            if is_webcam_on:
                filename_webcam = generate_filename("webcam")
                cmd.extend(["-f", "vfwcap", "-i", str(webcam_index), "-c:v", "libx264", filename_webcam])

            # Include microphone if enabled
            if is_microphone_on:
                filename_audio = generate_filename("audio")
                cmd.extend(["-f", "dshow", "-i", f"audio={mic_index}", filename_audio])

            cmd.append(filename)  # Main recording filename
            ffmpeg_process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            print(f"Recording started: {filename}")

        is_recording = not is_recording
    else:
        print("Start streaming first.")

# Function to stop streaming
def stop_stream():
    global scrcpy_process, is_recording, is_streaming
    if is_recording:
        toggle_recording()
    if scrcpy_process:
        scrcpy_process.terminate()
        scrcpy_process.wait()
    is_streaming = False
    print("Streaming stopped.")

# WebSocket server handler (Supports multiple clients)
async def websocket_handler(websocket, path):
    try:
        async for message in websocket:
            data = json.loads(message)
            command = data.get("command")

            if command == "start_stream":
                start_stream()
            elif command == "stop_stream":
                stop_stream()
            elif command == "start_recording":
                toggle_recording()
            elif command == "stop_recording":
                toggle_recording()
            elif command == "toggle_webcam":
                toggle_webcam()
            elif command == "toggle_microphone":
                toggle_microphone()

            response = {"status": "success", "command": command}
            await websocket.send(json.dumps(response))

    except websockets.exceptions.ConnectionClosedError:
        print("Client disconnected")

# Start the WebSocket server (allow multiple clients)
async def start_websocket_server():
    async with websockets.serve(websocket_handler, "0.0.0.0", 8765):
        await asyncio.Future()

# Run the WebSocket server
asyncio.run(start_websocket_server())