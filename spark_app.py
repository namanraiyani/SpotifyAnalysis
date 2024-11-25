from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, avg
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from collections import Counter
from wordcloud import WordCloud
import base64
import io
import pandas as pd
from cassandra.cluster import Cluster
from cassandra.query import dict_factory
import statistics
from sklearn.neighbors import NearestNeighbors
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Initialize Spark Session
spark = SparkSession.builder \
    .appName("Music Analytics") \
    .config("spark.cassandra.connection.host", "127.0.0.1") \
    .config("spark.cassandra.connection.port", "9042") \
    .getOrCreate()

# Connect to Cassandra
cassandra_host = '127.0.0.1'
cassandra_port = 9042
keyspace = 'music_db'

cluster = Cluster([cassandra_host], port=cassandra_port)
session = cluster.connect(keyspace)
session.row_factory = dict_factory

# Utility functions
def safe_str(value, default='Unknown'):
    return str(value) if value is not None else default

def safe_float(value, default=0.0):
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def calculate_statistics(tracks):
    """Calculate various statistics from track data."""
    stats = {
        'total_tracks': 0,
        'most_common_genre': None,
        'most_listened_song': None,
        'most_listened_artist': None,
        'average_duration': 0,
        'average_danceability': 0,
        'average_energy': 0,
        'average_loudness': 0,
        'average_tempo': 0,
    }
    genre_counter = Counter()
    song_counter = Counter()
    artist_counter = Counter()
    durations = []
    danceability = []
    energy = []
    loudness = []
    tempos = []
    for track in tracks:
        durations.append(safe_float(track.get('duration_ms')))
        danceability.append(safe_float(track.get('danceability')))
        energy.append(safe_float(track.get('energy')))
        loudness.append(safe_float(track.get('loudness')))
        tempos.append(safe_float(track.get('tempo')))
        genre_counter[safe_str(track.get('genre'))] += 1
        song_counter[safe_str(track.get('name'))] += 1
        artist_counter[safe_str(track.get('artist'))] += 1

    stats['total_tracks'] = len(tracks)
    if genre_counter:
        stats['most_common_genre'] = genre_counter.most_common(1)[0][0]
    if song_counter:
        stats['most_listened_song'] = song_counter.most_common(1)[0][0]
    if artist_counter:
        stats['most_listened_artist'] = artist_counter.most_common(1)[0][0]
    if tracks:
        stats['average_duration'] = (sum(durations) / len(tracks) / 6000) if durations else 0
        stats['average_danceability'] = statistics.mean(danceability) if danceability else 0
        stats['average_energy'] = statistics.mean(energy) if energy else 0
        stats['average_loudness'] = statistics.mean(loudness) if loudness else 0
        stats['average_tempo'] = statistics.mean(tempos) if tempos else 0
    return stats

def fig_to_base64(fig):
    img = io.BytesIO()
    fig.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode('utf8')

def create_pie_chart(data, title, is_percentage=False, figsize=(10, 10)):
    fig, ax = plt.subplots(figsize=figsize)
    labels = list(data.keys())
    values = list(data.values())
    total = sum(values)
    colors = ['#1DB954',  '#FF6F00',  '#0066FF',  '#8E44AD',  '#F39C12',  '#2980B9',  '#D35400',  '#27AE60'][:len(data)]
    
    wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='', startangle=90, colors=colors,
                                       textprops={'fontsize': 10, 'color': 'black'}, wedgeprops={'edgecolor': 'black'})
    
    annotations = []
    for i, value in enumerate(values):
        if is_percentage:
            percentage = (value / total) * 100
            annotation = f'{int(percentage)}%'  
        else:
            annotation = f'{int(value)}'  
        annotations.append(annotation)
    
    for i, a in enumerate(annotations):
        autotexts[i].set_text(a)
        autotexts[i].set_fontsize(12)
        autotexts[i].set_color('black')
    
    fig, ax = apply_black_background(fig, ax)
    ax.legend(wedges, [f'{label}: {ann}' for label, ann in zip(labels, annotations)],
              title=title,
              loc="center left",
              bbox_to_anchor=(1, 0, 0.5, 1),
              fontsize=15, facecolor='black', edgecolor='white', title_fontsize=17,
              labelcolor='white')  
    plt.tight_layout()
    return fig
    
