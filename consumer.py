from flask import Flask, jsonify
from faker import Faker
import random
import threading
import time
import csv
import os
from datetime import datetime

app = Flask(__name__)
fake = Faker()

# File names for synthetic music and user data
music_csv_file = "music_info.csv"
user_csv_file = "user_info.csv"

# Function to initialize music CSV if it doesn't exist
def initialize_music_csv():
    if not os.path.exists(music_csv_file):
        with open(music_csv_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                "track_id", "name", "artist", "spotify_preview_url", "spotify_id", 
                "tags", "genre", "year", "duration_ms", "danceability", "energy", 
                "key", "loudness", "mode", "speechiness", "acousticness", 
                "instrumentalness", "liveness", "valence", "tempo", "time_signature"
            ])

# Function to initialize user CSV if it doesn't exist
def initialize_user_csv():
    if not os.path.exists(user_csv_file):
        with open(user_csv_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                "track_id", "user_id", "playcount"
            ])

# Function to generate a single music data record
def generate_music_data():
    track_id = fake.uuid4()
    name = fake.sentence(nb_words=3)
    artist = fake.name()
    spotify_preview_url = fake.url()
    spotify_id = fake.uuid4()
    tags = random.choice(["rock", "pop", "jazz", "classical", "electronic", "hip-hop"])
    genre = random.choice(["Rock", "Pop", "Jazz", "Classical", "Electronic", "Hip-Hop"])
    year = random.randint(2000, 2023)
    duration_ms = random.randint(150000, 300000)  # Random duration between 2 and 5 minutes
    danceability = round(random.uniform(0, 1), 2)
    energy = round(random.uniform(0, 1), 2)
    key = random.randint(0, 11)
    loudness = round(random.uniform(-20, 0), 2)
    mode = random.choice([0, 1])
    speechiness = round(random.uniform(0, 1), 2)
    acousticness = round(random.uniform(0, 1), 2)
    instrumentalness = round(random.uniform(0, 1), 2)
    liveness = round(random.uniform(0, 1), 2)
    valence = round(random.uniform(0, 1), 2)
    tempo = round(random.uniform(60, 200), 2)
    time_signature = random.choice([3, 4, 5])

    return {
        "track_id": track_id,
        "name": name,
        "artist": artist,
        "spotify_preview_url": spotify_preview_url,
        "spotify_id": spotify_id,
        "tags": tags,
        "genre": genre,
        "year": year,
        "duration_ms": duration_ms,
        "danceability": danceability,
        "energy": energy,
        "key": key,
        "loudness": loudness,
        "mode": mode,
        "speechiness": speechiness,
        "acousticness": acousticness,
        "instrumentalness": instrumentalness,
        "liveness": liveness,
        "valence": valence,
        "tempo": tempo,
        "time_signature": time_signature
    }

# Function to generate a single user data record
def generate_user_data():
    track_id = fake.uuid4()
    user_id = fake.uuid4()
    playcount = random.randint(1, 100)
    
    return {
        "track_id": track_id,
        "user_id": user_id,
        "playcount": playcount
    }

# Background task to append generated data to music and user CSV every second
def generate_data_continuously():
    while True:
        music_data = generate_music_data()
        with open(music_csv_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(music_data.values())

        user_data = generate_user_data()
        with open(user_csv_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(user_data.values())

        time.sleep(1)  # Generate data every second

# API route to get recent music data from CSV
@app.route('/recent_music_data', methods=['GET'])
def recent_music_data():
    music_data = []
    if os.path.exists(music_csv_file):
        with open(music_csv_file, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                music_data.append(row)
    return jsonify(music_data[-10:])  # Return last 10 music records

# API route to get recent user data from CSV
@app.route('/recent_user_data', methods=['GET'])
def recent_user_data():
    user_data = []
    if os.path.exists(user_csv_file):
        with open(user_csv_file, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                user_data.append(row)
    return jsonify(user_data[-10:])  # Return last 10 user records

# API route to fetch all music data from CSV
@app.route('/fetch_all_music_data', methods=['GET'])
def fetch_all_music_data():
    music_data = []
    if os.path.exists(music_csv_file):
        with open(music_csv_file, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                music_data.append(row)
    return jsonify(music_data)  # Return all music records as JSON

# API route to fetch all user data from CSV
@app.route('/fetch_all_user_data', methods=['GET'])
def fetch_all_user_data():
    user_data = []
    if os.path.exists(user_csv_file):
        with open(user_csv_file, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                user_data.append(row)
    return jsonify(user_data)  # Return all user records as JSON

if __name__ == '__main__':
    # Initialize CSV and start background data generation
    initialize_music_csv()
    initialize_user_csv()
    threading.Thread(target=generate_data_continuously, daemon=True).start()
    app.run(port=5000)