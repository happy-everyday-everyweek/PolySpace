from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from app.core.agent.base import BaseAgent
from app.core.llm.gateway import llm_gateway

logger = logging.getLogger(__name__)


class ResearchPhase(str, Enum):
    PLANNING = "planning"
    SEARCHING = "searching"
    ANALYZING = "analyzing"
    SYNTHESIZING = "synthesizing"
    ITERATING = "iterating"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchStep(BaseAgent if hasattr(BaseAgent, "__init__") else object):
    pass


class ResearchResult:
    def __init__(
        self,
        id: str,
        query: str,
        phase: ResearchPhase,
        plan: list[dict] | None = None,
        sources: list[dict] | None = None,
        findings: list[dict] | None = None,
        report: str | None = None,
        gaps: list[str] | None = None,
        iterations: int = 0,
        max_iterations: int = 3,
        created_at: str | None = None,
    ):
        self.id = id
        self.query = query
        self.phase = phase
        self.plan = plan or []
        self.sources = sources or []
        self.findings = findings or []
        self.report = report
        self.gaps = gaps or []
        self.iterations = iterations
        self.max_iterations = max_iterations
        self.created_at = created_at or datetime.now().isoformat()

    def to_dict(self):
        return {
            "id": self.id,
            "query": self.query,
            "phase": self.phase.value,
            "plan": self.plan,
            "sources": self.sources,
            "findings": self.findings,
            "report": self.report,
            "gaps": self.gaps,
            "iterations": self.iterations,
            "max_iterations": self.max_iterations,
            "created_at": self.created_at,
        }


_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "research")


