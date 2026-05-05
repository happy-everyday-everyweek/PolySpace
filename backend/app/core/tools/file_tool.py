from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from app.core.tool.base import BaseTool


class FileTool(BaseTool):
    def __init__(self, allowed_dirs: list[str] | None = None) -> None:
        super().__init__(
            name="file",
            description="Read, write, list, delete files and directories",
        )
        self._allowed_dirs = allowed_dirs

    def _validate_path(self, path: str) -> str:
        resolved = str(Path(path).resolve())
        if self._allowed_dirs:
            if not any(resolved.startswith(str(Path(d).resolve())) for d in self._allowed_dirs):
                raise PermissionError(f"Access denied: {path}")
        return resolved

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs: Any) -> Any:
        action = kwargs.get("action", "")
        path = kwargs.get("path", "")

        if not action:
            return {"error": "No action specified"}

        try:
            if action == "read":
                resolved = self._validate_path(path)
                with open(resolved, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                return {"content": content, "path": resolved}

            elif action == "write":
                resolved = self._validate_path(path)
                content = kwargs.get("content", "")
                Path(resolved).parent.mkdir(parents=True, exist_ok=True)
                with open(resolved, "w", encoding="utf-8") as f:
                    f.write(content)
                return {"success": True, "path": resolved}

            elif action == "list":
                resolved = self._validate_path(path)
                p = Path(resolved)
                if not p.is_dir():
                    return {"error": f"Not a directory: {path}"}
                entries = []
                for entry in sorted(p.iterdir()):
                    entries.append({
                        "name": entry.name,
                        "type": "dir" if entry.is_dir() else "file",
                        "size": entry.stat().st_size if entry.is_file() else 0,
                    })
                return {"entries": entries, "path": resolved}

            elif action == "delete":
                resolved = self._validate_path(path)
                p = Path(resolved)
                if p.is_dir():
                    shutil.rmtree(resolved)
                elif p.is_file():
                    p.unlink()
                else:
                    return {"error": f"Path not found: {path}"}
                return {"success": True, "path": resolved}

            elif action == "mkdir":
                resolved = self._validate_path(path)
                Path(resolved).mkdir(parents=True, exist_ok=True)
                return {"success": True, "path": resolved}

            elif action == "copy":
                src = self._validate_path(path)
                dst = self._validate_path(kwargs.get("destination", ""))
                shutil.copy2(src, dst)
                return {"success": True, "source": src, "destination": dst}

            elif action == "move":
                src = self._validate_path(path)
                dst = self._validate_path(kwargs.get("destination", ""))
                shutil.move(src, dst)
                return {"success": True, "source": src, "destination": dst}

            else:
                return {"error": f"Unknown action: {action}"}

        except PermissionError as e:
            return {"error": str(e)}
        except FileNotFoundError:
            return {"error": f"File not found: {path}"}
        except Exception as e:
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        pass

    def get_definition(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["read", "write", "list", "delete", "mkdir", "copy", "move"],
                            "description": "File operation to perform",
                        },
                        "path": {"type": "string", "description": "File or directory path"},
                        "content": {"type": "string", "description": "Content to write (for write action)"},
                        "destination": {"type": "string", "description": "Destination path (for copy/move)"},
                    },
                    "required": ["action", "path"],
                },
            },
        }
