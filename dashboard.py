import pickle
import pandas as pd
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
import plotly.express as px

# Cassandra connection settings
cassandra_host = '127.0.0.1'  # Replace with your Cassandra host
cassandra_port = 9042         # Replace with your Cassandra port
keyspace = 'music_db'

# Connect to the Cassandra cluster
cluster = Cluster([cassandra_host], port=cassandra_port)
session = cluster.connect(keyspace)

# Initialize Dash app
app = Dash(__name__)
app.title = "Music Data Analysis Dashboard"

# Function to fetch data from Cassandra
def fetch_data_from_cassandra():
    # Fetching user listening history
    query_user_history = "SELECT * FROM user_listening_history"
    user_result = session.execute(query_user_history)
    user_data = pd.DataFrame(user_result, columns=user_result.column_names)

    # Fetching music information
    query_music_info = "SELECT * FROM music_info_new"
    music_result = session.execute(query_music_info)
    music_data = pd.DataFrame(music_result, columns=music_result.column_names)

    return user_data, music_data

# Function to process data using Pandas
def process_data_with_pandas(user_data, music_data):
    # Average song duration by genre
    avg_duration_by_genre = music_data.groupby("genre")["duration"].mean().reset_index()
    avg_duration_by_genre.rename(columns={"duration": "avg_duration"}, inplace=True)

    # Popular genre based on total listening duration
    popular_genre = user_data.merge(music_data, on="track_id", how="left")
    popular_genre = popular_genre.groupby("genre")["listening_duration"].sum().reset_index()
    popular_genre.rename(columns={"listening_duration": "total_duration"}, inplace=True)

    # Genre distribution by year
    genre_by_year = music_data.groupby(["year", "genre"]).size().reset_index(name="count")

    # Average loudness per genre
    avg_loudness_by_genre = music_data.groupby("genre")["loudness"].mean().reset_index()
    avg_loudness_by_genre.rename(columns={"loudness": "avg_loudness"}, inplace=True)

    # Average key per genre
    avg_key_by_genre = music_data.groupby("genre")["key"].mean().reset_index()
    avg_key_by_genre.rename(columns={"key": "avg_key"}, inplace=True)

    return avg_duration_by_genre, popular_genre, genre_by_year, avg_loudness_by_genre, avg_key_by_genre

# Function to create pickle file from processed data
def create_pickle_file():
    # Fetch the data
    user_data, music_data = fetch_data_from_cassandra()

    # Process the data using Pandas
    avg_duration_by_genre, popular_genre, genre_by_year, avg_loudness_by_genre, avg_key_by_genre = process_data_with_pandas(user_data, music_data)

    # Save processed data to a pickle file
    metrics = {
        "avg_duration_by_genre": avg_duration_by_genre,
        "popular_genre": popular_genre,
        "genre_by_year": genre_by_year,
        "avg_loudness_by_genre": avg_loudness_by_genre,
        "avg_key_by_genre": avg_key_by_genre,
    }

    with open("music_metrics.pkl", "wb") as f:
        pickle.dump(metrics, f)

# Function to load data from the pickle file
def load_pickle_file():
    with open("music_metrics.pkl", "rb") as f:
        return pickle.load(f)

# Define function to create bar plots with custom styling
def create_bar_figure(data, x, y, title, color=None):
    return px.bar(
        data,
        x=x,
        y=y,
        color=color,
        text_auto=True,
        color_discrete_sequence=px.colors.qualitative.Pastel
    ).update_layout(
        title=title,
        title_font=dict(size=36),
        xaxis_title=x.capitalize(),
        yaxis_title=y.capitalize(),
        font=dict(size=24),
        bargap=0.5,  # Reduce bar thickness
        height=450,
        margin=dict(l=40, r=40, t=70, b=40),
    )

# Define function to create line plots
def create_line_figure(data, x, y, title, color=None):
    return px.line(
        data,
        x=x,
        y=y,
        color=color,
        title=title,
        color_discrete_sequence=px.colors.qualitative.Vivid
    ).update_layout(
        title=title,
        title_font=dict(size=36),
        font=dict(size=24),
        height=450,
        margin=dict(l=40, r=40, t=70, b=40),
    )

# Layout with black background and green font
app.layout = html.Div(
    style={"background-color": "#2e2e2e", "color": "#4CAF50", "font-family": "Arial, sans-serif"},
    children=[
        html.H1(
            "Music Data Analysis Dashboard",
            style={"text-align": "center", "font-size": "72px", "color": "#4CAF50", "margin-bottom": "20px"}
        ),
        html.Button("Reload Data", id="reload-button", n_clicks=0, style={"font-size": "24px", "background-color": "#4CAF50", "color": "white", "padding": "10px 20px", "border": "none", "cursor": "pointer"}),
        html.Div(id="tabs-content", style={"padding": "20px"})
    ]
)

# Callback to reload data and regenerate the pickle file
@app.callback(
    Output("tabs-content", "children"),
    [Input("reload-button", "n_clicks")]
)
def reload_data(n_clicks):
    if n_clicks > 0:
        create_pickle_file()  # Regenerate pickle file when the button is clicked

    # Load the processed data from the pickle file
    metrics = load_pickle_file()

    # Render the charts
    return html.Div([
        dcc.Graph(
            id="avg_duration_graph",
            figure=create_bar_figure(metrics["avg_duration_by_genre"], "genre", "avg_duration", "Average Song Duration per Genre")
        ),
        dcc.Graph(
            id="popular_genre_graph",
            figure=create_bar_figure(metrics["popular_genre"], "genre", "total_duration", "Most Popular Genre (Based on Song Duration)")
        ),
        dcc.Graph(
            id="genre_by_year_graph",
            figure=create_line_figure(metrics["genre_by_year"], "year", "count", "Genre Distribution by Year")
        ),
        dcc.Graph(
            id="avg_loudness_graph",
            figure=create_bar_figure(metrics["avg_loudness_by_genre"], "genre", "avg_loudness", "Average Loudness per Genre")
        ),
        dcc.Graph(
            id="avg_key_graph",
            figure=create_bar_figure(metrics["avg_key_by_genre"], "genre", "avg_key", "Average Key per Genre")
        )
    ])

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
