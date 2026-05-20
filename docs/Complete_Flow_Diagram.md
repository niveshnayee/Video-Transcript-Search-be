# Complete Flow Diagram

This diagram shows the end-to-end flow: client request → synchronous registration response → queued background processing steps (Celery worker).

```mermaid
flowchart LR
  %% Client request path
  subgraph Client
    A[Client]
  end

  A --> B[POST /api/upload]
  B --> C{Request contains}
  C -->|url YouTube| D[Validate YouTube URL]
  C -->|file_id R2| I[Validate file_id]

  %% YouTube branch (synchronous)
  D --> E[VideoService.upload_youtube_video]
  E --> F["VideoRepository.insert<br/>status: UPLOADED,<br/>storage_type: youtube,<br/>url"]
  F --> G["Enqueue background task<br/>process_video_task video_id"]
  G --> H["Response to client<br/>video_id: id, status: UPLOADED"]

  %% R2 branch (synchronous)
  I --> J[VideoService.upload_video]
  J --> K["VideoRepository.insert<br/>status: UPLOADED,<br/>storage_type: r2,<br/>file_id"]
  K --> G

  %% Optional presign flow
  A --> L[POST /r2/presign]
  L --> M[StorageService.generate_presigned_url]
  M --> N[Return presigned URL]
  N -->|Client uploads directly to R2| O[Object stored in R2]
  O -->|Provide file_id to /api/upload| B

  %% Background processing (Celery worker)
  subgraph Background["Background (Celery worker)"]
    P[Celery: process_video_task video_id]
    P --> Q[Fetch video metadata from DB]
    Q --> R[Update status PROCESSING]
    R --> S{storage_type}
    S -->|r2| T["StorageService.download_file file_id to /tmp/video"]
    S -->|youtube| U["yt-dlp download to /tmp/video<br/>Extract title/description to VideoRepository.update_fields"]
    T --> V["VideoUtils.extract_audio /tmp/video to /tmp/audio.wav"]
    U --> V
    V --> W["WhisperTranscriptionService.transcribe /tmp/audio.wav to transcript"]
    W --> X["VideoRepository.add_transcript video_id, transcript"]
    X --> Y[Update status COMPLETED]
    W --> Z[On error Update status FAILED]
    Y --> AA["FileCleanup.cleanup_temp_files /tmp/*"]
  end

  %% Notes about response and queued work
  subgraph Notes
    note1["Synchronous response includes: video_id, current_status=UPLOADED, task_queued=true"]
  end
  H --> note1
  G --> note1
```

Notes:
- The `/api/upload` endpoint returns immediately after registering the video (status UPLOADED) and queues `process_video_task` for asynchronous work.
- Background steps include downloading the source (from R2 or YouTube), audio extraction, transcription, storing transcripts, status updates, and temp file cleanup.
