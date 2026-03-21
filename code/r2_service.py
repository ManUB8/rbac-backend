import os
import uuid
import boto3
from dotenv import load_dotenv
from fastapi import UploadFile, HTTPException

load_dotenv()

R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
R2_PUBLIC_BASE_URL = os.getenv("R2_PUBLIC_BASE_URL")

if not all([
    R2_ACCOUNT_ID,
    R2_ACCESS_KEY_ID,
    R2_SECRET_ACCESS_KEY,
    R2_BUCKET_NAME,
    R2_PUBLIC_BASE_URL,
]):
    raise ValueError("Missing one or more R2 environment variables")

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

s3_client = boto3.client(
    "s3",
    endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    region_name="auto",
)


async def upload_image_to_r2(file: UploadFile, folder: str = "activities") -> dict:
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, PNG, WEBP, GIF files are allowed",
        )

    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="Empty file is not allowed")

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File size must not exceed 5 MB",
        )

    ext = ALLOWED_IMAGE_TYPES[file.content_type]
    unique_name = f"{uuid.uuid4().hex}{ext}"
    object_key = f"{folder}/{unique_name}"

    try:
        s3_client.put_object(
            Bucket=R2_BUCKET_NAME,
            Key=object_key,
            Body=content,
            ContentType=file.content_type,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    file_url = f"{R2_PUBLIC_BASE_URL.rstrip('/')}/{object_key}"

    return {
        "file_name": unique_name,
        "object_key": object_key,
        "file_url": file_url,
        "content_type": file.content_type,
        "size": len(content),
    }


def delete_file_from_r2(object_key: str) -> bool:
    try:
        s3_client.delete_object(
            Bucket=R2_BUCKET_NAME,
            Key=object_key,
        )
        return True
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")