def plot_minutes_by_genre(user_music_info):
    minutes_by_genre = {}
    for track in user_music_info:
        genre = safe_str(track.get('genre'))
        duration_minutes = safe_float(track.get('duration_ms', 0)) / (1000 * 60)
        minutes_by_genre[genre] = minutes_by_genre.get(genre, 0) + duration_minutes
    
    fig = create_pie_chart(minutes_by_genre, 'Minutes by Genre')
    return fig_to_base64(fig)
    
def plot_minutes_by_artist(user_music_info):
    minutes_by_artist = {}
    for track in user_music_info:
        artist = safe_str(track.get('artist'))
        duration_minutes = safe_float(track.get('duration_ms', 0)) / (1000 * 60)
        minutes_by_artist[artist] = minutes_by_artist.get(artist, 0) + duration_minutes
    fig = create_pie_chart(minutes_by_artist, 'Minutes by Artist', figsize=(10, 10))
    return fig_to_base64(fig)
    
def plot_top_songs(user_music_info):
    song_play_counts = {}
    for track in user_music_info:
        song_name = track.get('name', '').strip()
        play_count = track.get('playcount', 0)
        if song_name:
            song_play_counts[song_name] = song_play_counts.get(song_name, 0) + play_count
    top_songs = dict(sorted(song_play_counts.items(), key=lambda item: item[1], reverse=True)[:5])
    
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.barh(list(top_songs.keys()), list(top_songs.values()), color=['#1DB954', '#16B3A7', '#3B4C3D', '#F0A500', '#4A90E2'], height=0.6)
    ax.set_xlabel('Play Count', fontsize=12, color='white')
    ax.set_ylabel('Song', fontsize=12, color='white')
    ax.tick_params(axis='y', labelcolor='white', labelsize=18)
    ax.tick_params(axis='x', labelcolor='white', labelsize=12)
    ax.set_facecolor('black')
    ax.invert_yaxis()  
    fig.patch.set_facecolor('black')
    
    plt.tight_layout()
    return fig_to_base64(fig)
    
def plot_energy_vs_danceability(user_music_info):
    energy = []
    danceability = []
    
    for track in user_music_info:
        energy_value = track.get('energy', None)
        danceability_value = track.get('danceability', None)
        
        if energy_value is not None and danceability_value is not None:
            energy.append(energy_value)
            danceability.append(danceability_value)
    
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.scatter(energy, danceability, color='springgreen', edgecolor='black', alpha=0.7, s=100)
    ax.set_xlabel('Energy', fontsize=12, color='white')
    ax.set_ylabel('Danceability', fontsize=12, color='white')
    ax.tick_params(axis='y', labelcolor='white')
    ax.tick_params(axis='x', labelcolor='white')
    ax.set_facecolor('black')
    fig.patch.set_facecolor('black')
    
    plt.tight_layout()
    return fig_to_base64(fig)
    
def plot_top_tags(user_music_info):
    all_tags = []
    for track in user_music_info:
        tags = track.get('tags', '')
        if isinstance(tags, list):
            all_tags.extend([tag.replace('_', ' ').capitalize() for tag in tags])  
        elif isinstance(tags, str):
            all_tags.extend([tag.strip().replace('_', ' ').capitalize() for tag in tags.split(',')]) 
    tag_counts = Counter(all_tags)
    wordcloud = WordCloud(
        background_color='black',
        colormap='Greens',         
        width=800, height=800,  
        max_words=40,
        contour_color='white',   
        contour_width=2,
    ).generate_from_frequencies(tag_counts)
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')  
    fig.patch.set_facecolor('black')  
    return fig_to_base64(fig)

def apply_black_background(fig, ax):
    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_color('white')
    return fig, ax

def create_wordcloud(data):
    valid_data = {k: v for k, v in data.items() if k and v > 0}
    if not valid_data:
        return None

    wordcloud = WordCloud(
        background_color='black',
        width=800,
        height=800,
        max_words=40,
    ).generate_from_frequencies(valid_data)

    fig, ax = plt.subplots(figsize=(10, 10))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    return fig_to_base64(fig)

