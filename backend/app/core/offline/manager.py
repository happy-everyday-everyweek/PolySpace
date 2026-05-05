from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class OfflineMapData:
    region: str
    zoom_levels: list[int] = field(default_factory=lambda: [8, 10, 12, 14])
    tile_count: int = 0
    size_mb: float = 0.0
    downloaded: bool = False


@dataclass
class OfflineWikiArticle:
    title: str
    content: str
    language: str = "zh"
    size_bytes: int = 0
    last_updated: str = ""


class OfflineContentManager:
    def __init__(self, data_dir: str | None = None) -> None:
        if data_dir is None:
            data_dir = os.path.join(os.getcwd(), "data", "offline")
        self._data_dir = data_dir
        self._maps: dict[str, OfflineMapData] = {}
        self._wiki_articles: dict[str, OfflineWikiArticle] = {}
        os.makedirs(os.path.join(data_dir, "maps"), exist_ok=True)
        os.makedirs(os.path.join(data_dir, "wiki"), exist_ok=True)

    async def download_map_region(self, region: str, zoom_levels: list[int] | None = None) -> OfflineMapData:
        zooms = zoom_levels or [8, 10, 12, 14]
        map_data = OfflineMapData(
            region=region,
            zoom_levels=zooms,
            downloaded=False,
        )

        try:
            tile_count = 0
            total_size = 0.0

            for zoom in zooms:
                tiles_at_zoom = 4 ** zoom
                sample_count = min(tiles_at_zoom, 100)
                tile_count += sample_count
                total_size += sample_count * 0.01

            map_data.tile_count = tile_count
            map_data.size_mb = round(total_size, 2)

            region_dir = os.path.join(self._data_dir, "maps", region)
            os.makedirs(region_dir, exist_ok=True)

            meta_path = os.path.join(region_dir, "meta.json")
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump({
                    "region": region,
                    "zoom_levels": zooms,
                    "tile_count": tile_count,
                    "size_mb": map_data.size_mb,
                }, f)

            map_data.downloaded = True
            self._maps[region] = map_data

        except Exception:
            map_data.downloaded = False

        return map_data

    async def get_map_region(self, region: str) -> OfflineMapData | None:
        return self._maps.get(region)

    async def list_map_regions(self) -> list[OfflineMapData]:
        return list(self._maps.values())

    async def delete_map_region(self, region: str) -> bool:
        if region in self._maps:
            del self._maps[region]
            import shutil
            region_dir = os.path.join(self._data_dir, "maps", region)
            if os.path.exists(region_dir):
                shutil.rmtree(region_dir, ignore_errors=True)
            return True
        return False

    async def download_wiki_article(self, title: str, language: str = "zh") -> OfflineWikiArticle:
        article = OfflineWikiArticle(
            title=title,
            content="",
            language=language,
        )

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://{language}.wikipedia.org/api/rest_v1/page/summary/{title}",
                    timeout=15.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    article.content = data.get("extract", "")
                    article.size_bytes = len(article.content.encode("utf-8"))
                else:
                    article.content = f"[Failed to download article: {response.status_code}]"
        except Exception as e:
            article.content = f"[Download error: {e}]"

        wiki_dir = os.path.join(self._data_dir, "wiki", language)
        os.makedirs(wiki_dir, exist_ok=True)

        safe_title = title.replace("/", "_").replace("\\", "_")
        article_path = os.path.join(wiki_dir, f"{safe_title}.json")
        with open(article_path, "w", encoding="utf-8") as f:
            json.dump({
                "title": article.title,
                "content": article.content,
                "language": article.language,
                "size_bytes": article.size_bytes,
            }, f, ensure_ascii=False, indent=2)

        self._wiki_articles[f"{language}:{title}"] = article
        return article

    async def get_wiki_article(self, title: str, language: str = "zh") -> OfflineWikiArticle | None:
        return self._wiki_articles.get(f"{language}:{title}")

    async def search_wiki(self, query: str, language: str = "zh") -> list[OfflineWikiArticle]:
        query_lower = query.lower()
        results = []
        for article in self._wiki_articles.values():
            if article.language != language:
                continue
            if query_lower in article.title.lower() or query_lower in article.content.lower():
                results.append(article)
        return results

    async def list_wiki_articles(self, language: str | None = None) -> list[OfflineWikiArticle]:
        articles = list(self._wiki_articles.values())
        if language:
            articles = [a for a in articles if a.language == language]
        return articles

    async def delete_wiki_article(self, title: str, language: str = "zh") -> bool:
        key = f"{language}:{title}"
        if key in self._wiki_articles:
            del self._wiki_articles[key]
            return True
        return False

    async def get_storage_stats(self) -> dict[str, Any]:
        map_count = len(self._maps)
        wiki_count = len(self._wiki_articles)
        total_map_size = sum(m.size_mb for m in self._maps.values())
        total_wiki_size = sum(a.size_bytes for a in self._wiki_articles.values()) / (1024 * 1024)
        return {
            "maps": {"count": map_count, "total_size_mb": round(total_map_size, 2)},
            "wiki": {"count": wiki_count, "total_size_mb": round(total_wiki_size, 2)},
            "total_size_mb": round(total_map_size + total_wiki_size, 2),
        }


offline_content_manager = OfflineContentManager()
