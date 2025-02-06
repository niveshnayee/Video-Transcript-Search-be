from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import video

app = FastAPI()

app.include_router(video.router)

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

@app.get("/")
async def root():
    return {"message": "Welcome to the YouTube Video Transcript Search API!"}
