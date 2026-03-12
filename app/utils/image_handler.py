import uuid
from fastapi import UploadFile
from PIL import Image
import io
from supabase import create_client
from app.core.config import (
    MAX_UPLOAD_SIZE, ALLOWED_EXTENSIONS,
    SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_BUCKET
)


def _get_supabase_client():
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


async def save_upload_file(upload_file: UploadFile) -> str:
    """Process image, upload to Supabase Storage, return public URL"""

    # Validate file extension
    file_ext = upload_file.filename.split('.')[-1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f'File type .{file_ext} not allowed')

    # Read file and validate size
    contents = await upload_file.read()
    if len(contents) > MAX_UPLOAD_SIZE:
        raise ValueError(f'File size exceeds {MAX_UPLOAD_SIZE / 1024 / 1024}MB limit')

    # Validate and optimize image
    try:
        image = Image.open(io.BytesIO(contents))
        if image.mode in ('RGBA', 'LA', 'P'):
            bg = Image.new('RGB', image.size, (255, 255, 255))
            bg.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = bg

        max_dimension = 2000
        if image.width > max_dimension or image.height > max_dimension:
            image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

        output = io.BytesIO()
        image.save(output, 'JPEG', quality=85)
        output.seek(0)
        image_bytes = output.read()
    except Exception as e:
        raise ValueError(f'Error processing image: {str(e)}')

    # Upload to Supabase Storage
    filename = f"{uuid.uuid4()}.jpg"
    supabase = _get_supabase_client()
    supabase.storage.from_(SUPABASE_BUCKET).upload(
        path=filename,
        file=image_bytes,
        file_options={"content-type": "image/jpeg"}
    )

    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{filename}"
    return public_url


async def delete_upload_file(image_url: str) -> None:
    """Delete image from Supabase Storage given its public URL"""
    try:
        filename = image_url.split(f"/{SUPABASE_BUCKET}/")[-1]
        supabase = _get_supabase_client()
        supabase.storage.from_(SUPABASE_BUCKET).remove([filename])
    except Exception:
        pass


def delete_upload_file_sync(image_url: str) -> None:
    """Synchronous version for use in non-async routes"""
    try:
        filename = image_url.split(f"/{SUPABASE_BUCKET}/")[-1]
        supabase = _get_supabase_client()
        supabase.storage.from_(SUPABASE_BUCKET).remove([filename])
    except Exception:
        pass