def plot_loudness_over_time(user_music_info):
    track_names = []
    loudness_values = []
    
    for track in user_music_info:
        track_name = safe_str(track.get('name'))
        loudness = safe_float(track.get('loudness', 0.0))
        
        if track_name and loudness != 0.0:
            track_names.append(track_name)
            loudness_values.append(loudness)
    
    loudness_df = pd.DataFrame({
        'Track': track_names,
        'Loudness': loudness_values
    })
    
    loudness_df.sort_values(by='Track', inplace=True)
    spotify_green = '#1DB954' 
    fig, ax = plt.subplots(figsize=(10, 10))
    sns.lineplot(data=loudness_df, x='Track', y='Loudness', marker='o', color=spotify_green, linewidth=2)
    
    # Add labels and customize the plot
    ax.set_title("Loudness of Tracks", fontsize=16, color='white')
    ax.set_xlabel("Track Name", fontsize=12, color='white')
    ax.set_ylabel("Loudness (dB)", fontsize=12, color='white')
    ax.tick_params(axis='x', labelrotation=90, labelsize=15, labelcolor='white')
    ax.tick_params(axis='y', labelsize=10, labelcolor='white')
    ax.set_facecolor('black')
    fig.patch.set_facecolor('black')
    
    plt.tight_layout()
    
    return fig_to_base64(fig)


# Flask routes
@app.route("/", methods=["GET", "POST"])
def user_dashboard():
    if request.method == "POST":
        user_id = request.form.get("user_id")
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        user_history_query = "SELECT * FROM user_listening_history WHERE user_id = %s"
        user_history = list(session.execute(user_history_query, [user_id]))
        if not user_history:
            return jsonify({"error": "No listening history found for this user"}), 404

        user_music_info = []
        for history_item in user_history:
            track_id = history_item.get('track_id')
            if track_id:
                music_info_query = "SELECT * FROM music_info_new WHERE track_id = %s"
                track_info = session.execute(music_info_query, [track_id]).one()
                if track_info:
                    combined_info = {**track_info, 'playcount': history_item.get('playcount', 0)}
                    user_music_info.append(combined_info)

        # Spark data processing (minimal usage)
        spark_df = spark.createDataFrame(user_music_info)
        genre_stats = spark_df.groupBy("genre").count().orderBy("count", ascending=False).collect()

        statistics = calculate_statistics(user_music_info)

        plot_images = {}
        plot_images["wordcloud"] = create_wordcloud({row['genre']: row['count'] for row in genre_stats})
        plot_images["minutes_by_genre"] = plot_minutes_by_genre(user_music_info)
        plot_images["minutes_by_artist"] = plot_minutes_by_artist(user_music_info)
        plot_images["top_5_songs"] = plot_top_songs(user_music_info)
        plot_images["top_tags"] = plot_top_tags(user_music_info)
        plot_images["scatterplot_energy"] = plot_energy_vs_danceability(user_music_info)
        plot_images["music_loudness"] = plot_loudness_over_time(user_music_info)
        return render_template(
            "dashboard.html",
            user_id=user_id,
            plot_images=plot_images,
            statistics=statistics,
        )

    return render_template("index.html")

@app.route('/recommendations', methods=['GET'])
def get_recommendations():
    user_id = safe_str(request.args.get('user_id'))
    num_recommendations = int(request.args.get('num_recommendations', 5))
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    user_history_query = "SELECT * FROM user_listening_history WHERE user_id = %s"
    user_history = session.execute(user_history_query, [user_id])
    user_history = list(user_history)
    if not user_history:
        return jsonify({"error": f"No listening history found for User ID {user_id}"}), 404

    user_data = []
    for row in user_history:
        track_query = "SELECT * FROM music_info_new WHERE track_id = %s"
        music_info = session.execute(track_query, [safe_str(row.get('track_id'))]).one()
        if music_info:
            user_data.append(music_info)

    if len(user_data) < 2:
        return jsonify({"error": "Not enough listening history to generate recommendations"}), 400

    try:
        X = np.array([[safe_float(row.get('danceability')), safe_float(row.get('energy')),
                       safe_float(row.get('loudness')), safe_float(row.get('tempo'))] for row in user_data])
        knn_model = NearestNeighbors(n_neighbors=min(num_recommendations, len(X)), metric='euclidean')
        knn_model.fit(X)
        distances, indices = knn_model.kneighbors(X)

        recommendations_list = []
        added_tracks = set()
        for i, idx in enumerate(indices):
            for j in range(len(idx)):
                recommended_track = user_data[idx[j]]
                track_id = safe_str(recommended_track.get('track_id'))
                if track_id and track_id not in added_tracks:
                    recommendations_list.append({
                        "name": safe_str(recommended_track.get('name')),
                        "artist": safe_str(recommended_track.get('artist'))
                    })
                    added_tracks.add(track_id)
                    if len(recommendations_list) >= num_recommendations:
                        break
            if len(recommendations_list) >= num_recommendations:
                break

        return jsonify(recommendations_list[:num_recommendations])
    except Exception as e:
        return jsonify({"error": f"Error processing music features: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
