import socketio
import pyaudio
import time
import wave
import os
import zlib
import sys
import ntplib


ARGS = sys.argv
# IP = str(ARGS[0])
ID = "mathias"


init_time = time.perf_counter()
client = ntplib.NTPClient()

sio = socketio.Client()
server_url = f"http://localhost:5000"

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 7
OUTPUT_FOLDER = "output_local"

audio = pyaudio.PyAudio()
frames = []


def record_audio(start_time):
    """
    Wait until the specified start time and then record audio for a predefined duration.
    """

    # Wait until the local performance counter reaches the specified start time
    # TODO very shitty needs fix

    ntp_time = client.request("pool.ntp.org", version=3).tx_time
    init_time = time.perf_counter()
    while ntp_time < start_time:
        ntp_time = ntp_time + time.perf_counter() - init_time

    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True, frames_per_buffer=CHUNK)

    start_recording = time.perf_counter()

    while time.perf_counter() - start_recording < RECORD_SECONDS:
        data = stream.read(CHUNK)
        frames.append(data)
    print(
        f"Recording finished. Time: {time.perf_counter() - start_recording} seconds.")

    # print("Recording finished.")

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    audio.terminate()

    return b''.join(frames), ntp_time


def save_wav(test_id, timestamp, data):
    """
    Save the recorded audio data to a WAV file.
    """
    folder_path = os.path.join(OUTPUT_FOLDER, f"test_{test_id}")
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, f"{ID}_{timestamp}.wav")

    with wave.open(file_path, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(pyaudio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(data)

    print(f"Audio saved as {file_path}")


@ sio.on('start_test')
def handle_start_test(data):
    """
    Handle the 'start_test' event from the server, which includes the start time for recording.
    """
    test_id = data['test_id']
    start_time = data['start_time']

    recorded_data, ntp_time = record_audio(start_time)

    compressed_data = zlib.compress(recorded_data)

    chunk_size = CHUNK

    for i in range(0, len(compressed_data), chunk_size):
        sio.emit('audioData', {
                 'data': compressed_data[i:i + chunk_size], 'test_id': test_id, 'timestamp':  ntp_time})

    sio.emit('endOfData', test_id)

    save_wav(test_id, start_time, recorded_data)


# TODO Using NTP now
# @sio.on('syncResponse')
# def handle_sync_response(server_time):
#    """
#    Handle the syncResponse event from the server, which includes the server's timestamp.
#    Adjust the clock offset based on the server's timestamp and the round-trip time.
#    """
#    global clock_offset
#    client_receive_time = time.perf_counter()
#    round_trip_time = client_receive_time - client_send_time
#    estimated_server_time_at_client_receive = server_time + round_trip_time / 2
#    clock_offset = estimated_server_time_at_client_receive - client_receive_time
#    print(f"Clock offset adjusted: {clock_offset} seconds.")

@ sio.event
def connect():
    """
    Handle connection to the server.
    """
    print("Connected to the server.")
    # Register this microphone/client with the server
    sio.emit('newMicrophone', {'id': ID, 'sample_rate': RATE})
    # Synchronize time with the server


@ sio.event
def disconnect():
    """
    Handle disconnection from the server.
    """
    print("Disconnected from the server.")


def clear_buffer(stream, chunks=10):
    for _ in range(chunks):
        stream.read(CHUNK, exception_on_overflow=False)


# Clear buffer right before starting main recording loop

if __name__ == "__main__":
    # Connect to the server
    sio.connect(server_url)
    sio.wait()
