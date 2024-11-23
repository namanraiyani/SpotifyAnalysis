import json
from cassandra.cluster import Cluster

# Cassandra setup
CASSANDRA_CONTACT_POINTS = ['localhost']
CASSANDRA_KEYSPACE = 'music_db'
CASSANDRA_TABLE = 'user_listening_history'

def fetch_and_store_ids():
    try:
        print("Connecting to Cassandra...")
        cluster = Cluster(CASSANDRA_CONTACT_POINTS)
        session = cluster.connect(CASSANDRA_KEYSPACE)
        print("Connected to Cassandra.")

        query = f"SELECT user_id, track_id FROM {CASSANDRA_TABLE};"
        rows = session.execute(query)

        user_ids = set()
        track_ids = set()

        for row in rows:
            user_ids.add(row.user_id)
            track_ids.add(row.track_id)

        # Save to JSON files
        with open('user_ids.json', 'w') as user_file:
            json.dump(list(user_ids), user_file)

        with open('track_ids.json', 'w') as track_file:
            json.dump(list(track_ids), track_file)

        print(f"Saved {len(user_ids)} unique user_ids to 'user_ids.json'.")
        print(f"Saved {len(track_ids)} unique track_ids to 'track_ids.json'.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_and_store_ids()