from typing import List
from fastapi import APIRouter, HTTPException, Form, BackgroundTasks
from app.services.video_processing import VideoProcessingService  # Updated import
from app.models.video_models import SearchQuery, VideoCreate, VideoResponse
from urllib.parse import urlparse, parse_qs
from fastapi.responses import JSONResponse
from google.cloud import storage
import os
from dotenv import load_dotenv
import uuid
from datetime import timedelta
from bson import ObjectId
from celery.result import AsyncResult
from app.database import MongoDBClient



# Initialize MongoDB client
db_client = MongoDBClient()
videos_collection = db_client.get_collection("videos")

load_dotenv()  # Load environment variables from .env file
router = APIRouter()


# Set Google Cloud credentials (ensure the key file is in your working directory)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
# Define your bucket name
BUCKET_NAME = os.getenv("BUCKET_NAME")
# Initialize the Google Cloud Storage client
storage_client = storage.Client()

@router.get("/videos")
async def get_all_videos():
    """
    Get a list of all uploaded videos with metadata.
    """
    try:
        videos = videos_collection.find()
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
        return VideoResponse(
            success=False, message=f"An error occurred while fetching videos: {str(e)}", data=None
        )




@router.get("/video/{video_id}")
async def get_video_details(video_id: str):
    """
    Get the details of a specific video by its ID.
    """
    try:
        video = videos_collection.find_one({"_id": ObjectId(video_id)})
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
        
        elif video.get("file_id"):
            # If 'file_id' exists, fetch the video file from GridFS
            ile_id_obj = ObjectId(video["file_id"])
            video_file = fs.get(ile_id_obj)
            response_data["file"] = str(video["file_id"])  # Send the file ID as a reference

            # Return the video file as a streaming response
            return StreamingResponse(
                    BytesIO(video_file.read()), 
                    media_type="video/mp4", 
                    headers={"Content-Disposition": "attachment; filename=video.mp4"}
                )
        
        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching video details: {str(e)}")


@router.delete("/delete_video/{video_id}")
def delete_video(video_id: str):
    try:
        try:
            video_id_obj = ObjectId(video_id)  # Convert video_id to ObjectId
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid video ID format")

        # Step 1: Get video metadata from MongoDB
        video_data = videos_collection.find_one({"_id": video_id_obj})
        
        if not video_data:
            raise HTTPException(status_code=404, detail="Video not found")

        # Step 2: Get the unique filename of the video
        unique_filename = video_data["file_id"]
        
        # Step 3: Delete the video file from GCS
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(unique_filename)
        blob.delete()  # Delete the blob from GCS
        
        # Step 4: Delete the video metadata from MongoDB
        videos_collection.delete_one({"_id": video_id_obj})
        
        return {"success": True, "message": "Video deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# Function to generate signed URL for upload
def generate_signed_url_for_upload(bucket_name, object_name, expiration_minutes: int = 15):
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(object_name)
    
    expiration = timedelta(expiration_minutes)  # Signed URL validity for 15 minutes
    
    signed_url = blob.generate_signed_url(
        expiration=expiration,
        method="PUT",
        content_type="video/mp4",  # Ensure it matches content type
    )
    return signed_url


@router.post("/generate_upload_url")
def get_signed_url(video_name: str = Form(...)):
    """Generate a signed URL so the frontend can upload directly to GCS."""
    unique_filename = f"{uuid.uuid4()}_{video_name}"
    signed_url = generate_signed_url_for_upload(BUCKET_NAME, unique_filename)

    return {"upload_url": signed_url, "file_id": unique_filename}


def delete_gcs_file(bucket_name, file_name):
    """Deletes a file from Google Cloud Storage."""

    bucket =  storage_client.bucket(bucket_name)
    blob =  bucket.blob(file_name)
    
    blob.delete()
    print(f"Deleted {file_name} from {bucket_name}")

# Example usage:
# delete_gcs_file("your-bucket-name", "your-object-name")

@router.post("/upload_video", response_model=VideoResponse)
def upload_video(
    background_tasks: BackgroundTasks,
    video_name: str = Form(...),
    video_category: str = Form(...),
    video_description: str = Form(...),
    fileId: str = Form(...)
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
        video_dict = video_data.dict()
        inserted_id = videos_collection.insert_one(video_dict).inserted_id


        # Step 5: Start background task for transcription
        # background_tasks.add_task(process_video_from_url, str(inserted_id), video_url)

         # Start Celery task
        task = VideoProcessingService.process_video_from_url.apply_async(args=[str(inserted_id), video_url])  # Updated task call

         # Return success response
        return JSONResponse(
            status_code=200,
            content=VideoResponse(
                success=True,
                message="Video uploaded and processing started successfully",
                data={
                    "video_id": str(inserted_id),
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
        delete_gcs_file(BUCKET_NAME, fileId)
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
        delete_gcs_file(BUCKET_NAME, fileId)
        return JSONResponse(
            status_code=500,
            content=VideoResponse(
                success=False,
                message=f"An error occurred: {str(e)}",
                data=None,
            ).dict(),
        )

@router.post("/video/{video_id}/search")
async def search_transcript(video_id: str, query: SearchQuery):
    """
    Search for the query text in the transcript and return results with timestamps.
    """

    try:
        # Fetch video by ID
        video = videos_collection.find_one({"_id": ObjectId(video_id)})
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        transcript = video.get("transcript", [])
        if not transcript:
            raise HTTPException(status_code=404, detail="Transcript not found")

        video_url = video.get("url")
        if not video_url:
            raise HTTPException(status_code=404, detail="Video URL not found")

        # Search in the transcript
        results = []
        for idx, entry in enumerate(transcript):
            if query.query.lower() in entry["text"].lower():
                results.append({
                    "seconds": entry["timestamp"],
                    "time": seconds_to_video_time(entry["timestamp"]),
                    "text": " ".join(
                        [entry["text"]] +
                        [transcript[i]["text"] for i in range(idx + 1, min(idx + 4, len(transcript)))]
                    ),
                    "video_link": f"{video_url}#t={int(entry['timestamp'])}s"
                })

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

def seconds_to_video_time(seconds):

    minutes, remaining_seconds = divmod(seconds, 60)

    video_time = f"{minutes:.0f}:{(remaining_seconds / 60):.2f}"

    return video_time


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
    task_result = AsyncResult(task_id)
    return {"task_id": task_id, "status": task_result.status}

{
        # Generate a unique filename for the video
        # unique_filename = f"{uuid.uuid4()}_{file.filename}"

        # Upload file to Google Cloud Storage
        # bucket = storage_client.bucket(BUCKET_NAME)
        # blob = bucket.blob(unique_filename)
        # blob.upload_from_file(file.file, content_type=file.content_type)
        # blob.make_public()

         # Step 1: Generate signed URL for uploading the video to GCS
        # signed_url = generate_signed_url_for_upload(BUCKET_NAME, unique_filename)

        # Step 2: Upload video file to GCS using the signed URL
        # video_data = await file.read()  # Read file content from the frontend

        # Make the PUT request to upload the file
        # response = requests.put(signed_url, data=video_data, headers={"Content-Type": file.content_type})

        # if response.status_code != 200:
        #     raise HTTPException(status_code=500, detail="Failed to upload video to Google Cloud Storage")
        }