class DeepResearchAgent:
    def __init__(self, max_iterations: int = 3):
        self.max_iterations = max_iterations
        self._results: dict[str, ResearchResult] = {}
        os.makedirs(_DATA_DIR, exist_ok=True)

    async def start_research(self, query: str) -> ResearchResult:
        research_id = uuid.uuid4().hex[:12]
        result = ResearchResult(
            id=research_id,
            query=query,
            phase=ResearchPhase.PLANNING,
            max_iterations=self.max_iterations,
        )
        self._results[research_id] = result
        plan = await self._generate_plan(query)
        result.plan = plan
        result.phase = ResearchPhase.SEARCHING
        self._save(result)
        return result

    async def execute_step(self, research_id: str, step_index: int) -> dict:
        result = self._results.get(research_id)
        if not result:
            return {"error": "Research not found"}
        if step_index >= len(result.plan):
            return {"error": "Step index out of range"}
        step = result.plan[step_index]
        result.phase = ResearchPhase.SEARCHING
        sources = await self._search_sources(step.get("query", result.query), step.get("source_types", ["web", "knowledge"]))
        result.sources.extend(sources)
        result.phase = ResearchPhase.ANALYZING
        findings = await self._analyze_sources(result.query, sources)
        result.findings.extend(findings)
        self._save(result)
        return {"step": step, "sources": sources, "findings": findings}

    async def synthesize(self, research_id: str) -> ResearchResult:
        result = self._results.get(research_id)
        if not result:
            raise ValueError("Research not found")
        result.phase = ResearchPhase.SYNTHESIZING
        report = await self._generate_report(result.query, result.findings, result.sources)
        result.report = report
        gaps = await self._identify_gaps(result.query, result.findings)
        result.gaps = gaps
        result.iterations += 1
        if result.iterations >= result.max_iterations or not gaps:
            result.phase = ResearchPhase.COMPLETED
        else:
            result.phase = ResearchPhase.ITERATING
            for gap in gaps:
                result.plan.append({"query": gap, "source_types": ["web", "knowledge"], "reason": f"Filling gap: {gap}"})
        self._save(result)
        return result

    async def get_status(self, research_id: str) -> Optional[dict]:
        result = self._results.get(research_id)
        return result.to_dict() if result else None

    async def list_research(self, limit: int = 20) -> list[dict]:
        results = sorted(self._results.values(), key=lambda r: r.created_at, reverse=True)
        return [r.to_dict() for r in results[:limit]]

    async def _generate_plan(self, query: str) -> list[dict]:
        prompt = f"""You are a research planner. Given the research question below, create a step-by-step research plan.

Research Question: {query}

Return a JSON array of steps. Each step should have:
- "query": specific search query for this step
- "source_types": array of source types to search ["web", "knowledge", "document"]
- "reason": why this step is needed

Return ONLY the JSON array, no other text."""

        try:
            response = await llm_gateway.acompletion(
                messages=[{"role": "user", "content": prompt}],
                task_category="planning",
            )
            content = response.get("content", "[]")
            start = content.find("[")
            end = content.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
        except Exception as e:
            logger.warning("Failed to generate research plan: %s", e)
        return [{"query": query, "source_types": ["web", "knowledge"], "reason": "Initial broad search"}]

    async def _search_sources(self, query: str, source_types: list[str]) -> list[dict]:
        sources = []
        if "knowledge" in source_types:
            try:
                from app.core.memory.manager import memory_manager
                memories = await memory_manager.retrieve(query, limit=5)
                for m in memories:
                    sources.append({"type": "knowledge", "content": m.get("content", ""), "relevance": m.get("score", 0)})
            except Exception as e:
                logger.warning("Knowledge search failed: %s", e)
        if "web" in source_types:
            try:
                from app.core.tools.search_tool import SearchTool
                search = SearchTool()
                await search._on_activate()
                try:
                    result = await search._on_call(query=query, max_results=5)
                    if isinstance(result, dict) and "results" in result:
                        for r in result["results"]:
                            sources.append({"type": "web", "title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("snippet", "")})
                finally:
                    await search._on_hibernate()
            except Exception as e:
                logger.warning("Web search failed: %s", e)
        return sources

    async def _analyze_sources(self, query: str, sources: list[dict]) -> list[dict]:
        if not sources:
            return []
        source_text = "\n".join([f"[{i+1}] {json.dumps(s, ensure_ascii=False)[:500]}" for i, s in enumerate(sources)])
        prompt = f"""Analyze the following sources in relation to the research question.

Research Question: {query}

Sources:
{source_text}

For each source, extract key findings relevant to the research question.
Return a JSON array of findings. Each finding should have:
- "source_index": index of the source (1-based)
- "finding": the key finding text
- "confidence": confidence score 0-1
- "relevance": relevance to the question 0-1

Return ONLY the JSON array."""

        try:
            response = await llm_gateway.acompletion(
                messages=[{"role": "user", "content": prompt}],
                task_category="daily",
            )
            content = response.get("content", "[]")
            start = content.find("[")
            end = content.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
        except Exception as e:
            logger.warning("Failed to analyze sources: %s", e)
        return []

    async def _generate_report(self, query: str, findings: list[dict], sources: list[dict]) -> str:
        findings_text = "\n".join([f"- {f.get('finding', '')} (confidence: {f.get('confidence', 0)})" for f in findings])
        sources_text = "\n".join([f"[{i+1}] {s.get('title', s.get('type', 'source'))}" for i, s in enumerate(sources)])
        prompt = f"""Write a comprehensive research report based on the findings below.

Research Question: {query}

Findings:
{findings_text}

Sources:
{sources_text}

Write a well-structured report with:
1. Executive Summary
2. Key Findings
3. Analysis
4. Conclusions
5. Recommendations
6. References

Write in Chinese (Simplified)."""

        try:
            response = await llm_gateway.acompletion(
                messages=[{"role": "user", "content": prompt}],
                task_category="planning",
            )
            return response.get("content", "")
        except Exception as e:
            logger.error("Report generation failed: %s", e)
            return "Report generation failed."

    async def _identify_gaps(self, query: str, findings: list[dict]) -> list[str]:
        findings_text = "\n".join([f"- {f.get('finding', '')}" for f in findings])
        prompt = f"""Based on the research question and current findings, identify information gaps that need further research.

Research Question: {query}

Current Findings:
{findings_text}

Return a JSON array of gap descriptions (strings). Each gap should be a specific question that needs answering.
Return ONLY the JSON array. If no gaps, return []."""

        try:
            response = await llm_gateway.acompletion(
                messages=[{"role": "user", "content": prompt}],
                task_category="intent",
            )
            content = response.get("content", "[]")
            start = content.find("[")
            end = content.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
        except Exception as e:
            logger.warning("Failed to identify gaps: %s", e)
        return []

    def _save(self, result: ResearchResult):
        path = os.path.join(_DATA_DIR, f"{result.id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)


deep_research_agent = DeepResearchAgent()
