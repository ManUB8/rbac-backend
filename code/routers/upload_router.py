from fastapi import APIRouter, File, UploadFile
from r2_service import upload_image_to_r2

router = APIRouter(prefix="/upload/v1", tags=["Upload"])


@router.post("/image-activities")
async def upload_image(file: UploadFile = File(...)):
    result = await upload_image_to_r2(file=file, folder="activities")
    return {
        "message": "Upload image activities successfully",
        "data": result,
    }


@router.post("/student-image")
async def upload_student_image(file: UploadFile = File(...)):
    result = await upload_image_to_r2(file=file, folder="students")
    return {
        "message": "Upload student image successfully",
        "data": result,
    }