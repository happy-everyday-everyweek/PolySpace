import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DreamPhase(str, Enum):
    LIGHT = "light"
    DEEP = "deep"
    REM = "rem"


@dataclass
class DreamSource:
    daily: list[dict] = field(default_factory=list)
    sessions: list[dict] = field(default_factory=list)
    memory: list[dict] = field(default_factory=list)
    recall: list[dict] = field(default_factory=list)


@dataclass
class DreamResult:
    phase: DreamPhase
    timestamp: float = field(default_factory=time.time)
    insights: list[str] = field(default_factory=list)
    consolidated: list[dict] = field(default_factory=list)
    pruned: list[str] = field(default_factory=list)
    patterns: list[dict] = field(default_factory=list)
    report: str = ""


@dataclass
class DreamConfig:
    enabled: bool = True
    light_cron: str = "0 */6 * * *"
    light_lookback_days: int = 2
    light_limit: int = 100
    light_dedupe_similarity: float = 0.9
    deep_cron: str = "0 3 * * *"
    deep_limit: int = 10
    deep_min_score: float = 0.8
    deep_min_recall_count: int = 3
    deep_recency_half_life_days: int = 14
    deep_max_age_days: int = 30
    deep_recovery_enabled: bool = True
    deep_recovery_trigger_below_health: float = 0.35
    rem_cron: str = "0 5 * * 0"
    rem_lookback_days: int = 7
    rem_limit: int = 10
    rem_min_pattern_strength: float = 0.75


