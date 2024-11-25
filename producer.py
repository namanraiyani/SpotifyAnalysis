from kafka import KafkaProducer
import json
import random
import time

# Kafka setup
KAFKA_TOPIC = 'music_topic'
KAFKA_BROKER = 'localhost:9092'

def load_ids():
    try:
        with open('user_ids.json', 'r') as user_file:
            user_ids = json.load(user_file)

        with open('track_ids.json', 'r') as track_file:
            track_ids = json.load(track_file)

        print(f"Loaded {len(user_ids)} user_ids and {len(track_ids)} track_ids from files.")
        return user_ids, track_ids
    except Exception as e:
        print(f"Error loading files: {e}")
        exit()

def kafka_producer(user_ids, track_ids):
    try:
        print("Connecting to Kafka Producer...")
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKER,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        print("Connected to Kafka Producer.")

        existing_combinations = set()
        print("Starting to produce messages to Kafka...")
        while True:
            while True:
                user_id = random.choice(user_ids)
                track_id = random.choice(track_ids)
                if (user_id, track_id) not in existing_combinations:
                    break

            playcount = random.randint(1, 3)
            message = {
                "user_id": user_id,
                "track_id": track_id,
                "playcount": playcount
            }

            # Add the new combination to avoid duplicates
            existing_combinations.add((user_id, track_id))

            # Send to Kafka
            producer.send(KAFKA_TOPIC, message)
            print(f"Produced to Kafka: {message}")
            time.sleep(1)  # Send 1 message per second
    except Exception as e:
        print(f"Error in Kafka Producer: {e}")
        exit()

if __name__ == "__main__":
    user_ids, track_ids = load_ids()
    kafka_producer(user_ids, track_ids)
