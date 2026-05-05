from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class HubItem:
    id: str
    name: str
    description: str
    version: str = "1.0.0"
    author: str = ""
    category: str = "tool"
    tags: list[str] = field(default_factory=list)
    download_url: str = ""
    source_url: str = ""
    installed: bool = False


class ClawHubClient:
    HUB_API_BASE = "https://hub.claw.ai/api/v1"

    def __init__(self, install_dir: str | None = None) -> None:
        if install_dir is None:
            install_dir = os.path.join(os.getcwd(), "hub_packages")
        self._install_dir = install_dir
        self._installed: dict[str, HubItem] = {}
        self._load_installed_registry()

    def _load_installed_registry(self) -> None:
        registry_path = Path(self._install_dir) / "registry.json"
        if registry_path.exists():
            try:
                with open(registry_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item_data in data.get("items", []):
                    item = HubItem(**item_data, installed=True)
                    self._installed[item.id] = item
            except Exception:
                pass

    def _save_installed_registry(self) -> None:
        registry_path = Path(self._install_dir) / "registry.json"
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "items": [
                {
                    "id": item.id,
                    "name": item.name,
                    "description": item.description,
                    "version": item.version,
                    "author": item.author,
                    "category": item.category,
                    "tags": item.tags,
                    "download_url": item.download_url,
                    "source_url": item.source_url,
                }
                for item in self._installed.values()
            ]
        }
        with open(registry_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    async def search(self, query: str, category: str | None = None, limit: int = 20) -> list[HubItem]:
        try:
            import httpx
            params = {"q": query, "limit": str(limit)}
            if category:
                params["category"] = category

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.HUB_API_BASE}/search",
                    params=params,
                    timeout=10.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    items = []
                    for item_data in data.get("items", []):
                        item = HubItem(
                            id=item_data.get("id", ""),
                            name=item_data.get("name", ""),
                            description=item_data.get("description", ""),
                            version=item_data.get("version", "1.0.0"),
                            author=item_data.get("author", ""),
                            category=item_data.get("category", "tool"),
                            tags=item_data.get("tags", []),
                            download_url=item_data.get("download_url", ""),
                            source_url=item_data.get("source_url", ""),
                            installed=item_data.get("id", "") in self._installed,
                        )
                        items.append(item)
                    return items
        except Exception:
            pass

        return []

    async def install(self, item_id: str) -> HubItem | None:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.HUB_API_BASE}/items/{item_id}",
                    timeout=10.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    item = HubItem(
                        id=data.get("id", item_id),
                        name=data.get("name", ""),
                        description=data.get("description", ""),
                        version=data.get("version", "1.0.0"),
                        author=data.get("author", ""),
                        category=data.get("category", "tool"),
                        tags=data.get("tags", []),
                        download_url=data.get("download_url", ""),
                        source_url=data.get("source_url", ""),
                        installed=True,
                    )

                    if item.download_url:
                        pkg_response = await client.get(item.download_url, timeout=60.0)
                        if pkg_response.status_code == 200:
                            pkg_dir = Path(self._install_dir) / item.category / item.name
                            pkg_dir.mkdir(parents=True, exist_ok=True)
                            pkg_file = pkg_dir / "package.zip"
                            pkg_file.write_bytes(pkg_response.content)

                    self._installed[item.id] = item
                    self._save_installed_registry()
                    return item
        except Exception:
            pass

        return None

    async def uninstall(self, item_id: str) -> bool:
        item = self._installed.pop(item_id, None)
        if not item:
            return False

        pkg_dir = Path(self._install_dir) / item.category / item.name
        if pkg_dir.exists():
            import shutil
            shutil.rmtree(pkg_dir, ignore_errors=True)

        self._save_installed_registry()
        return True

    def list_installed(self, category: str | None = None) -> list[HubItem]:
        items = list(self._installed.values())
        if category:
            items = [i for i in items if i.category == category]
        return items

    def get_installed(self, item_id: str) -> HubItem | None:
        return self._installed.get(item_id)


clawhub_client = ClawHubClient()