class DreamStore:
    def __init__(self, base_dir: str | Path | None = None):
        if base_dir is None:
            from app.config import settings
            base_dir = Path(settings.DATA_DIR) / "dreams"
        self._dir = Path(base_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def save_result(self, result: DreamResult) -> str:
        result_id = str(uuid.uuid4())
        path = self._dir / f"dream_{result.phase.value}_{int(time.time())}.json"
        data = {
            "id": result_id,
            "phase": result.phase.value,
            "timestamp": result.timestamp,
            "insights": result.insights,
            "consolidated": result.consolidated,
            "pruned": result.pruned,
            "patterns": result.patterns,
            "report": result.report,
        }
        try:
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(path)
        except OSError as e:
            logger.error(f"Failed to save dream result: {e}")
        return result_id

    def load_results(self, phase: DreamPhase | None = None, limit: int = 20) -> list[dict]:
        results = []
        pattern = f"dream_{phase.value}_*.json" if phase else "dream_*.json"
        for path in sorted(self._dir.glob(pattern), reverse=True)[:limit]:
            try:
                results.append(json.loads(path.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                pass
        return results


class MemoryDreamer:
    def __init__(self, config: DreamConfig | None = None, store: DreamStore | None = None):
        self._config = config or DreamConfig()
        self._store = store or DreamStore()
        self._llm_call: Any = None
        self._dream_lock = asyncio.Lock()

    def set_llm_call(self, fn):
        self._llm_call = fn

    async def _call_llm(self, prompt: str, system: str = "") -> str:
        if self._llm_call:
            return await self._llm_call(prompt, system)
        return ""

    def _gather_sources(self, memory_mgr, lookback_days: int) -> DreamSource:
        sources = DreamSource()
        cutoff = time.time() - lookback_days * 86400
        try:
            structured = memory_mgr.load_structured_memory()
            for fact in structured.get("facts", []):
                created = fact.get("createdAt", "")
                try:
                    fact_ts = datetime.fromisoformat(created).timestamp()
                    if fact_ts >= cutoff:
                        sources.daily.append(fact)
                except (ValueError, OSError):
                    sources.daily.append(fact)
            for section_key in ["workContext", "personalContext", "topOfMind"]:
                section = structured.get("user", {}).get(section_key, {})
                if section.get("summary"):
                    sources.memory.append({"section": section_key, **section})
            for hist_key in ["recentMonths", "earlierContext", "longTermBackground"]:
                section = structured.get("history", {}).get(hist_key, {})
                if section.get("summary"):
                    sources.memory.append({"section": hist_key, **section})
        except Exception as e:
            logger.error(f"Error gathering dream sources: {e}")

        self._gather_task_sources(sources, cutoff)

        return sources

    def _gather_task_sources(self, sources: DreamSource, cutoff: float) -> None:
        try:
            from app.core.tool.interaction_tools import async_task_manager
            tasks = async_task_manager.list_tasks(limit=50)
            for task_data in tasks:
                created = task_data.get("created_at", 0)
                if isinstance(created, (int, float)) and created >= cutoff:
                    task_summary = {
                        "id": task_data.get("id", ""),
                        "content": f"[Task] {task_data.get('description', '')} - Status: {task_data.get('status', '')}",
                        "status": task_data.get("status", ""),
                        "progress": task_data.get("progress", 0),
                        "steps_count": len(task_data.get("steps", [])),
                        "supplements_count": len(task_data.get("supplements", [])),
                        "has_error": bool(task_data.get("error", "")),
                    }
                    sources.daily.append(task_summary)
                    if task_data.get("status") == "completed":
                        sources.sessions.append({
                            "content": f"Completed task: {task_data.get('description', '')[:80]}",
                            "steps": task_data.get("steps_count", 0),
                            "type": "task_completion",
                        })
        except Exception as e:
            logger.debug(f"Could not gather task sources for dreaming: {e}")

    async def light_dream(self, memory_mgr) -> DreamResult:
        result = DreamResult(phase=DreamPhase.LIGHT)
        if not self._config.enabled:
            return result

        sources = self._gather_sources(memory_mgr, self._config.light_lookback_days)
        all_items = sources.daily + sources.sessions + sources.recall
        if not all_items:
            result.report = "No recent items to process in light dream."
            return result

        seen_contents: dict[str, str] = {}
        deduped = []
        for item in all_items:
            content = item.get("content", item.get("summary", str(item)))
            key = content[:200].lower().strip()
            if key not in seen_contents:
                seen_contents[key] = content
                deduped.append(item)

        items_text = "\n".join(
            f"- {item.get('content', item.get('summary', str(item)))}"
            for item in deduped[:self._config.light_limit]
        )

        prompt = (
            "Analyze these recent memory entries and extract key insights. "
            "Group related items, identify duplicates, and summarize.\n\n"
            f"Recent entries:\n{items_text}\n\n"
            "Return JSON:\n"
            '{"insights": ["insight1", "insight2"], '
            '"consolidated": [{"original_ids": ["id1","id2"], '
            '"merged_content": "...", "category": "..."}], '
            '"pruned": ["id_of_redundant_entry"]}'
        )

        response = await self._call_llm(
            prompt,
            "You are a memory consolidation system. Be concise and accurate.",
        )
        try:
            parsed = json.loads(response)
            result.insights = parsed.get("insights", [])
            result.consolidated = parsed.get("consolidated", [])
            result.pruned = parsed.get("pruned", [])
        except json.JSONDecodeError:
            result.insights = [response[:500]] if response else []

        for insight in result.insights:
            memory_mgr.add_fact(insight, confidence=0.7)

        result.report = (
            f"Light dream: {len(result.insights)} insights, "
            f"{len(result.consolidated)} consolidated, "
            f"{len(result.pruned)} pruned"
        )
        self._store.save_result(result)
        return result

    async def deep_dream(self, memory_mgr) -> DreamResult:
        result = DreamResult(phase=DreamPhase.DEEP)
        if not self._config.enabled:
            return result

        sources = self._gather_sources(memory_mgr, self._config.deep_max_age_days)
        all_items = sources.daily + sources.memory + sources.sessions
        if not all_items:
            result.report = "No items for deep dream processing."
            return result

        items_text = "\n".join(
            f"- [{item.get('id', 'unknown')}] {item.get('content', item.get('summary', str(item)))}"
            for item in all_items[:self._config.deep_limit * 5]
        )

        prompt = (
            "Deep memory consolidation. Analyze these memory entries "
            "for deep patterns, long-term significance, and connections.\n\n"
            f"Memory entries:\n{items_text}\n\n"
            "Return JSON:\n"
            '{"insights": ["deep insight about long-term patterns"], '
            '"consolidated": [{"original_ids": ["id1","id2"], '
            '"merged_content": "...", "significance": "high/medium/low"}], '
            '"pruned": ["id_of_outdated_entry"], '
            '"patterns": [{"pattern": "...", '
            '"strength": 0.0-1.0, "evidence": ["id1","id2"]}]}'
        )

        response = await self._call_llm(
            prompt,
            "You are a deep memory consolidation system. "
            "Focus on long-term patterns and significance.",
        )
        try:
            parsed = json.loads(response)
            result.insights = parsed.get("insights", [])
            result.consolidated = parsed.get("consolidated", [])
            result.pruned = parsed.get("pruned", [])
            result.patterns = parsed.get("patterns", [])
        except json.JSONDecodeError:
            result.insights = [response[:500]] if response else []

        for insight in result.insights:
            memory_mgr.add_fact(insight, confidence=0.9)

        for pattern in result.patterns:
            if pattern.get("strength", 0) >= self._config.deep_min_score:
                memory_mgr.add_fact(
                    f"Pattern: {pattern['pattern']} (strength: {pattern['strength']})",
                    confidence=pattern["strength"],
                )

        if self._config.deep_recovery_enabled:
            await self._check_recovery(memory_mgr)

        result.report = f"Deep dream: {len(result.insights)} insights, {len(result.patterns)} patterns"
        self._store.save_result(result)
        return result

    async def _check_recovery(self, memory_mgr) -> None:
        structured = memory_mgr.load_structured_memory()
        facts = structured.get("facts", [])
        if not facts:
            return
        low_conf = [f for f in facts if f.get("confidence", 1.0) < self._config.deep_recovery_trigger_below_health]
        if not low_conf:
            return

        facts_text = "\n".join(
            f"- [{f.get('id')}] {f.get('content')} "
            f"(confidence: {f.get('confidence', 0)})"
            for f in low_conf[:20]
        )
        prompt = (
            "These memory facts have low confidence scores. "
            "Review and determine which should be recovered "
            "(confirmed as true) or pruned.\n\n"
            f"Low confidence facts:\n{facts_text}\n\n"
            'Return JSON:\n'
            '{"recover": [{"id": "...", '
            '"new_confidence": 0.0-1.0, "reason": "..."}], '
            '"prune": ["id_to_remove"]}'
        )

        response = await self._call_llm(prompt, "You are a memory quality assurance system.")
        try:
            parsed = json.loads(response)
            for rec in parsed.get("recover", []):
                if rec.get("new_confidence", 0) >= self._config.deep_recovery_trigger_below_health:
                    memory_mgr.add_fact(
                        f"[Recovered] {rec.get('reason', '')}",
                        confidence=rec["new_confidence"],
                    )
        except json.JSONDecodeError:
            pass

    async def rem_dream(self, memory_mgr) -> DreamResult:
        result = DreamResult(phase=DreamPhase.REM)
        if not self._config.enabled:
            return result

        sources = self._gather_sources(memory_mgr, self._config.rem_lookback_days)
        all_items = sources.memory + sources.daily
        if not all_items:
            result.report = "No items for REM dream processing."
            return result

        items_text = "\n".join(
            f"- {item.get('content', item.get('summary', str(item)))}"
            for item in all_items[:self._config.rem_limit * 3]
        )

        prompt = (
            "REM (Rapid Eye Movement) dream: creative pattern synthesis. "
            "Find unexpected connections, generate creative insights, "
            "and discover hidden relationships.\n\n"
            f"Memory entries:\n{items_text}\n\n"
            "Return JSON:\n"
            '{"patterns": [{"pattern": "...", '
            '"strength": 0.0-1.0, "connections": ["item1", "item2"]}], '
            '"insights": ["creative/unexpected insight from pattern synthesis"], '
            '"consolidated": [{"merged_content": "...", '
            '"source_pattern": "..."}]}'
        )

        response = await self._call_llm(
            prompt,
            "You are a creative memory synthesis system. "
            "Think laterally and find unexpected connections.",
        )
        try:
            parsed = json.loads(response)
            result.patterns = parsed.get("patterns", [])
            result.insights = parsed.get("insights", [])
            result.consolidated = parsed.get("consolidated", [])
        except json.JSONDecodeError:
            result.insights = [response[:500]] if response else []

        for insight in result.insights:
            memory_mgr.add_fact(insight, confidence=0.6)

        result.report = f"REM dream: {len(result.patterns)} patterns, {len(result.insights)} creative insights"
        self._store.save_result(result)
        return result

    async def run_all_phases(self, memory_mgr) -> list[DreamResult]:
        async with self._dream_lock:
            results = []
            results.append(await self.light_dream(memory_mgr))
            results.append(await self.deep_dream(memory_mgr))
            results.append(await self.rem_dream(memory_mgr))
            return results

    def get_results(self, phase: DreamPhase | None = None, limit: int = 20) -> list[dict]:
        return self._store.load_results(phase, limit)


_memory_dreamer: MemoryDreamer | None = None


def get_memory_dreamer() -> MemoryDreamer:
    global _memory_dreamer
    if _memory_dreamer is None:
        _memory_dreamer = MemoryDreamer()
    return _memory_dreamer
