from typing import List
from fastapi import APIRouter, HTTPException, Form, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from urllib.parse import urlparse, parse_qs
from google.cloud import storage
import os
from dotenv import load_dotenv
import uuid
from datetime import timedelta
from bson import ObjectId
from celery.result import AsyncResult
from app.database import MongoDBClient

from app.services.video_processing import VideoProcessingService  # Updated import
from app.models.video_models import SearchQuery, VideoCreate, VideoResponse, TranscriptItem
from app.repositories.video_repository import VideoRepository
from app.services.storage_service import StorageService
from app.utils.file_cleanup import FileCleanup
from app.database import MongoDBClient
from app.utils.video_utils import VideoUtils
from app.services.search_transcript.basic_search import BasicSearch
from app.services.search_transcript.search_service import SearchStrategy
from app.services.search_transcript.semantic_search import SemanticSearch


router = APIRouter()
load_dotenv()  # Load environment variables from .env file

# Initialize dependencies
def get_video_repo():
    mongo_client = MongoDBClient()
    return VideoRepository(mongo_client.get_collection("videos"))


def get_storage_service():
    return StorageService(
        bucket_name=os.getenv("BUCKET_NAME")
    )

def get_processing_service():
    return VideoProcessingService(
        video_utils=VideoUtils(),
        file_cleanup=FileCleanup(),
        transcription_service=WhisperTranscriptionService(),
        video_repo=get_video_repo()
    )

def get_search_strategy(method: str = "basic") -> SearchStrategy:
    strategies = {
        "basic": BasicSearch,
        "semantic": SemanticSearch,
    }
    return strategies[method]()
    



@router.get("/videos", response_model=VideoResponse)
async def get_all_videos(repo: VideoRepository = Depends(get_video_repo)):
    """
    Get a list of all uploaded videos with metadata.
    """
    try:
        videos = repo.get_all_videos() # IMPLEMENT THIS FUNCTION
        video_list = []

        for video in videos:
            video_list.append(
                {
                    "video_id": str(video["_id"]),
                    "name": video["name"],
                    "category": video["category"],
                    "description": video["description"],
                    "url": video.get("url"),
                }
            )

        return VideoResponse(
            success=True,
            message="Videos fetched successfully",
            data={"videos": video_list},
        )
    except Exception as e:
        logging.error(f"Error fetching videos: {str(e)}")
        return VideoResponse(
            success=False, message=f"An error occurred while fetching videos: {str(e)}", data=None
        )




@router.get("/video/{video_id}")
async def get_video_details(video_id: str, repo: VideoRepository = Depends(get_video_repo)):
    """
    Get the details of a specific video by its ID.
    """
    try:
        video = repo.get_video(video_id)
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        # Prepare video metadata
        response_data = {
            "name": video.get("name"),
            "video_id": str(video["_id"]) , # Convert ObjectId to string
            "category": video.get("category"),
        }
        if video.get("url"):
            response_data["url"] = video.get("url")
        
        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching video details: {str(e)}")


@router.delete("/delete_video/{video_id}")
def delete_video(
    video_id: str,
    repo: VideoRepository = Depends(get_video_repo),
    storage: StorageService = Depends(get_storage_service)
    ):
    """Delete video and associated data"""
    try:
        try:
            video_id_obj = ObjectId(video_id)  # Convert video_id to ObjectId
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid video ID format")

        # Step 1: Get video metadata from MongoDB
        video_data = repo.get_video(video_id_obj)
        
        if not video_data:
            raise HTTPException(status_code=404, detail="Video not found")


         # Delete from storage
        storage.delete_file(video_data.file_id)
        
        # Delete from database
        repo.delete_video(video_id_obj)
        
        return {"success": True, "message": "Video deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")



@router.post("/generate_upload_url")
def get_signed_url(
    video_name: str = Form(...),
    storage: StorageService = Depends(get_storage_service)
    ):
    """Generate a signed URL so the frontend can upload directly to GCS."""
    try:

        unique_filename = f"{uuid.uuid4()}_{video_name}"
        signed_url = storage.generate_upload_url(
                object_name=unique_filename,
                expiration=15  # 15 minute expiration
        )

        return {"upload_url": signed_url, "file_id": unique_filename}
    except Exception as e:
        logging.error(f"URL generation failed: {str(e)}")




