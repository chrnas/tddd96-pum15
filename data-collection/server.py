from flask import Flask, send_from_directory, request
from flask_socketio import SocketIO, emit
import os
import math
from datetime import datetime
from Multilaterate import Multilateration
import numpy as np
import time
import numpy as np
from scipy.optimize import least_squares
from tidsuträkning.TidsförskjutningBeräkning import Wav_file, calc_offset, create_wav_object
import matplotlib.pyplot as plt  # Corrected import

app = Flask(__name__, static_folder='public', static_url_path='')

perf_counter = time.perf_counter()
print("preftcounter", perf_counter)
microphones = {}
socketio = SocketIO(app)


# TBH i have no idea how to use this class.
multilateration = Multilateration(v=343, delta_d=1, max_d=300)


class AudioData:

    def __init__(self, data, timestamp):
        self.data = data
        self.timestamp = timestamp

    def RMS(self):
        return math.sqrt(sum([sample**2 for sample in self.data]) / len(self.data))

    def __repr__(self):
        return f'AudioData(data={len(self.data)}, timestamp={self.timestamp})'


class User:
    def __init__(self, name, xCoordinate=None, yCoordinate=None, sample_rate=44100):
        self.sample_rate = sample_rate
        self.name = name
        self.xCoordinate = xCoordinate
        self.yCoordinate = yCoordinate
        self.audio_data = []
        self.distances = {}
        self.last_timestamp = None
        self.triggered = False
        self.extra_samples = 0

        # Initialize the lock attribute for each user (microphone)
        self.lock = False

    def update_last_timestamp(self, timestamp):
        self.last_timestamp = timestamp

    def add_audio_data(self, audio_data):
        if len(self.audio_data) >= 150:  # How many audio data points to store
            self.audio_data.pop(0)
        self.audio_data.append(audio_data.data)

    def calculate_distances(self, users):
        for sid, user in users.items():
            if user != self:
                dx = self.xCoordinate - user.xCoordinate
                dy = self.yCoordinate - user.yCoordinate
                distance = math.sqrt(dx**2 + dy**2)
                self.distances[sid] = distance

    def get_last_audio_data(self):
        if len(self.audio_data) > 0:
            return self.audio_data[-1]
        return None

    def get_last_audio_data_timestamp(self):
        return self.last_timestamp

    def __repr__(self):
        return f'User(name={self.name}, xCoordinate={self.xCoordinate}, yCoordinate={self.yCoordinate}, audio_data_count={len(self.audio_data)})'


def broadcast_user_positions():
    users_data = [{'name': user.name, 'xCoordinate': user.xCoordinate,
                   'yCoordinate': user.yCoordinate} for user in microphones.values()]
    emit('updatePositions', users_data, broadcast=True)


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/start_test')
def start_test():
    return "Started"

@socketio.on('newUser')
def handle_new_user(data):
    # Function to handle new user connection

    name = data.get('name')
    xCoordinate = float(data.get('xCoordinate'))
    yCoordinate = float(data.get('yCoordinate'))
    sample_rate = data.get('sample_rate') or 44100

    new_user = User(name, xCoordinate, yCoordinate, sample_rate)

    microphones[request.sid] = new_user

    new_user.calculate_distances(microphones)
    for sid, user in microphones.items():
        if sid != request.sid:
            user.calculate_distances(microphones)

    print(f'New user connected: {new_user}')
    broadcast_user_positions()


@socketio.on('audioData')
def handle_audio_data(data):
    audio_data = AudioData(data['data'], data['timestamp'])
    print("Got the audio")
    if request.sid in microphones:
        user = microphones[request.sid]
        user.add_audio_data(audio_data)
        user.update_last_timestamp(data["timestamp"])

        if audio_data.RMS() > 0.3 and not user.triggered and len(user.audio_data) == 150:
            print("Triggered")
            user.triggered = True
            return

        if user.triggered and user.extra_samples < 50:
            user.extra_samples += 1
            return

        if user.triggered and user.extra_samples == 50:
            user.triggered = False
            user.extra_samples = 0

            wav_files = []
            for id in microphones:
                listconcated = [
                    item for sublist in microphones[id].audio_data for item in sublist]
                wav_file = create_wav_object(
                    listconcated, microphones[id].sample_rate)
                # wav_file.save(f'{microphones[id].name}_audio_data.wav')
                wav_files.append(wav_file)

            tdoa_0_1 = calc_offset(wav_files[0], wav_files[1])

            print("TDOA 0 1", tdoa_0_1)

            plt.figure(figsize=(10, 5))
            print("Plotting")
            # Save and plot for the current microphone
            current_user = user  # The current microphone/user

            current_user_audio_flat = [
                item for sublist in current_user.audio_data for item in sublist]
            plt.subplot(2, 1, 1)  # First subplot
            plt.plot(current_user_audio_flat,
                     label=f'Microphone {current_user.name}')
            plt.xlabel('Sample')
            plt.ylabel('Amplitude')
            plt.title(f'Waveform - Microphone {current_user.name}')
            plt.legend()

            # Save and plot for the other microphone
            other_microphone_id = next(
                (id for id in microphones if id != request.sid), None)
            if other_microphone_id is not None:
                other_user = microphones[other_microphone_id]
                other_user_audio_flat = [
                    item for sublist in other_user.audio_data for item in sublist]
                plt.subplot(2, 1, 2)  # Second subplot
                plt.plot(other_user_audio_flat,
                         label=f'Microphone {other_user.name}')
                plt.xlabel('Sample')
                plt.ylabel('Amplitude')
                plt.title(
                    f'Waveform - Microphone {other_user.name} {tdoa_0_1} ')
                plt.legend()

            plt.tight_layout()
            plt.savefig(f'waveforms_{current_user.name}_{other_user.name}.png')
            plt.close()

            return


@socketio.on('syncTime')
def handle_sync_time():
    # Function to handle sync time request from the client
    print("Sync requested")
    server_timestamp = time.perf_counter() - perf_counter
    emit('syncResponse', server_timestamp)


@socketio.on('disconnect')
def handle_disconnect():
    # Clean up when a user disconnects
    if request.sid in microphones:
        print(f'User {microphones[request.sid].name} disconnected')
        microphones.pop(request.sid, None)
    emit('userDisconnected', {'id': request.sid}, broadcast=True)

    def equations(guess):
        x, y = guess
        return [(np.linalg.norm([x - pos[0], y - pos[1]]) - distance) for pos, distance in zip(positions, distances)]

    initial_guess = [0, 0]

    result = least_squares(equations, initial_guess)
    sound_source_position = np.round(result.x).astype(int)

    return sound_source_position


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)