import os
from typing import List, Dict, Any, TYPE_CHECKING
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from minio import get_minio_client, get_minio_bucket_name
from auth import current_active_user
from datetime import timedelta
import tempfile
import uuid

if TYPE_CHECKING:
    from minio import Minio
    from models.user import User

MAX_FILE_SIZE = 50 * 1024 * 1024 * 1024  # 50GB in bytest
techpack_router = APIRouter(prefix="/api/v1")


class InitiateUploadRequest(BaseModel):
    filename: str
    filesize: int
    content_type: str


class CompleteUploadRequest(BaseModel):
    upload_id: str
    parts: List[Dict[str, Any]]


@techpack_router.post("/upload/initiate")
async def initiate_multipart_upload(
    filename: str, filesize: int, current_user: User = Depends(current_active_user)
) -> Dict[str, str]:
    """Generate TUS upload URL with auth check

    Args:
        filename (str): _description_
        filesize (int): _description_
        current_user (User, optional): _description_. Defaults to Depends(current_active_user).

    Raises:
        HTTPException: _description_

    Returns:
        Dict[str, str]: return TUS endpoint object with user context
    """
    upload_limit = 50 * 1024 * 1024 * 1024  # 50gb
    max_chunk_size = 10 * 1024 * 1024

    if filesize > upload_limit:
        raise HTTPException(413, "File too large")

    return {"upload_url": "http://localhost:1081/files/", "user_id": current_user.id, "max_chunk_size": max_chunk_size}


@techpack_router.post("/upload/complete")
async def complete_upload(
    tus_url: str,
    current_user: "User" = Depends(current_active_user),
    minio_client: "Minio" = Depends(get_minio_client),
    minio_bucket_name: str = Depends(get_minio_bucket_name),
) -> Dict[str, Any]:
    """Called after TUS upload completes

    Args:
        tus_url (str): _description_
        current_user (User, optional): _description_. Defaults to Depends(current_active_user).
        minio_client (Minio, optional): _description_. Defaults to Depends(get_minio_client).

    Raises:
        HTTPException: _description_

    Returns:
        Dict[str, Any]: Object containing presigned url
    """
    object_name = tus_url.split("/")[1]
    presigned_url = minio_client.presigned_get_object(
        bucket_name=minio_bucket_name,
        object_name=f"user_{current_user.id}/{object_name}",
        expires=timedelta(days=7),
    )

    return {
        "object_name": object_name,
        "presigned_url": presigned_url,
    }