@router.post("/upload_video", response_model=VideoResponse)
def upload_video(
    background_tasks: BackgroundTasks,
    video_name: str = Form(...),
    video_category: str = Form(...),
    video_description: str = Form(...),
    fileId: str = Form(...),
    repo: VideoRepository = Depends(get_video_repo),
    storage: StorageService = Depends(get_storage_service),
    processing: VideoProcessingService = Depends(get_processing_service)
    ):
    """
    Upload a video file, store it in Google Cloud Storage(in frontend), and save metadata to MongoDB.
    """
    try:
        if not fileId:
            raise HTTPException(status_code=400, detail="Video file is required")

        """Store video metadata and start async transcript processing."""
        video_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{fileId}"

        # Save video metadata to MongoDB
        # After successful upload, create video data object
        video_data = VideoCreate(
            name=video_name,
            category=video_category,
            description = video_description,
            url=video_url,
            file_id=fileId,
            status = "queued"  # Initial status
        )
   

         # Save to database
        video_id = repo.create_video(video_data.dict())

        # Start processing task
        task = processing.process_video_task.delay(str(video_id), video_data.url)



        #  # Start Celery task
        # task = VideoProcessingService.process_video_from_url.apply_async(args=[str(inserted_id), video_url])  # Updated task call

         # Return success response
        return JSONResponse(
            status_code=200,
            content=VideoResponse(
                success=True,
                message="Video uploaded and processing started successfully",
                data={
                    "video_id": str(video_id),
                    "name": video_name,
                    "category": video_category,
                    "description": video_description,
                    "url": video_url,
                    "task_id": task.id
                },
            ).dict(),
        )
    except HTTPException as e:
        # Delete the file from GCS if an error occurs
        storage.delete_file(file_id)
        return JSONResponse(
            status_code=e.status_code,
            content=VideoResponse(
                success=False,
                message=f"An error occurred: {str(e)}",
                data=None,
            ).dict(),
        )

    except Exception as e:
        # Delete the file from GCS if an error occurs
        storage.delete_file(file_id)
        return JSONResponse(
            status_code=500,
            content=VideoResponse(
                success=False,
                message=f"An error occurred: {str(e)}",
                data=None,
            ).dict(),
        )

@router.post("/video/{video_id}/search")
async def search_transcript(
    video_id: str, 
    query: SearchQuery,
    repo: VideoRepository = Depends(get_video_repo)
    ):
    """
    Search for the query text in the transcript and return results with timestamps.
    """

    try:
        # Fetch video by ID
        video = repo.get_video(ObjectId(video_id))
        # video = videos_collection.find_one({"_id": ObjectId(video_id)})

        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        transcript = video.get("transcript", [])

        if not transcript:
            raise HTTPException(status_code=404, detail="Transcript not found")

        video_url = video.get("url")
        if not video_url:
            raise HTTPException(status_code=404, detail="Video URL not found")

        # Get search strategy based on method
        strategy = get_search_strategy("semantic")
        # strategy = get_search_strategy("basic")
        results = strategy.search(query.query.lower(), transcript, video_url)


        # Search in the transcript
        # results = []
        # for idx, entry in enumerate(transcript):
        #     if query.query.lower() in entry["text"].lower():
        #         results.append({
        #             "seconds": entry["timestamp"],
        #             "time": seconds_to_video_time(entry["timestamp"]),
        #             "text": " ".join(
        #                 [entry["text"]] +
        #                 [transcript[i]["text"] for i in range(idx + 1, min(idx + 4, len(transcript)))]
        #             ),
        #             "video_link": f"{video_url}#t={int(entry['timestamp'])}s"
        #         })

        if not results:
            return JSONResponse(
                status_code=200,
                content={"success": False, "message": "No results found", "data": None},
            )

        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "Search completed successfully", "data": {"results": results}},
        )

    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"success": False, "message": e.detail, "data": None},
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Error searching transcript: {str(e)}", "data": None},
        )


@router.post("/transcribe_video")
def transcribe(file_id: str, video_url: str):
    task = VideoProcessingService.process_video_from_url.apply_async(args=[file_id, video_url])  # Updated task call
    return {"task_id": task.id}

@router.post("/delete_GCS_Video")
def delete_GCS_video(fileName : str):
    return delete_gcs_file(BUCKET_NAME, fileName)

@router.get("/task_status/{task_id}")
async def get_task_status(task_id: str):
    """Check Celery task status."""
    task_result = processing.process_video_task.AsyncResult(task_id)
    return {"task_id": task_id, "status": task_result.status}