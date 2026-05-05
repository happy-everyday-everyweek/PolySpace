from __future__ import annotations

import asyncio
import logging
import os
import platform
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

LIBREOFFICE_FILTER_MAP: dict[str, str] = {
    "pdf": "writer_pdf_Export",
    "docx": "MS Word 2007 XML",
    "odt": "writer8",
    "html": "HTML (StarWriter)",
    "txt": "Text",
    "rtf": "Rich Text Format",
    "pptx": "Impress MS PowerPoint 2007 XML",
    "odp": "impress8",
    "xlsx": "Calc MS Excel 2007 XML",
    "ods": "calc8",
    "csv": "Text - txt - csv (StarCalc)",
}


def _find_libreoffice_executable() -> str | None:
    system = platform.system()
    candidates: list[str] = []
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    if system == "Windows":
        bundled = os.path.join(project_root, "libreoffice", "program", "soffice.exe")
        candidates.append(bundled)
        program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
        program_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        for base in [program_files, program_files_x86]:
            for name in ["LibreOffice", "LibreOffice 24", "LibreOffice 25"]:
                candidates.append(os.path.join(base, name, "program", "soffice.exe"))
        if local_app_data:
            for name in ["LibreOffice", "LibreOffice 24", "LibreOffice 25"]:
                candidates.append(os.path.join(local_app_data, "Programs", name, "program", "soffice.exe"))
        candidates.append("soffice.exe")
    elif system == "Darwin":
        bundled = os.path.join(project_root, "libreoffice", "MacOS", "soffice")
        candidates.append(bundled)
        candidates.append("/Applications/LibreOffice.app/Contents/MacOS/soffice")
        candidates.append("soffice")
    else:
        bundled = os.path.join(project_root, "libreoffice", "program", "soffice")
        candidates.append(bundled)
        candidates.append("/usr/bin/libreoffice")
        candidates.append("/usr/bin/soffice")
        candidates.append("/snap/bin/libreoffice")
        candidates.append("libreoffice")
        candidates.append("soffice")
    for path in candidates:
        if os.path.isfile(path):
            return path
    result = shutil.which("libreoffice") or shutil.which("soffice")
    return result


class LibreOfficeService:
    def __init__(self, soffice_path: str | None = None, data_dir: str | None = None):
        self._soffice_path = soffice_path
        self._data_dir = data_dir or os.path.join(os.getcwd(), "data", "conversions")
        os.makedirs(self._data_dir, exist_ok=True)
        self._available: bool | None = None

    @property
    def soffice_path(self) -> str | None:
        if self._soffice_path is None:
            self._soffice_path = _find_libreoffice_executable()
        return self._soffice_path

    @property
    def available(self) -> bool:
        if self._available is None:
            self._available = self.soffice_path is not None
            if self._available:
                logger.info(f"LibreOffice found: {self._soffice_path}")
            else:
                logger.warning("LibreOffice not found. Document conversion will use fallback methods.")
        return self._available

    async def convert(
        self,
        input_path: str,
        output_format: str = "pdf",
        output_path: str | None = None,
        filter_name: str | None = None,
        timeout: int = 120,
    ) -> dict[str, Any]:
        if not os.path.isfile(input_path):
            return {"error": f"Input file not found: {input_path}"}

        if not self.available:
            return {"error": "LibreOffice is not installed or not found on this system"}

        if output_path is None:
            base = os.path.splitext(input_path)[0]
            ext = f".{output_format}"
            output_path = base + ext

        actual_filter = filter_name or LIBREOFFICE_FILTER_MAP.get(output_format)
        output_dir = os.path.dirname(output_path) or self._data_dir

        cmd = [
            self.soffice_path,
            "--headless",
            "--convert-to",
            f"{output_format}:{actual_filter}" if actual_filter else output_format,
            "--outdir",
            output_dir,
            input_path,
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            if proc.returncode != 0:
                err_msg = stderr.decode(errors="replace").strip()
                logger.error(f"LibreOffice conversion failed: {err_msg}")
                return {"error": f"Conversion failed: {err_msg}"}

            expected_output = os.path.join(output_dir, Path(input_path).stem + f".{output_format}")
            if not os.path.isfile(expected_output):
                for f in os.listdir(output_dir):
                    if f.startswith(Path(input_path).stem) and f.endswith(f".{output_format}"):
                        expected_output = os.path.join(output_dir, f)
                        break

            if not os.path.isfile(expected_output):
                return {"error": f"Output file not found after conversion: {expected_output}"}

            if expected_output != output_path:
                shutil.move(expected_output, output_path)

            return {
                "status": "ok",
                "output_path": output_path,
                "output_format": output_format,
                "file_size": os.path.getsize(output_path),
            }
        except asyncio.TimeoutError:
            return {"error": f"Conversion timed out after {timeout}s"}
        except Exception as e:
            logger.error(f"LibreOffice conversion error: {e}")
            return {"error": str(e)}

    async def convert_bytes(
        self,
        data: bytes,
        source_format: str,
        output_format: str = "pdf",
        filename: str | None = None,
        timeout: int = 120,
    ) -> dict[str, Any]:
        ext_map = {
            "docx": ".docx", "doc": ".doc", "odt": ".odt", "rtf": ".rtf",
            "html": ".html", "txt": ".txt", "md": ".md",
            "pptx": ".pptx", "ppt": ".ppt", "odp": ".odp",
            "xlsx": ".xlsx", "xls": ".xls", "ods": ".ods", "csv": ".csv",
            "pdf": ".pdf",
        }
        src_ext = ext_map.get(source_format, f".{source_format}")
        if filename is None:
            filename = str(uuid.uuid4())

        with tempfile.TemporaryDirectory(dir=self._data_dir) as tmpdir:
            input_path = os.path.join(tmpdir, filename + src_ext)
            output_path = os.path.join(tmpdir, filename + f".{output_format}")

            with open(input_path, "wb") as f:
                f.write(data)

            result = await self.convert(input_path, output_format, output_path, timeout=timeout)
            if "error" in result:
                return result

            with open(output_path, "rb") as f:
                output_data = f.read()

            result["output_data"] = output_data
            return result

    async def get_info(self) -> dict[str, Any]:
        if not self.available:
            return {"available": False, "path": None}
        try:
            proc = await asyncio.create_subprocess_exec(
                self.soffice_path, "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
            version_str = stdout.decode(errors="replace").strip()
            return {"available": True, "path": self.soffice_path, "version": version_str}
        except Exception as e:
            return {"available": True, "path": self.soffice_path, "version": "unknown", "error": str(e)}


libreoffice_service = LibreOfficeService()
