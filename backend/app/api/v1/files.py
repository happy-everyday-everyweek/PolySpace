import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.api.v1.auth import get_current_user
from app.services.auth_service import User

router = APIRouter()

UPLOAD_DIR = os.path.join(os.getcwd(), "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_UPLOAD_SIZE = 50 * 1024 * 1024

_file_registry: dict[str, dict] = {}


def _safe_join(base_dir: str, rel_path: str) -> str:
    base = Path(base_dir).resolve()
    target = (base / rel_path).resolve()
    if not str(target).startswith(str(base) + os.sep) and target != base:
        raise HTTPException(status_code=400, detail="Invalid path")
    return str(target)


def _scan_dir(base_dir: str, rel_path: str = "") -> list[dict]:
    items = []
    try:
        full_path = _safe_join(base_dir, rel_path)
    except HTTPException:
        return items
    if not os.path.isdir(full_path):
        return items
    for name in sorted(os.listdir(full_path)):
        fp = os.path.join(full_path, name)
        entry_rel = os.path.join(rel_path, name) if rel_path else name
        if os.path.isfile(fp):
            stat = os.stat(fp)
            items.append({
                "name": name,
                "path": entry_rel.replace("\\", "/"),
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "type": "file",
            })
        elif os.path.isdir(fp):
            items.append({
                "name": name,
                "path": entry_rel.replace("\\", "/"),
                "type": "directory",
            })
    return items


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), subdir: str = "", current_user: Optional[User] = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    allowed_ext = {
        ".txt", ".md", ".json", ".csv", ".xlsx", ".xls", ".docx", ".doc",
        ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp",
        ".py", ".js", ".ts", ".html", ".css", ".sql", ".sh",
        ".zip", ".tar", ".gz",
    }
    _, ext = os.path.splitext(file.filename.lower())
    if ext not in allowed_ext:
        raise HTTPException(status_code=400, detail=f"File type {ext} not allowed")
    if ".." in subdir or subdir.startswith("/") or subdir.startswith("\\"):
        raise HTTPException(status_code=400, detail="Invalid subdir")
    dest_dir = _safe_join(UPLOAD_DIR, subdir)
    os.makedirs(dest_dir, exist_ok=True)
    file_id = str(uuid.uuid4())
    dest_path = os.path.join(dest_dir, file.filename)
    if os.path.exists(dest_path):
        base, ext_part = os.path.splitext(file.filename)
        dest_path = os.path.join(dest_dir, f"{base}_{file_id[:8]}{ext_part}")
    chunks = []
    total_size = 0
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=400, detail="File too large (max 50MB)")
        chunks.append(chunk)
    with open(dest_path, "wb") as f:
        for chunk in chunks:
            f.write(chunk)
    rel_path = os.path.relpath(dest_path, UPLOAD_DIR).replace("\\", "/")
    _file_registry[file_id] = {
        "file_id": file_id,
        "filename": file.filename,
        "path": rel_path,
        "size": total_size,
        "content_type": file.content_type or "application/octet-stream",
    }
    return {
        "file_id": file_id,
        "filename": file.filename,
        "size": total_size,
        "path": rel_path,
        "status": "uploaded",
    }


@router.get("/list")
async def list_files(path: Optional[str] = Query(None), current_user: Optional[User] = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    rel = path or ""
    try:
        _safe_join(UPLOAD_DIR, rel)
    except HTTPException:
        raise HTTPException(status_code=400, detail="Invalid path")
    items = _scan_dir(UPLOAD_DIR, rel)
    return {"files": items, "path": rel or "/"}


@router.get("/read/{file_id}")
async def read_file(file_id: str, current_user: Optional[User] = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    info = _file_registry.get(file_id)
    if not info:
        for fid, reg in _file_registry.items():
            if reg.get("path") == file_id:
                info = reg
                break
    if not info:
        full_path = os.path.join(UPLOAD_DIR, file_id)
        if os.path.isfile(full_path):
            stat = os.stat(full_path)
            info = {"path": file_id, "size": stat.st_size}
        else:
            raise HTTPException(status_code=404, detail="File not found")
    full_path = os.path.join(UPLOAD_DIR, info["path"])
    resolved = Path(full_path).resolve()
    upload_root = Path(UPLOAD_DIR).resolve()
    if not str(resolved).startswith(str(upload_root) + os.sep) and resolved != upload_root:
        raise HTTPException(status_code=400, detail="Invalid path")
    if not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    text_ext = {".txt", ".md", ".json", ".csv", ".py", ".js", ".ts", ".html", ".css", ".sql", ".sh", ".svg", ".xml", ".yaml", ".yml", ".toml"}
    _, ext = os.path.splitext(full_path.lower())
    if ext in text_ext:
        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return {"file_id": file_id, "content": content, "size": info.get("size", len(content)), "type": "text"}
    else:
        return {"file_id": file_id, "content": None, "size": info.get("size", 0), "type": "binary", "path": info["path"]}


@router.delete("/delete/{file_id}")
async def delete_file(file_id: str, current_user: Optional[User] = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    info = _file_registry.get(file_id)
    if not info:
        raise HTTPException(status_code=404, detail="File not found")
    full_path = os.path.join(UPLOAD_DIR, info["path"])
    if os.path.isfile(full_path):
        os.remove(full_path)
    del _file_registry[file_id]
    return {"status": "ok", "file_id": file_id}


@router.get("/download/{file_id}")
async def download_file(file_id: str, current_user: Optional[User] = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    info = _file_registry.get(file_id)
    if not info:
        for fid, reg in _file_registry.items():
            if reg.get("path") == file_id:
                info = reg
                break
    if not info:
        full_path = os.path.join(UPLOAD_DIR, file_id)
        if os.path.isfile(full_path):
            info = {"path": file_id, "filename": os.path.basename(full_path)}
        else:
            raise HTTPException(status_code=404, detail="File not found")
    full_path = os.path.join(UPLOAD_DIR, info["path"])
    resolved = Path(full_path).resolve()
    upload_root = Path(UPLOAD_DIR).resolve()
    if not str(resolved).startswith(str(upload_root) + os.sep) and resolved != upload_root:
        raise HTTPException(status_code=400, detail="Invalid path")
    if not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    filename = info.get("filename", os.path.basename(full_path))
    return FileResponse(path=full_path, filename=filename, media_type="application/octet-stream")


class FileWriteRequest(BaseModel):
    path: str
    content: str
    subdir: str = ""


@router.post("/write")
async def write_file(req: FileWriteRequest, current_user: Optional[User] = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if ".." in req.path or req.path.startswith("/") or req.path.startswith("\\"):
        raise HTTPException(status_code=400, detail="Invalid path")
    dest_dir = _safe_join(UPLOAD_DIR, req.subdir)
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, req.path)
    resolved = Path(dest_path).resolve()
    upload_root = Path(UPLOAD_DIR).resolve()
    if not str(resolved).startswith(str(upload_root) + os.sep) and resolved != upload_root:
        raise HTTPException(status_code=400, detail="Invalid path")
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(req.content)
    file_id = str(uuid.uuid4())
    rel_path = os.path.relpath(dest_path, UPLOAD_DIR).replace("\\", "/")
    _file_registry[file_id] = {
        "file_id": file_id,
        "filename": os.path.basename(dest_path),
        "path": rel_path,
        "size": len(req.content.encode("utf-8")),
        "content_type": "text/plain",
    }
    return {"file_id": file_id, "filename": os.path.basename(dest_path), "path": rel_path, "status": "saved"}
