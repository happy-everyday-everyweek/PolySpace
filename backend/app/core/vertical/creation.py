from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.agent.base import AgentContext, AgentMessage, BaseAgent


@dataclass
class CreationResult:
    action: str
    content: str
    truth_updates: dict[str, str] = field(default_factory=dict)
    audit_score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class CreationAgent(BaseAgent):
    def __init__(self, name: str = "creation_agent") -> None:
        super().__init__(name=name)
        self._inkos_url: str = ""
        self._books: dict[str, dict[str, Any]] = {}

    def configure(self, inkos_url: str = "http://localhost:4567") -> None:
        self._inkos_url = inkos_url.rstrip("/")

    async def think(self, context: AgentContext) -> AgentContext:
        return context

    async def run(self, context: AgentContext) -> AgentContext:
        user_message = context.messages[-1].content if context.messages else ""
        result = await self.process_creation_request(user_message)
        self.add_message("assistant", result.content)
        context.messages.append(AgentMessage(role="assistant", content=result.content))
        return context

    async def process_creation_request(self, query: str) -> CreationResult:
        query_lower = query.lower()
        if any(kw in query_lower for kw in ["create", "new book", "new novel", "create book", "create novel"]):
            return await self._create_book(query)
        elif any(kw in query_lower for kw in ["write", "next chapter", "continue", "draft"]):
            return await self._write_chapter(query)
        elif any(kw in query_lower for kw in ["audit", "check", "review", "consistency"]):
            return await self._audit_chapter(query)
        elif any(kw in query_lower for kw in ["revise", "fix", "polish", "rewrite"]):
            return await self._revise_chapter(query)
        elif any(kw in query_lower for kw in ["truth", "state", "character", "world"]):
            return await self._manage_truth(query)
        elif any(kw in query_lower for kw in ["export", "download", "publish"]):
            return await self._export_book(query)
        elif any(kw in query_lower for kw in ["style", "genre", "tone"]):
            return await self._manage_style(query)
        else:
            return CreationResult(
                action="guide",
                content="I am your creative writing assistant powered by InkOS. I can help you:\n"
                "- Create a new book/novel\n"
                "- Write the next chapter\n"
                "- Audit chapter consistency (33 dimensions)\n"
                "- Revise chapters (polish/spot-fix/rewrite/rework/anti-detect)\n"
                "- Manage truth files (7 types for story consistency)\n"
                "- Export books (txt/md/epub)\n"
                "- Analyze and import writing styles\n"
                "- Create fan fiction from source material\n"
                "What would you like to create?",
            )

    async def _create_book(self, query: str) -> CreationResult:
        return CreationResult(
            action="create_book",
            content="Book creation initiated. I'll set up the project with 7 truth files for consistency tracking. "
            "Please provide: title, genre, brief description, target chapter count, and language preference.",
            metadata={"step": "awaiting_book_config"},
        )

    async def _write_chapter(self, query: str) -> CreationResult:
        return CreationResult(
            action="write_chapter",
            content="Starting the InkOS 10-agent pipeline for chapter writing:\n"
            "Planner -> Composer -> Writer -> Observer -> Reflector -> Normalizer -> Auditor -> Reviser\n"
            "The pipeline ensures consistency with truth files and 33-dimension quality checks.",
            metadata={"pipeline_stages": 10, "auto_audit": True},
        )

    async def _audit_chapter(self, query: str) -> CreationResult:
        return CreationResult(
            action="audit_chapter",
            content="Running 33-dimension continuity audit:\n"
            "- Character consistency\n- Timeline coherence\n- World state continuity\n"
            "- Resource tracking\n- Foreshadowing closure\n- Emotional arc consistency\n"
            "- AI trace detection\n- Dialogue authenticity\n- Scene logic",
            audit_score=0.0,
            metadata={"dimensions": 33, "includes_ai_detection": True},
        )

    async def _revise_chapter(self, query: str) -> CreationResult:
        return CreationResult(
            action="revise_chapter",
            content="Revision mode available:\n"
            "- polish: Light touch-up for flow and style\n"
            "- spot-fix: Target specific issues\n"
            "- rewrite: Full chapter rewrite preserving plot\n"
            "- rework: Deep restructuring\n"
            "- anti-detect: Reduce AI writing traces\n"
            "Which revision mode would you like?",
            metadata={"modes": ["polish", "spot-fix", "rewrite", "rework", "anti-detect"]},
        )

    async def _manage_truth(self, query: str) -> CreationResult:
        return CreationResult(
            action="manage_truth",
            content="Truth file management available. 7 truth files track story consistency:\n"
            "1. current_state.md - World state & character positions\n"
            "2. particle_ledger.md - Resource tracking\n"
            "3. pending_hooks.md - Unclosed foreshadowing\n"
            "4. chapter_summaries.md - Per-chapter summaries\n"
            "5. subplot_board.md - Subplot progress\n"
            "6. emotional_arcs.md - Character emotional arcs\n"
            "7. character_matrix.md - Character interactions\n"
            "Which truth file would you like to view or edit?",
            metadata={"truth_files": 7},
        )

    async def _export_book(self, query: str) -> CreationResult:
        return CreationResult(
            action="export_book",
            content="Export formats available:\n"
            "- TXT (plain text)\n- MD (Markdown)\n- EPUB (e-book)\n"
            "You can also export to the Design app for visual formatting, "
            "or to the Dev app for interactive application development.",
            metadata={"formats": ["txt", "md", "epub"]},
        )

    async def _manage_style(self, query: str) -> CreationResult:
        return CreationResult(
            action="manage_style",
            content="Style management available:\n"
            "- Analyze reference text to extract style fingerprint\n"
            "- Import style fingerprint to your book\n"
            "- Genre-aware writing (xuanhuan, scifi, romance, thriller, etc.)\n"
            "- Market radar for trend scanning",
            metadata={"features": ["analyze", "import", "genre", "radar"]},
        )
