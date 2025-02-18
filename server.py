import asyncio
import signal
import subprocess
import websockets
import json
import datetime
import cv2
import pyaudio
import wave
import threading

# Initialize global variables
scrcpy_process = None
ffmpeg_process = None
mic_process = None
is_recording = False
is_streaming = False
is_webcam_on = False
is_microphone_on = False

# Webcam and Microphone Settings
webcam_index = 0  #? Multiple webcams
mic_index = 1      #? Multiple microphones / not detected
webcam_name = "HP Wide Vision HD Camera"
mic_name = "Varios micrófonos (Intel® Smart Sound Technology for Digital Microphones)"

# Function to generate timestamped filename
def generate_filename(prefix="recording", extension=".mp4"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f"{prefix}_{timestamp}{extension}"

# Function to start streaming
def start_stream():
    global scrcpy_process, is_streaming
    if not is_streaming:
        scrcpy_process = subprocess.Popen(["scrcpy", "--max-fps=30", "--video-bit-rate=8M"])
        is_streaming = True
        print("Streaming started")

# Function to toggle webcam
def toggle_webcam():
    global is_webcam_on
    is_webcam_on = not is_webcam_on
    if is_webcam_on:
        threading.Thread(target=show_webcam, daemon=True).start()
        print("Webcam turned on.")
    else:
        print("Webcam turned off.")

# Function to show webcam feed
def show_webcam():
    cap = cv2.VideoCapture(webcam_index)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(f'{generate_filename("webcam")}', fourcc, 20.0, (640, 480))
    while is_webcam_on:
        ret, frame = cap.read()
        if ret:
            cv2.imshow("Webcam Feed", frame)
            if is_recording:
                out.write(frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    out.release()
    cv2.destroyAllWindows()

# Function to toggle microphone
def toggle_microphone():
    global is_microphone_on
    is_microphone_on = not is_microphone_on
    if is_microphone_on:
        threading.Thread(target=play_microphone_audio, daemon=True).start()
        print("Microphone turned on.")
    else:
        print("Microphone turned off.")

# Function to play microphone audio
def play_microphone_audio():
    # Set audio parameters
    audio_format = pyaudio.paInt16
    channels = 1
    sample_rate = 44100
    frames_per_buffer = 1024

    # Initialize PyAudio    
    pa = pyaudio.PyAudio()
    
    # Open input stream (microphone)
    input_stream = pa.open(format=audio_format,
                           channels=channels,
                           rate=sample_rate, input=True,
                           input_device_index=mic_index,
                           frames_per_buffer=frames_per_buffer)
    
    # Open output stream (speaker playback)
    output_stream = pa.open(format=audio_format,
                           channels=channels,
                           rate=sample_rate,
                           output=True,
                           frames_per_buffer=frames_per_buffer)
    
    frames = []
    
    while is_microphone_on:
        try:
            data = input_stream.read(frames_per_buffer)  # Capture audio
            output_stream.write(data)  # Play the audio in real-time
            
            if is_recording:
                frames.append(data)  # Save to recording buffer

        except Exception as e:
            print(f"Error during audio processing: {e}")
            break

    # Stop and close streams
    input_stream.stop_stream()
    input_stream.close()
    output_stream.stop_stream()
    output_stream.close()
    pa.terminate()

    # Save recording if applicable
    if frames:
        audio_filename = generate_filename("audio", ".wav")
        with wave.open(audio_filename, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(pa.get_sample_size(audio_format))
            wf.setframerate(sample_rate)
            wf.writeframes(b''.join(frames))

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
            filename_streaming = generate_filename()
            
            cmd = [
                "ffmpeg",
                "-f", "gdigrab", "-framerate", "30", "-i", "title=23043RP34G",
                "-c:v", "libx264", "-b:v", "5000k", 
                filename_streaming
            ]

            # # Include microphone if enabled
            # if is_microphone_on:
            #     filename_audio = generate_filename("audio")
            #     cmd.extend(["-f", "dshow", "-i", f"audio={mic_name}", "-c:a", "aac", "-b:a", "192k", filename_audio])

            ffmpeg_process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            print(f"Recording started: {filename_streaming}")

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
async def websocket_handler(websocket):
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
print("Starting WebSocket server")
asyncio.run(start_websocket_server())