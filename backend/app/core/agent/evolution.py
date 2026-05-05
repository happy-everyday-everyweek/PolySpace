import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class EvolutionEntry:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    trigger: str = ""
    observation: str = ""
    old_behavior: str = ""
    new_behavior: str = ""
    confidence: float = 0.5
    source: str = ""
    applied: bool = False
    feedback_score: float | None = None


@dataclass
class PromptEvolution:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    original_prompt: str = ""
    evolved_prompt: str = ""
    rationale: str = ""
    performance_before: dict = field(default_factory=dict)
    performance_after: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    accepted: bool = False


class SelfEvolutionEngine:
    def __init__(self, storage_dir: str | Path | None = None):
        if storage_dir is None:
            from app.config import settings
            storage_dir = Path(settings.DATA_DIR) / "evolution"
        self._dir = Path(storage_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._evolution_log: list[EvolutionEntry] = []
        self._prompt_evolutions: list[PromptEvolution] = []
        self._llm_call: Any = None
        self._load()

    def set_llm_call(self, fn):
        self._llm_call = fn

    async def _call_llm(self, prompt: str, system: str = "") -> str:
        if self._llm_call:
            return await self._llm_call(prompt, system)
        return ""

    def observe_execution(self, task_desc: str, result: Any, success: bool, duration: float, agent_name: str = ""):
        if success and duration < 5.0:
            return
        entry = EvolutionEntry(
            trigger="execution_result",
            observation=f"Agent '{agent_name}' task: {task_desc[:100]} | success={success} | duration={duration:.1f}s",
            old_behavior="",
            new_behavior="",
            confidence=0.3 if not success else 0.5,
            source=agent_name,
        )
        self._evolution_log.append(entry)
        if len(self._evolution_log) > 500:
            self._evolution_log = self._evolution_log[-500:]
        self._persist()

    async def learn_from_feedback(self, task_desc: str, result: Any, feedback: str, score: float):
        prompt = f"""Analyze this execution feedback and determine what behavior should change.

Task: {task_desc}
Result: {json.dumps(result, ensure_ascii=False)[:500] if isinstance(result, (dict, list)) else str(result)[:500]}
User feedback: {feedback}
Score: {score}/1.0

Return JSON:
{{
  "observation": "What happened",
  "old_behavior": "What the agent did wrong or suboptimally",
  "new_behavior": "What the agent should do instead",
  "confidence": 0.0-1.0
}}"""

        response = await self._call_llm(prompt, "You are a self-improvement system. Analyze failures and suggest concrete behavior changes.")
        entry = EvolutionEntry(
            trigger="user_feedback",
            observation=feedback,
            confidence=score,
            source="feedback",
        )
        try:
            parsed = json.loads(response)
            entry.old_behavior = parsed.get("old_behavior", "")
            entry.new_behavior = parsed.get("new_behavior", "")
            entry.confidence = parsed.get("confidence", score)
            entry.applied = True
        except (json.JSONDecodeError, ValueError):
            entry.new_behavior = response[:300] if response else ""

        self._evolution_log.append(entry)
        self._persist()
        return entry

    async def evolve_prompt(self, current_prompt: str, performance_metrics: dict) -> PromptEvolution:
        prompt = f"""You are a prompt optimization system. Improve the following system prompt based on performance metrics.

Current prompt:
{current_prompt[:2000]}

Performance metrics:
{json.dumps(performance_metrics, ensure_ascii=False, indent=2)}

Improve the prompt to:
1. Be more specific and actionable
2. Address observed weaknesses
3. Maintain core functionality
4. Add guardrails for common failure modes

Return JSON:
{{
  "evolved_prompt": "The improved prompt",
  "rationale": "Why these changes improve performance",
  "expected_improvements": ["improvement1", "improvement2"]
}}"""

        response = await self._call_llm(prompt, "You are a prompt engineering expert. Optimize system prompts for better agent performance.")
        evolution = PromptEvolution(original_prompt=current_prompt, performance_before=performance_metrics)
        try:
            parsed = json.loads(response)
            evolution.evolved_prompt = parsed.get("evolved_prompt", current_prompt)
            evolution.rationale = parsed.get("rationale", "")
        except (json.JSONDecodeError, ValueError):
            evolution.evolved_prompt = current_prompt

        self._prompt_evolutions.append(evolution)
        self._persist()
        return evolution

    def get_learned_behaviors(self, limit: int = 20) -> list[dict]:
        applied = [e for e in self._evolution_log if e.applied and e.new_behavior]
        return [
            {"old": e.old_behavior, "new": e.new_behavior, "confidence": e.confidence, "source": e.source}
            for e in applied[-limit:]
        ]

    def get_evolution_summary(self) -> dict:
        return {
            "total_observations": len(self._evolution_log),
            "applied_changes": len([e for e in self._evolution_log if e.applied]),
            "prompt_evolutions": len(self._prompt_evolutions),
            "avg_confidence": sum(e.confidence for e in self._evolution_log) / max(len(self._evolution_log), 1),
        }

    def _persist(self):
        data = {
            "evolution_log": [
                {"trigger": e.trigger, "observation": e.observation, "old_behavior": e.old_behavior,
                 "new_behavior": e.new_behavior, "confidence": e.confidence, "applied": e.applied, "source": e.source}
                for e in self._evolution_log[-200:]
            ],
            "prompt_evolutions": [
                {"original": p.original_prompt[:200], "evolved": p.evolved_prompt[:200],
                 "rationale": p.rationale, "accepted": p.accepted}
                for p in self._prompt_evolutions[-50:]
            ],
        }
        path = self._dir / "evolution_state.json"
        try:
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(path)
        except OSError as e:
            logger.error(f"Evolution persist failed: {e}")

    def _load(self):
        path = self._dir / "evolution_state.json"
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            for raw in data.get("evolution_log", []):
                self._evolution_log.append(EvolutionEntry(
                    trigger=raw.get("trigger", ""),
                    observation=raw.get("observation", ""),
                    old_behavior=raw.get("old_behavior", ""),
                    new_behavior=raw.get("new_behavior", ""),
                    confidence=raw.get("confidence", 0.5),
                    applied=raw.get("applied", False),
                    source=raw.get("source", ""),
                ))
            for raw in data.get("prompt_evolutions", []):
                self._prompt_evolutions.append(PromptEvolution(
                    original_prompt=raw.get("original", ""),
                    evolved_prompt=raw.get("evolved", ""),
                    rationale=raw.get("rationale", ""),
                    accepted=raw.get("accepted", False),
                ))
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Evolution load failed: {e}")


_evolution_engine: SelfEvolutionEngine | None = None


def get_evolution_engine() -> SelfEvolutionEngine:
    global _evolution_engine
    if _evolution_engine is None:
        _evolution_engine = SelfEvolutionEngine()
    return _evolution_engine
