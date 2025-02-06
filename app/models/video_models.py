
from pydantic import BaseModel
from typing import List, Optional


class VideoRequest(BaseModel):
    """
    Model for the video upload request.
    - `url`: The YouTube video URL provided by the user.
    """
    url: str


class SearchQuery(BaseModel):
    """
    Model for the transcript search query.
    - `query`: The text to search in the transcript.
    """
    query: str


# Define the Transcript item
class TranscriptItem(BaseModel):
    timestamp: int  
    text: str

# Define the Video model
class VideoCreate(BaseModel):
    name: str
    category: str
    description: str
    url: str  # URL 
    file_id : str
    transcript: Optional[List[TranscriptItem]] = []  # List of TranscriptItem objects
    

# # Response Model for retrieving a Video
# class VideoResponse(VideoCreate):
#     video_id: str

class VideoResponse(BaseModel):
    success: bool
    message: str
    data: dict = None
