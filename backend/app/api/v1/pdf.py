import logging
import os
import re
import uuid
from pathlib import Path
from typing import Optional

from app.api.v1.auth import get_current_user
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, Depends

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOAD_DIR = os.path.join(os.getcwd(), "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    _, ext = os.path.splitext(file.filename.lower())
    if ext != ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    content = await file.read()
    if len(content) > 100 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 100MB)")
    file_id = str(uuid.uuid4())
    dest_path = os.path.join(UPLOAD_DIR, file_id + ".pdf")
    with open(dest_path, "wb") as f:
        f.write(content)
    return {
        "file_id": file_id,
        "filename": file.filename,
        "size": len(content),
        "path": file_id + ".pdf",
        "status": "uploaded",
    }


@router.get("/info/{file_id}")
async def get_pdf_info(file_id: str, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    file_path = _find_pdf(file_id)
    try:
        import fitz
        with fitz.open(file_path) as doc:
            meta = doc.metadata
            pages = []
            for i in range(len(doc)):
                page = doc[i]
                text = page.get_text()
                pages.append({
                    "page_number": i,
                    "width": round(page.rect.width, 2),
                    "height": round(page.rect.height, 2),
                    "rotation": page.rotation,
                    "text_length": len(text),
                    "text_preview": text[:200] if text else "",
                })
            toc = doc.get_toc()
            bookmarks = [{"level": item[0], "title": item[1], "page": item[2] - 1} for item in toc]
            result = {
                "file_id": file_id,
                "metadata": {
                    "title": meta.get("title", ""),
                    "author": meta.get("author", ""),
                    "subject": meta.get("subject", ""),
                    "keywords": meta.get("keywords", ""),
                    "creator": meta.get("creator", ""),
                    "producer": meta.get("producer", ""),
                    "creationDate": meta.get("creationDate", ""),
                    "modDate": meta.get("modDate", ""),
                },
                "page_count": len(doc),
                "is_encrypted": doc.is_encrypted,
                "pages": pages,
                "bookmarks": bookmarks,
            }
            return result
    except ImportError:
        raise HTTPException(status_code=500, detail="PyMuPDF not installed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/page/{file_id}/{page_num}")
async def get_page_image(file_id: str, page_num: int, dpi: int = Query(150, ge=72, le=300)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    file_path = _find_pdf(file_id)
    try:
        import base64

        import fitz
        with fitz.open(file_path) as doc:
            if page_num < 0 or page_num >= len(doc):
                raise HTTPException(status_code=400, detail=f"Page {page_num} out of range")
            page = doc[page_num]
            pix = page.get_pixmap(dpi=dpi)
            img_bytes = pix.tobytes("png")
            return {
                "page": page_num,
                "width": pix.width,
                "height": pix.height,
                "image_base64": base64.b64encode(img_bytes).decode("ascii"),
            }
    except ImportError:
        raise HTTPException(status_code=500, detail="PyMuPDF not installed")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/text/{file_id}")
async def extract_text(file_id: str, pages: Optional[str] = Query(None)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    file_path = _find_pdf(file_id)
    try:
        import fitz
        with fitz.open(file_path) as doc:
            if pages:
                indices = _parse_page_range(pages, len(doc))
                selected = [doc[i] for i in indices]
            else:
                selected = list(doc)
            text_parts = []
            for page in selected:
                text_parts.append(page.get_text())
            return {"text": "\n\n".join(text_parts), "page_count": len(doc)}
    except ImportError:
        raise HTTPException(status_code=500, detail="PyMuPDF not installed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/watermark")
async def add_watermark(
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    file_id: str = Query(...),
    text: str = Query("WATERMARK"),
    opacity: float = Query(0.15, ge=0, le=1),
    font_size: int = Query(36, ge=8, le=120),
    color: str = Query("#808080"),
    angle: float = Query(-45),
    position: str = Query("center"),
):
    file_path = _find_pdf(file_id)
    try:
        import fitz
        with fitz.open(file_path) as doc:
            color_rgb = _hex_to_rgb(color)
            for page in doc:
                rect = page.rect
                if position == "tile":
                    step_x = rect.width / 3
                    step_y = rect.height / 3
                    for xi in range(3):
                        for yi in range(3):
                            cx = step_x * xi + step_x / 2
                            cy = step_y * yi + step_y / 2
                            _insert_watermark(page, text, cx, cy, font_size, color_rgb, opacity, angle)
                else:
                    cx, cy = _get_position(rect, position)
                    _insert_watermark(page, text, cx, cy, font_size, color_rgb, opacity, angle)
            output_id = str(uuid.uuid4()) + ".pdf"
            output_path = os.path.join(UPLOAD_DIR, output_id)
            doc.save(output_path)
            return {"status": "ok", "output_file_id": output_id, "watermark_text": text}
    except ImportError:
        raise HTTPException(status_code=500, detail="PyMuPDF not installed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/encrypt")
async def encrypt_pdf(
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    file_id: str = Query(...),
    password: str = Query(...),
    owner_password: Optional[str] = Query(None),
    allow_print: bool = Query(True),
    allow_copy: bool = Query(True),
    allow_modify: bool = Query(False),
    allow_annotate: bool = Query(True),
):
    file_path = _find_pdf(file_id)
    try:
        import fitz
        with fitz.open(file_path) as doc:
            owner_pw = owner_password or password
            perm_value = 0
            if allow_print:
                perm_value |= fitz.PDF_PERM_PRINT
            if allow_copy:
                perm_value |= fitz.PDF_PERM_COPY
            if allow_modify:
                perm_value |= fitz.PDF_PERM_MODIFY
            if allow_annotate:
                perm_value |= fitz.PDF_PERM_ANNOTATE
            output_id = str(uuid.uuid4()) + ".pdf"
            output_path = os.path.join(UPLOAD_DIR, output_id)
            doc.save(output_path, encryption=fitz.PDF_ENCRYPT_AES_256, owner_pw=owner_pw, user_pw=password, permissions=perm_value)
            return {"status": "ok", "output_file_id": output_id, "encryption": "AES-256"}
    except ImportError:
        raise HTTPException(status_code=500, detail="PyMuPDF not installed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decrypt")
async def decrypt_pdf(file_id: str = Query(...), password: str = Query(...)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    file_path = _find_pdf(file_id)
    try:
        import fitz
        with fitz.open(file_path) as doc:
            if not doc.is_encrypted:
                raise HTTPException(status_code=400, detail="File is not encrypted")
            rc = doc.authenticate(password)
            if not rc:
                raise HTTPException(status_code=400, detail="Incorrect password")
            output_id = str(uuid.uuid4()) + ".pdf"
            output_path = os.path.join(UPLOAD_DIR, output_id)
            doc.save(output_path)
            return {"status": "ok", "output_file_id": output_id}
    except ImportError:
        raise HTTPException(status_code=500, detail="PyMuPDF not installed")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/merge")
async def merge_pdfs(file_ids: list[str] = Query(...)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if len(file_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 PDF files required")
    try:
        import fitz
        with fitz.open() as merged:
            for fid in file_ids:
                fp = _find_pdf(fid)
                with fitz.open(fp) as doc:
                    merged.insert_pdf(doc)
            output_id = str(uuid.uuid4()) + ".pdf"
            output_path = os.path.join(UPLOAD_DIR, output_id)
            merged.save(output_path)
            return {"status": "ok", "output_file_id": output_id, "merged_count": len(file_ids)}
    except ImportError:
        raise HTTPException(status_code=500, detail="PyMuPDF not installed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/split")
async def split_pdf(file_id: str = Query(...), pages: str = Query(...)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    file_path = _find_pdf(file_id)
    try:
        import fitz
        with fitz.open(file_path) as doc:
            indices = _parse_page_range(pages, len(doc))
            with fitz.open() as new_doc:
                for i in indices:
                    new_doc.insert_pdf(doc, from_page=i, to_page=i)
                output_id = str(uuid.uuid4()) + ".pdf"
                output_path = os.path.join(UPLOAD_DIR, output_id)
                new_doc.save(output_path)
                return {"status": "ok", "output_file_id": output_id, "pages": pages}
    except ImportError:
        raise HTTPException(status_code=500, detail="PyMuPDF not installed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rotate")
async def rotate_pdf(file_id: str = Query(...), angle: int = Query(90), pages: Optional[str] = Query(None)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if angle not in (90, 180, 270):
        raise HTTPException(status_code=400, detail="Angle must be 90, 180, or 270")
    file_path = _find_pdf(file_id)
    try:
        import fitz
        with fitz.open(file_path) as doc:
            if pages:
                indices = _parse_page_range(pages, len(doc))
                for i in indices:
                    doc[i].set_rotation(angle)
            else:
                for page in doc:
                    page.set_rotation(angle)
            output_id = str(uuid.uuid4()) + ".pdf"
            output_path = os.path.join(UPLOAD_DIR, output_id)
            doc.save(output_path)
            return {"status": "ok", "output_file_id": output_id, "angle": angle}
    except ImportError:
        raise HTTPException(status_code=500, detail="PyMuPDF not installed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compress")
async def compress_pdf(file_id: str = Query(...), quality: str = Query("medium")):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    file_path = _find_pdf(file_id)
    try:
        import fitz
        with fitz.open(file_path) as doc:
            original_size = os.path.getsize(file_path)
            output_id = str(uuid.uuid4()) + ".pdf"
            output_path = os.path.join(UPLOAD_DIR, output_id)
            doc.save(output_path, deflate=True, garbage=4, clean=True)
            compressed_size = os.path.getsize(output_path)
            ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
            return {
                "status": "ok",
                "output_file_id": output_id,
                "original_size": original_size,
                "compressed_size": compressed_size,
                "compression_ratio": f"{ratio:.1f}%",
            }
    except ImportError:
        raise HTTPException(status_code=500, detail="PyMuPDF not installed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/convert")
async def convert_pdf(file_id: str = Query(...), format: str = Query("images"), dpi: int = Query(150)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    file_path = _find_pdf(file_id)
    if format == "docx":
        from app.services.doc_conversion_service import doc_conversion_service
        result = await doc_conversion_service.convert_file(file_path, "docx", "pdf")
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        output_path = result.get("output_path", "")
        if output_path and os.path.isfile(output_path):
            from fastapi.responses import FileResponse
            return FileResponse(output_path, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", filename=f"{file_id}.docx")
        raise HTTPException(status_code=500, detail="DOCX conversion output not found")
    try:
        import base64

        import fitz
        with fitz.open(file_path) as doc:
            results = []
            if format == "images":
                for i in range(len(doc)):
                    page = doc[i]
                    pix = page.get_pixmap(dpi=dpi)
                    img_bytes = pix.tobytes("png")
                    results.append({
                        "page": i,
                        "width": pix.width,
                        "height": pix.height,
                        "image_base64": base64.b64encode(img_bytes).decode("ascii"),
                    })
            elif format == "txt":
                text = ""
                for page in doc:
                    text += page.get_text() + "\n\n"
                results.append({"text": text})
            elif format == "html":
                for i in range(len(doc)):
                    page = doc[i]
                    results.append({"page": i, "html": page.get_text("html")})
            return {"status": "ok", "format": format, "results": results}
    except ImportError:
        raise HTTPException(status_code=500, detail="PyMuPDF not installed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/page-numbers")
async def add_page_numbers(
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    file_id: str = Query(...),
    format: str = Query("1/N"),
    position: str = Query("bottom-center"),
):
    file_path = _find_pdf(file_id)
    try:
        import fitz
        with fitz.open(file_path) as doc:
            total = len(doc)
            for i in range(total):
                page = doc[i]
                rect = page.rect
                if format == "- 1 -":
                    num_str = f"- {i + 1} -"
                elif format == "Page 1":
                    num_str = f"Page {i + 1}"
                elif format == "Page 1 of N":
                    num_str = f"Page {i + 1} of {total}"
                else:
                    num_str = f"{i + 1}/{total}"
                font_size = 9
                text_width = fitz.get_text_length(num_str, fontname="helv", fontsize=font_size)
                if "bottom" in position:
                    y = rect.height - 24
                else:
                    y = 24
                if "center" in position:
                    x = (rect.width - text_width) / 2
                elif "right" in position:
                    x = rect.width - text_width - 36
                else:
                    x = 36
                page.insert_text(fitz.Point(x, y), num_str, fontsize=font_size, color=(0.3, 0.3, 0.3))
            output_id = str(uuid.uuid4()) + ".pdf"
            output_path = os.path.join(UPLOAD_DIR, output_id)
            doc.save(output_path)
            return {"status": "ok", "output_file_id": output_id}
    except ImportError:
        raise HTTPException(status_code=500, detail="PyMuPDF not installed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/header-footer")
async def add_header_footer(
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    file_id: str = Query(...),
    header: str = Query(""),
    footer: str = Query(""),
    font_size: int = Query(9),
):
    file_path = _find_pdf(file_id)
    if not header and not footer:
        raise HTTPException(status_code=400, detail="header or footer text required")
    try:
        from datetime import datetime

        import fitz
        with fitz.open(file_path) as doc:
            total = len(doc)
            now = datetime.now().strftime("%Y-%m-%d")
            for i in range(total):
                page = doc[i]
                rect = page.rect
                if header:
                    ht = header.replace("{page}", str(i + 1)).replace("{total}", str(total)).replace("{date}", now)
                    page.insert_text(fitz.Point(72, 36), ht, fontsize=font_size, color=(0.3, 0.3, 0.3))
                if footer:
                    ft = footer.replace("{page}", str(i + 1)).replace("{total}", str(total)).replace("{date}", now)
                    page.insert_text(fitz.Point(72, rect.height - 24), ft, fontsize=font_size, color=(0.3, 0.3, 0.3))
            output_id = str(uuid.uuid4()) + ".pdf"
            output_path = os.path.join(UPLOAD_DIR, output_id)
            doc.save(output_path)
            return {"status": "ok", "output_file_id": output_id}
    except ImportError:
        raise HTTPException(status_code=500, detail="PyMuPDF not installed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/redact")
async def redact_pdf(file_id: str = Query(...), texts: list[str] = Query(...), color: str = Query("#000000")):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    file_path = _find_pdf(file_id)
    try:
        import fitz
        color_rgb = _hex_to_rgb(color)
        with fitz.open(file_path) as doc:
            total = 0
            for page in doc:
                for text in texts:
                    areas = page.search_for(text)
                    for area in areas:
                        page.add_redact_annot(area, fill=color_rgb)
                        total += 1
                page.apply_redactions()
            output_id = str(uuid.uuid4()) + ".pdf"
            output_path = os.path.join(UPLOAD_DIR, output_id)
            doc.save(output_path)
            return {"status": "ok", "output_file_id": output_id, "redactions": total}
    except ImportError:
        raise HTTPException(status_code=500, detail="PyMuPDF not installed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bookmark")
async def manage_bookmark(
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    file_id: str = Query(...),
    action: str = Query("add"),
    title: str = Query(""),
    page: int = Query(0),
    level: int = Query(0),
    index: int = Query(-1),
):
    file_path = _find_pdf(file_id)
    try:
        import fitz
        with fitz.open(file_path) as doc:
            if action == "list":
                toc = doc.get_toc()
                bookmarks = [{"level": item[0], "title": item[1], "page": item[2] - 1} for item in toc]
                return {"bookmarks": bookmarks}
            elif action == "add":
                toc = doc.get_toc()
                toc.append([level + 1, title or "Untitled", page + 1])
                doc.set_toc(toc)
                output_id = str(uuid.uuid4()) + ".pdf"
                output_path = os.path.join(UPLOAD_DIR, output_id)
                doc.save(output_path)
                return {"status": "ok", "output_file_id": output_id}
            elif action == "remove":
                toc = doc.get_toc()
                if 0 <= index < len(toc):
                    toc.pop(index)
                    doc.set_toc(toc)
                    output_id = str(uuid.uuid4()) + ".pdf"
                    output_path = os.path.join(UPLOAD_DIR, output_id)
                    doc.save(output_path)
                    return {"status": "ok", "output_file_id": output_id}
                raise HTTPException(status_code=400, detail="Invalid bookmark index")
            else:
                raise HTTPException(status_code=400, detail="Action must be add, remove, or list")
    except ImportError:
        raise HTTPException(status_code=500, detail="PyMuPDF not installed")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/annotate")
async def annotate_pdf(
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    file_id: str = Query(...),
    page_num: int = Query(0),
    annotation_type: str = Query("highlight"),
    rect: Optional[str] = Query(None),
    content: str = Query(""),
    color: str = Query("#FFFF00"),
    icon: str = Query("Note"),
):
    file_path = _find_pdf(file_id)
    try:
        import fitz
        with fitz.open(file_path) as doc:
            if page_num < 0 or page_num >= len(doc):
                raise HTTPException(status_code=400, detail=f"Page {page_num} out of range")
            page = doc[page_num]
            color_rgb = _hex_to_rgb(color)

            if annotation_type == "highlight":
                if not rect:
                    raise HTTPException(status_code=400, detail="rect required for highlight")
                coords = [float(x) for x in rect.split(",")]
                if len(coords) != 4:
                    raise HTTPException(status_code=400, detail="rect must be x0,y0,x1,y1")
                annot = page.add_highlight_annot(fitz.Rect(coords[0], coords[1], coords[2], coords[3]))
                annot.set_colors(stroke=color_rgb)
                annot.update()
            elif annotation_type == "text":
                if not rect or not content:
                    raise HTTPException(status_code=400, detail="rect and content required for text annotation")
                coords = [float(x) for x in rect.split(",")]
                point = fitz.Point(coords[0], coords[1])
                annot = page.add_text_annot(point, content)
                annot.update()
            elif annotation_type == "stamp":
                if not rect:
                    raise HTTPException(status_code=400, detail="rect required for stamp annotation")
                coords = [float(x) for x in rect.split(",")]
                stamp_map = {
                    "Note": fitz.STAMP_Note, "Comment": fitz.STAMP_Comment, "Help": fitz.STAMP_Help,
                    "Insert": fitz.STAMP_Insert, "Key": fitz.STAMP_Key,
                    "NewParagraph": fitz.STAMP_NewParagraph, "Paragraph": fitz.STAMP_Paragraph,
                }
                stamp_id = stamp_map.get(icon, fitz.STAMP_Note)
                annot = page.add_stamp_annot(fitz.Rect(coords[0], coords[1], coords[2], coords[3]), stamp=stamp_id)
                if content:
                    annot.set_info(content=content)
                annot.update()
            else:
                raise HTTPException(status_code=400, detail="annotation_type must be highlight, text, or stamp")

            output_id = str(uuid.uuid4()) + ".pdf"
            output_path = os.path.join(UPLOAD_DIR, output_id)
            doc.save(output_path)
            return {"status": "ok", "output_file_id": output_id, "annotation_type": annotation_type}
    except ImportError:
        raise HTTPException(status_code=500, detail="PyMuPDF not installed")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/metadata")
async def update_metadata(file_id: str = Query(...), title: str = Query(""), author: str = Query(""), subject: str = Query(""), keywords: str = Query("")):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    file_path = _find_pdf(file_id)
    try:
        import fitz
        with fitz.open(file_path) as doc:
            meta = {}
            if title:
                meta["title"] = title
            if author:
                meta["author"] = author
            if subject:
                meta["subject"] = subject
            if keywords:
                meta["keywords"] = keywords
            if meta:
                doc.set_metadata(meta)
            output_id = str(uuid.uuid4()) + ".pdf"
            output_path = os.path.join(UPLOAD_DIR, output_id)
            doc.save(output_path)
            return {"status": "ok", "output_file_id": output_id}
    except ImportError:
        raise HTTPException(status_code=500, detail="PyMuPDF not installed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{file_id}")
async def download_pdf(file_id: str, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    from fastapi.responses import FileResponse
    file_path = _find_pdf(file_id)
    return FileResponse(file_path, media_type="application/pdf", filename=file_id)


def _find_pdf(file_id: str) -> str:
    safe_id = re.sub(r'[^\w\-.]', '_', file_id)
    if safe_id != file_id:
        raise HTTPException(status_code=400, detail="Invalid file ID")
    direct = os.path.join(UPLOAD_DIR, file_id)
    resolved_direct = Path(direct).resolve()
    upload_root = Path(UPLOAD_DIR).resolve()
    if not str(resolved_direct).startswith(str(upload_root) + os.sep) and resolved_direct != upload_root:
        raise HTTPException(status_code=400, detail="Invalid file ID")
    if os.path.isfile(direct):
        return direct
    with_ext = os.path.join(UPLOAD_DIR, file_id + ".pdf")
    resolved_ext = Path(with_ext).resolve()
    if not str(resolved_ext).startswith(str(upload_root) + os.sep) and resolved_ext != upload_root:
        raise HTTPException(status_code=400, detail="Invalid file ID")
    if os.path.isfile(with_ext):
        return with_ext
    raise HTTPException(status_code=404, detail=f"PDF file not found: {file_id}")


def _parse_page_range(pages_str: str, total: int) -> list[int]:
    indices = []
    for part in pages_str.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            for i in range(int(start) - 1, min(int(end), total)):
                indices.append(i)
        else:
            idx = int(part) - 1
            if 0 <= idx < total:
                indices.append(idx)
    return indices


def _hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return (0.5, 0.5, 0.5)
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return (r, g, b)


def _get_position(rect, position: str):
    if position == "top-left":
        return rect.width * 0.25, rect.height * 0.25
    elif position == "top-right":
        return rect.width * 0.75, rect.height * 0.25
    elif position == "bottom-left":
        return rect.width * 0.25, rect.height * 0.75
    elif position == "bottom-right":
        return rect.width * 0.75, rect.height * 0.75
    return rect.width / 2, rect.height / 2


def _insert_watermark(page, text, cx, cy, font_size, color_rgb, opacity, angle):
    import fitz
    fontname = "helv"
    text_width = fitz.get_text_length(text, fontname=fontname, fontsize=font_size)
    text_rect = fitz.Rect(
        cx - text_width / 2 - 10,
        cy - font_size / 2 - 10,
        cx + text_width / 2 + 10,
        cy + font_size / 2 + 10,
    )
    shape = page.new_shape()
    shape.insert_textbox(
        text_rect,
        text,
        fontname=fontname,
        fontsize=font_size,
        color=color_rgb,
        align=fitz.TEXT_ALIGN_CENTER,
    )
    shape.commit()
