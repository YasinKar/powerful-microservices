import asyncio
import io

import pytest
from fastapi import HTTPException, UploadFile
from starlette.datastructures import Headers

from core.config import settings
from utils.upload import save_upload_file


def make_upload(filename: str, content: bytes, content_type: str) -> UploadFile:
    file_obj = io.BytesIO(content)
    return UploadFile(filename=filename, file=file_obj, headers=Headers({"content-type": content_type}))


def test_save_upload_file_success(tmp_path, monkeypatch):
    monkeypatch.setattr(type(settings), "MEDIA_ROOT", tmp_path, raising=False)
    upload = make_upload("a.jpg", b"hello", "image/jpeg")

    path, size = asyncio.run(save_upload_file(upload, "products"))

    assert path.startswith("products/")
    assert size == 5


def test_save_upload_file_rejects_invalid_type(tmp_path, monkeypatch):
    monkeypatch.setattr(type(settings), "MEDIA_ROOT", tmp_path, raising=False)
    upload = make_upload("a.txt", b"hello", "text/plain")

    with pytest.raises(HTTPException) as exc:
        asyncio.run(save_upload_file(upload, "products"))

    assert exc.value.status_code == 400


def test_save_upload_file_rejects_oversize(tmp_path, monkeypatch):
    monkeypatch.setattr(type(settings), "MEDIA_ROOT", tmp_path, raising=False)
    monkeypatch.setattr(type(settings), "MAX_FILE_SIZE", 3, raising=False)
    upload = make_upload("a.jpg", b"hello", "image/jpeg")

    with pytest.raises(HTTPException) as exc:
        asyncio.run(save_upload_file(upload, "products"))

    assert exc.value.status_code == 400
