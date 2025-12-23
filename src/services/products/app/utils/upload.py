from pathlib import Path
import uuid
import aiofiles

from fastapi import UploadFile, HTTPException

from core.config import settings

async def save_upload_file(
    file: UploadFile,
    subdir: str
) -> tuple[str, int]:
    if file.content_type not in settings.ALLOWED_UPLOAD_TYPES:
        raise HTTPException(400, "Invalid file type")

    ext = Path(file.filename).suffix
    filename = f"{uuid.uuid4()}{ext}"

    dir_path = settings.MEDIA_ROOT / subdir
    dir_path.mkdir(parents=True, exist_ok=True)

    file_path = dir_path / filename

    size = 0
    async with aiofiles.open(file_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > settings.MAX_FILE_SIZE:
                raise HTTPException(400, "File too large")
            await f.write(chunk)

    return f"{subdir}/{filename}", size