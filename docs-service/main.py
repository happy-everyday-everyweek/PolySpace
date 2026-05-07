from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
import os
import uuid
import hashlib
import hmac
import json
import time
import urllib.parse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("docs-service")

app = FastAPI(title="PolySpace Docs Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STORAGE_PATH = os.environ.get("STORAGE_PATH", "d:/PolySpace/data/documents")
ONLYOFFICE_URL = os.environ.get("ONLYOFFICE_URL", "http://localhost:8082")
ONLYOFFICE_JWT_SECRET = os.environ.get("ONLYOFFICE_JWT_SECRET", "polyspace_docs_secret_2026")
POLYSPACE_BACKEND_URL = os.environ.get("POLYSPACE_BACKEND_URL", "http://localhost:8000")

os.makedirs(STORAGE_PATH, exist_ok=True)

DOCUMENTS_DB: dict[str, dict] = {}

FILE_EXTENSIONS = {
    "word": ".docx",
    "cell": ".xlsx",
    "slide": ".pptx",
    "pdf": ".pdf",
}

DOCUMENT_TYPES = {
    ".docx": "word",
    ".xlsx": "cell",
    ".pptx": "slide",
    ".pdf": "pdf",
    ".doc": "word",
    ".xls": "cell",
    ".ppt": "slide",
    ".odt": "word",
    ".ods": "cell",
    ".odp": "slide",
}


def get_file_key(filepath: str) -> str:
    stat = os.stat(filepath)
    raw = f"{filepath}-{stat.st_mtime}-{stat.st_size}"
    return hashlib.md5(raw.encode()).hexdigest()


def create_jwt(payload: dict) -> str:
    import base64
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    signature = hmac.new(ONLYOFFICE_JWT_SECRET.encode(), f"{header}.{payload_b64}".encode(), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    return f"{header}.{payload_b64}.{sig_b64}"


class DocumentInfo(BaseModel):
    id: str
    filename: str
    document_type: str
    file_key: str
    created_at: float
    updated_at: float


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    filename = file.filename or "untitled.docx"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in DOCUMENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file format: {ext}")

    doc_id = str(uuid.uuid4())
    doc_dir = os.path.join(STORAGE_PATH, doc_id)
    os.makedirs(doc_dir, exist_ok=True)
    filepath = os.path.join(doc_dir, filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    file_key = get_file_key(filepath)
    now = time.time()

    DOCUMENTS_DB[doc_id] = {
        "id": doc_id,
        "filename": filename,
        "filepath": filepath,
        "document_type": DOCUMENT_TYPES[ext],
        "file_key": file_key,
        "created_at": now,
        "updated_at": now,
    }

    return {"id": doc_id, "filename": filename, "document_type": DOCUMENT_TYPES[ext]}


@app.post("/api/documents/create")
async def create_document(document_type: str = "word", filename: Optional[str] = None):
    if document_type not in FILE_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid document type: {document_type}")

    ext = FILE_EXTENSIONS[document_type]
    if not filename:
        filename = f"New Document{ext}"

    doc_id = str(uuid.uuid4())
    doc_dir = os.path.join(STORAGE_PATH, doc_id)
    os.makedirs(doc_dir, exist_ok=True)
    filepath = os.path.join(doc_dir, filename)

    template_map = {
        "word": b"PK\x03\x04",
        "cell": b"PK\x03\x04",
        "slide": b"PK\x03\x04",
        "pdf": b"%PDF-1.4\n",
    }
    with open(filepath, "wb") as f:
        f.write(b"")

    file_key = get_file_key(filepath) if os.path.getsize(filepath) > 0 else str(int(time.time()))
    now = time.time()

    DOCUMENTS_DB[doc_id] = {
        "id": doc_id,
        "filename": filename,
        "filepath": filepath,
        "document_type": document_type,
        "file_key": file_key,
        "created_at": now,
        "updated_at": now,
    }

    return {"id": doc_id, "filename": filename, "document_type": document_type}


@app.get("/api/documents")
async def list_documents():
    results = []
    for doc in DOCUMENTS_DB.values():
        results.append({
            "id": doc["id"],
            "filename": doc["filename"],
            "document_type": doc["document_type"],
            "created_at": doc["created_at"],
            "updated_at": doc["updated_at"],
        })
    return results


@app.get("/api/documents/{doc_id}")
async def get_document_info(doc_id: str):
    if doc_id not in DOCUMENTS_DB:
        raise HTTPException(status_code=404, detail="Document not found")
    doc = DOCUMENTS_DB[doc_id]
    return {
        "id": doc["id"],
        "filename": doc["filename"],
        "document_type": doc["document_type"],
        "file_key": doc["file_key"],
        "created_at": doc["created_at"],
        "updated_at": doc["updated_at"],
    }


@app.get("/api/documents/{doc_id}/download")
async def download_document(doc_id: str):
    if doc_id not in DOCUMENTS_DB:
        raise HTTPException(status_code=404, detail="Document not found")
    doc = DOCUMENTS_DB[doc_id]
    if not os.path.exists(doc["filepath"]):
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(doc["filepath"], filename=doc["filename"])


@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str):
    if doc_id not in DOCUMENTS_DB:
        raise HTTPException(status_code=404, detail="Document not found")
    doc = DOCUMENTS_DB.pop(doc_id)
    doc_dir = os.path.join(STORAGE_PATH, doc_id)
    if os.path.exists(doc_dir):
        import shutil
        shutil.rmtree(doc_dir)
    return {"status": "deleted"}


@app.get("/api/documents/{doc_id}/editor-config")
async def get_editor_config(doc_id: str, mode: str = "edit"):
    if doc_id not in DOCUMENTS_DB:
        raise HTTPException(status_code=404, detail="Document not found")
    doc = DOCUMENTS_DB[doc_id]

    host = os.environ.get("DOCS_SERVICE_HOST", "localhost")
    port = os.environ.get("DOCS_SERVICE_PORT", "8084")

    file_url = f"http://{host}:{port}/api/documents/{doc_id}/download"
    callback_url = f"http://{host}:{port}/api/documents/{doc_id}/callback"

    doc_type = doc["document_type"]
    file_key = get_file_key(doc["filepath"]) if os.path.exists(doc["filepath"]) else doc["file_key"]

    config = {
        "document": {
            "fileType": os.path.splitext(doc["filename"])[1].lstrip("."),
            "key": file_key,
            "title": doc["filename"],
            "url": file_url,
        },
        "documentType": doc_type,
        "editorConfig": {
            "mode": mode if doc_type != "pdf" else "view",
            "callbackUrl": callback_url,
            "lang": "zh-CN",
            "customization": {
                "autosave": True,
                "forcesave": True,
                "compactHeader": False,
                "compactToolbar": False,
                "toolbarNoTabs": False,
                "uiTheme": "theme-light",
            },
        },
    }

    token = create_jwt(config)
    config["token"] = token

    return config


@app.post("/api/documents/{doc_id}/callback")
async def onlyoffice_callback(doc_id: str, request: Request):
    if doc_id not in DOCUMENTS_DB:
        raise HTTPException(status_code=404, detail="Document not found")

    body = await request.json()
    logger.info(f"Callback for doc {doc_id}: status={body.get('status')}")

    status = body.get("status")

    if status == 2 or status == 3 or status == 6:
        download_url = body.get("url")
        if download_url:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(download_url)
                if response.status_code == 200:
                    doc = DOCUMENTS_DB[doc_id]
                    with open(doc["filepath"], "wb") as f:
                        f.write(response.content)
                    doc["file_key"] = get_file_key(doc["filepath"])
                    doc["updated_at"] = time.time()
                    logger.info(f"Document {doc_id} saved successfully")

    return {"error": 0}


@app.post("/api/documents/{doc_id}/save")
async def force_save_document(doc_id: str):
    if doc_id not in DOCUMENTS_DB:
        raise HTTPException(status_code=404, detail="Document not found")

    doc = DOCUMENTS_DB[doc_id]
    doc_type = doc["document_type"]

    command_url = f"{ONLYOFFICE_URL}/coauthoring/CommandService.ashx"
    command = {
        "c": "forcesave",
        "key": doc["file_key"],
    }
    token = create_jwt(command)
    command["token"] = token

    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.post(command_url, json=command)
        result = response.json()

    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8084)
