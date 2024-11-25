# SpotifyAnalysis

User Behavior Analysis with Apache Spark, Kafka, and Cassandra
Overview
This project focuses on analyzing user behavior in real-time by processing streaming data from Kafka using Apache Spark. The goal is to provide personalized music recommendations based on users' listening habits, musical preferences, and emotional context. The analysis includes metrics like top genres, mood-based tags, and user interaction insights, all displayed on a user dashboard for a personalized experience.

Key Technologies
Apache Kafka: Real-time data streaming for song metadata and user listening history.
Apache Spark: Real-time processing and aggregation of streaming data.
Apache Cassandra: Storage for processed data and results.
Data Pipeline
Data Ingestion:

Kafka Topics:
Song Metadata: Song attributes like title, artist, genre, danceability, energy, and valence.
User Listening History: User interactions with songs (User ID, Song ID, timestamp, and duration).
Real-Time Processing:

Spark Streaming:
Processes song metadata to extract key song features (danceability, energy, valence).
Aggregates user listening data to calculate metrics such as total listening time, top genres, top artists, and mood tags.
Personalization:

Insights:
Top genres and artists for each user.
Mood tags based on song characteristics (e.g., "Chill" or "Energetic").
Recommendations based on user’s listening history.
Data Storage:

Processed data is stored in Apache Cassandra for efficient retrieval and further analysis.
Usage
Set up Apache Kafka for streaming the song metadata and user listening history.
Use Apache Spark Streaming to process the incoming data from Kafka topics.
Store the processed data in Apache Cassandra for analysis and display.
Access user insights via the dashboard for personalized recommendations.
Prerequisites
Apache Kafka
Apache Spark
Apache Cassandra

![image](https://github.com/user-attachments/assets/7872146b-c4db-438d-9516-8e6db9f40db2)

![image](https://github.com/user-attachments/assets/4206abb2-7845-4cac-b1cc-80c30e835365)

![image](https://github.com/user-attachments/assets/0f628af0-817b-4a7f-8cd0-99290f62f797)

![image](https://github.com/user-attachments/assets/98b2d45e-bcd1-454c-b2cd-0718dc2df709)
