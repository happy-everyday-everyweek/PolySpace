import logging
import os
from typing import Optional

from app.api.v1.auth import get_current_user
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, Depends

from app.services.doc_conversion_service import doc_conversion_service
from app.services.libreoffice_service import libreoffice_service

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOAD_DIR = os.path.join(os.getcwd(), "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/libreoffice/status")
async def libreoffice_status(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    info = await libreoffice_service.get_info()
    return info


@router.post("/convert")
async def convert_document(
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    file: UploadFile = File(...),
    output_format: str = Query(
        "pdf",
        description="Target format: pdf, docx, xlsx, pptx, odt, ods, odp, html, txt, csv, rtf",
    ),
    source_format: Optional[str] = Query(None, description="Source format (auto-detected if not specified)"),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    content = await file.read()
    if len(content) > 200 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 200MB)")

    import tempfile
    import uuid

    ext = os.path.splitext(file.filename.lower())[1]
    src_format = source_format or ext.lstrip(".") or "unknown"

    with tempfile.TemporaryDirectory(dir=UPLOAD_DIR) as tmpdir:
        input_filename = str(uuid.uuid4()) + ext
        input_path = os.path.join(tmpdir, input_filename)
        with open(input_path, "wb") as f:
            f.write(content)

        result = await doc_conversion_service.convert_file(input_path, output_format, src_format)
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        output_path = result.get("output_path", "")
        if output_path and os.path.isfile(output_path):
            from fastapi.responses import FileResponse
            output_filename = os.path.splitext(file.filename)[0] + f".{output_format}"
            return FileResponse(
                output_path,
                media_type=_media_type(output_format),
                filename=output_filename,
            )

        raise HTTPException(status_code=500, detail="Conversion output file not found")


@router.post("/html/to/docx")
async def html_to_docx(
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    html_content: str = Query(..., description="HTML content to convert"),
    title: str = Query("Document", description="Document title"),
):
    result = await doc_conversion_service.html_to_docx(html_content, title)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    output_path = result.get("output_path", "")
    if output_path and os.path.isfile(output_path):
        from fastapi.responses import FileResponse

        docx_mime = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        return FileResponse(
            output_path, media_type=docx_mime, filename=f"{title}.docx"
        )
    raise HTTPException(status_code=500, detail="Conversion output file not found")


@router.post("/html/to/pdf")
async def html_to_pdf(
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    html_content: str = Query(..., description="HTML content to convert"),
    title: str = Query("Document", description="Document title"),
):
    result = await doc_conversion_service.html_to_pdf(html_content, title)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    output_path = result.get("output_path", "")
    if output_path and os.path.isfile(output_path):
        from fastapi.responses import FileResponse
        return FileResponse(output_path, media_type="application/pdf", filename=f"{title}.pdf")
    raise HTTPException(status_code=500, detail="Conversion output file not found")


@router.post("/file/convert")
async def convert_file_by_path(
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    file_path: str = Query(..., description="Path to the file to convert"),
    output_format: str = Query("pdf", description="Target format"),
    source_format: Optional[str] = Query(None, description="Source format"),
):
    abs_path = os.path.abspath(file_path)
    if not abs_path.startswith(os.path.abspath(UPLOAD_DIR)) and not abs_path.startswith(os.path.abspath("data")):
        raise HTTPException(status_code=403, detail="Access denied: file path outside allowed directories")
    if not os.path.isfile(abs_path):
        raise HTTPException(status_code=404, detail="File not found")
    result = await doc_conversion_service.convert_file(abs_path, output_format, source_format)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    output_path = result.get("output_path", "")
    if output_path and os.path.isfile(output_path):
        from fastapi.responses import FileResponse
        filename = os.path.splitext(os.path.basename(file_path))[0] + f".{output_format}"
        return FileResponse(output_path, media_type=_media_type(output_format), filename=filename)
    raise HTTPException(status_code=500, detail="Conversion output file not found")


def _media_type(fmt: str) -> str:
    types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "odt": "application/vnd.oasis.opendocument.text",
        "ods": "application/vnd.oasis.opendocument.spreadsheet",
        "odp": "application/vnd.oasis.opendocument.presentation",
        "html": "text/html",
        "txt": "text/plain",
        "csv": "text/csv",
        "rtf": "application/rtf",
    }
    return types.get(fmt, "application/octet-stream")
