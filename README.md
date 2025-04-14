# Smart Video Search

This project is built with **FastAPI**. It allows users to upload videos, transcribe them, and search through the transcripts using either basic or semantic search strategies. The project integrates with **Google Cloud Storage**, **MongoDB**, and **Celery** for task processing.

---

## Features

- **Video Upload**: Upload videos and store metadata in MongoDB.
- **Transcription**: Extract audio from videos and generate transcripts using **Whisper** or **YouTubeTranscriptApi** (for YouTube videos).
- **Search**: Search transcripts using:
  - **Basic Search**: Simple text matching.
  - **Semantic Search**: Contextual search using **SentenceTransformers**.
- **Task Queue**: Asynchronous video processing with **Celery** and **Redis**.
- **Google Cloud Storage**: Store video files in GCS with signed URLs.
- **RESTful API**: Expose endpoints for video management, transcription, and search.

---

## Project Structure

```
.
├── app/
│   ├── database.py                # MongoDB client setup
│   ├── main.py                    # FastAPI application entry point
│   ├── models/                    # Pydantic models for request/response
│   ├── repositories/              # Database interaction logic
│   ├── routers/                   # API routes
│   ├── services/                  # Core business logic (transcription, search, etc.)
│   ├── tasks/                     # Celery worker tasks
│   ├── utils/                     # Utility functions (e.g., file cleanup, video utils)
├── run.py                         # Script to start the FastAPI server
├── run.sh                         # Script to start the entire stack (Redis, Celery, FastAPI)
├── requirements.txt               # Python dependencies
├── .env                           # Environment variables
├── .gitignore                     # Ignored files for Git
```

---

## Installation

### Prerequisites

- Python 3.10+
- Redis
- MongoDB
- Google Cloud Storage bucket
- [Google Cloud Service Account Key](https://cloud.google.com/iam/docs/creating-managing-service-account-keys)

### Steps

1. **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd <repository-folder>
    ```

2. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Set up environment variables**: Create a `.env` file in the root directory with the following variables:
    ```env
    MONGO_USERNAME=<your-mongo-username>
    MONGO_PASSWORD=<your-mongo-password>
    DATABASE_NAME=<your-database-name>
    BUCKET_NAME=<your-gcs-bucket-name>
    ```

4. **Set up Google Cloud credentials**: Place your service account key JSON file in the root directory and update `.gitignore` to exclude it.

5. **Run the application**: Use the provided `run.sh` script to start the stack:
    ```bash
    chmod +x run.sh
    ./run.sh
    ```

---

## API Endpoints

### Video Management

- `GET /videos`: Fetch all uploaded videos.
- `GET /video/{video_id}`: Fetch details of a specific video.
- `POST /upload_video`: Upload a video and start transcription.
- `DELETE /delete_video/{video_id}`: Delete a video and its associated data.

### Transcription

- `POST /transcribe_video`: Start transcription for a video.

### Search

- `POST /video/{video_id}/search`: Search the transcript of a video.

### Task Management

- `GET /task_status/{task_id}`: Check the status of a Celery task.

---

## Key Components

1. **Transcription Services**
   - `YouTubeTranscriptApi`: Fetch transcripts directly from YouTube.
   - `Whisper`: Generate transcripts from audio files.

2. **Search Strategies**
   - `BasicSearch`: Simple substring matching.
   - `SemanticSearch`: Contextual search using SentenceTransformers.

3. **Google Cloud Storage**
   - Store video files and generate signed URLs for secure uploads.

4. **MongoDB**
   - Store video metadata and transcripts.

5. **Celery + Redis**
   - Asynchronous task processing for video transcription.

---

## Deployment

### Local Deployment

**Run the application locally using uvicorn**:
```bash
python run.py
```