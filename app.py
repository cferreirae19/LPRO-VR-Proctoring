import signal
import subprocess
import tkinter as tk

# Initialize global variables
scrcpy_process = None
ffmpeg_process = None
is_recording = False
is_streaming = False

# Function to start streaming
def start_stream():
    global scrcpy_process, is_streaming
    is_streaming = True
    scrcpy_process = subprocess.Popen(["scrcpy", "--max-fps=30", "--video-bit-rate=8M"])
    
# Function to start/stop recording
def toggle_recording():
    global ffmpeg_process, is_recording, is_streaming
    if is_streaming:
        if is_recording:
            ffmpeg_process.stdin.write(b"q")
            ffmpeg_process.stdin.flush()
            ffmpeg_process.wait()
            record_button.config(text="Start Recording")
        else:
            ffmpeg_process = subprocess.Popen([
                "ffmpeg", "-f", "gdigrab", "-i", "title=23043RP34G", "-framerate", "30", "-c:v", "libx264", "output.mp4"
            ], stdin=subprocess.PIPE)
            record_button.config(text="Stop Recording")
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

# Create GUI window
root = tk.Tk()
root.title("Oculus Quest 2 Remote Control")

start_button = tk.Button(root, text="Start Streaming", command=start_stream, width=20, height=2)
start_button.pack(pady=10)

record_button = tk.Button(root, text="Start Recording", command=toggle_recording, width=20, height=2)
record_button.pack(pady=10)

stop_button = tk.Button(root, text="Stop Streaming", command=stop_stream, width=20, height=2)
stop_button.pack(pady=10)

root.mainloop()