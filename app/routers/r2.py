from fastapi import APIRouter, HTTPException
from app.services.storage.storage_service import StorageService
from app.schemas.video_schemas import UploadUrlRequest, UploadUrlResponse, VideoResponse
from app.exceptions import AppException
from app.logging_config import get_logger
from app.utils.response_utils import create_success_response

logger = get_logger(__name__)
router = APIRouter(prefix="/r2", tags=["r2"])


@router.post("/presign", response_model=UploadUrlResponse)
async def generate_upload_url(request: UploadUrlRequest):
    """Generate a presigned URL for uploading a video file to R2.

    Validation of file name and file size occurs before the signed URL is generated.
    """
    try:
        storage_service = StorageService()
        upload_url, file_id = storage_service.generate_presigned_url(
            file_name=request.file_name,
            file_size=request.file_size,
        )
        return UploadUrlResponse(upload_url=upload_url, file_id=file_id)
    except AppException as e:
        logger.error(f"Error generating upload URL: {e.message}", extra={"extra_fields": {"file_name": request.file_name, "error_code": e.code}})
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
    except Exception as e:
        logger.error(f"Unexpected error generating upload URL: {str(e)}", exc_info=True, extra={"extra_fields": {"file_name": request.file_name}})
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/files/{file_id}", response_model=VideoResponse)
async def delete_r2_file(file_id: str):
    """Delete a video file from R2 storage."""
    try:
        storage_service = StorageService()
        storage_service.delete_file(file_id)
        return create_success_response(
            message="File deleted from R2 storage successfully"
        )
    except AppException as e:
        logger.error(f"Error deleting file from R2: {e.message}", extra={"extra_fields": {"file_id": file_id, "error_code": e.code}})
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
    except Exception as e:
        logger.error(f"Unexpected error deleting file from R2: {str(e)}", exc_info=True, extra={"extra_fields": {"file_id": file_id}})
        raise HTTPException(status_code=500, detail="Internal server error")
