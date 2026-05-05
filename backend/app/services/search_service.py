from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Optional

from app.api.v1.search import SearchResult

logger = logging.getLogger(__name__)

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
_RECENT_FILE = os.path.join(_DATA_DIR, "recent_searches.json")


@dataclass
class CommandDef:
    id: str
    title: str
    description: str
    category: str
    icon: str
    action: str
    action_data: dict = field(default_factory=dict)
    keywords: list[str] = field(default_factory=list)


_BUILTIN_COMMANDS: list[CommandDef] = [
    CommandDef("nav_agent", "AI 助手", "切换到 AI 助手对话模式", "navigation", "message-circle", "navigate", {"path": "/"}, ["agent", "chat", "ai", "助手", "对话"]),
    CommandDef("nav_workspace", "工作台", "切换到工作台模式", "navigation", "layout-grid", "navigate", {"path": "/workspace"}, ["workspace", "工作台", "工具"]),
    CommandDef("nav_settings", "设置", "打开系统设置", "navigation", "settings", "navigate", {"path": "/settings"}, ["settings", "设置", "配置"]),
    CommandDef("cmd_clear", "清空对话", "清空当前对话记录", "command", "trash-2", "clear_chat", {}, ["clear", "清空", "清除"]),
    CommandDef("cmd_mode", "切换模式", "在 Agent 和工作台模式间切换", "command", "repeat", "toggle_mode", {}, ["mode", "模式", "切换"]),
    CommandDef("cmd_new_session", "新建会话", "创建新的聊天会话", "command", "plus", "new_session", {}, ["new", "新建", "会话"]),
    CommandDef("app_document", "Word 文档", "打开文档编辑器", "app", "file-text", "open_app", {"app": "document"}, ["word", "文档", "document"]),
    CommandDef("app_ppt", "PPT 演示", "打开演示文稿编辑器", "app", "presentation", "open_app", {"app": "ppt"}, ["ppt", "演示", "presentation"]),
    CommandDef("app_excel", "Excel 表格", "打开电子表格编辑器", "app", "table", "open_app", {"app": "excel"}, ["excel", "表格", "spreadsheet"]),
    CommandDef("app_calendar", "日历", "打开日历应用", "app", "calendar", "open_app", {"app": "calendar"}, ["calendar", "日历", "日程"]),
    CommandDef("app_todo", "待办事项", "打开待办列表", "app", "check-square", "open_app", {"app": "todo"}, ["todo", "待办", "任务"]),
    CommandDef("app_knowledge", "知识库", "打开知识库", "app", "book-open", "open_app", {"app": "knowledge"}, ["knowledge", "知识库", "wiki"]),
    CommandDef("app_memo", "备忘录", "打开备忘录", "app", "sticky-note", "open_app", {"app": "memo"}, ["memo", "备忘录", "笔记"]),
    CommandDef("app_email", "邮件", "打开邮件客户端", "app", "mail", "open_app", {"app": "email"}, ["email", "邮件", "mail"]),
    CommandDef("app_kanban", "看板", "打开看板管理", "app", "columns", "open_app", {"app": "kanban"}, ["kanban", "看板", "board"]),
    CommandDef("app_mindmap", "思维导图", "打开思维导图", "app", "git-branch", "open_app", {"app": "mindmap"}, ["mindmap", "思维导图", "脑图"]),
    CommandDef("app_notes", "笔记", "打开笔记编辑器", "app", "edit-3", "open_app", {"app": "notes"}, ["notes", "笔记", "markdown"]),
    CommandDef("app_code", "代码编辑器", "打开代码编辑器", "app", "code", "open_app", {"app": "code"}, ["code", "代码", "editor"]),
    CommandDef("app_finance", "财务管理", "打开财务管理", "app", "trending-up", "open_app", {"app": "finance"}, ["finance", "财务", "预算"]),
    CommandDef("app_weather", "天气", "查看天气信息", "app", "cloud", "open_app", {"app": "weather"}, ["weather", "天气"]),
    CommandDef("app_focus", "专注计时", "打开番茄钟", "app", "clock", "open_app", {"app": "focus"}, ["focus", "专注", "番茄钟", "pomodoro"]),
    CommandDef("app_contacts", "联系人", "打开联系人管理", "app", "users", "open_app", {"app": "contacts"}, ["contacts", "联系人", "通讯录"]),
    CommandDef("app_reader", "阅读器", "打开阅读器", "app", "book", "open_app", {"app": "reader"}, ["reader", "阅读", "pdf"]),
    CommandDef("app_music", "音乐播放", "打开音乐播放器", "app", "music", "open_app", {"app": "music"}, ["music", "音乐", "白噪音"]),
    CommandDef("app_image", "图片编辑", "打开图片编辑器", "app", "image", "open_app", {"app": "image"}, ["image", "图片", "编辑"]),
    CommandDef("app_video", "视频编辑", "打开视频编辑器", "app", "film", "open_app", {"app": "video"}, ["video", "视频", "剪辑"]),
    CommandDef("app_calculator", "计算器", "打开计算器", "app", "calculator", "open_app", {"app": "calculator"}, ["calculator", "计算器", "数学"]),
    CommandDef("app_screenrecorder", "屏幕录制", "打开屏幕录制", "app", "monitor", "open_app", {"app": "screenrecorder"}, ["screen", "录制", "录屏"]),
    CommandDef("app_dataviz", "数据可视化", "打开数据可视化工具", "app", "bar-chart", "open_app", {"app": "dataviz"}, ["dataviz", "可视化", "图表", "chart"]),
    CommandDef("app_research", "深度研究", "打开深度研究模式", "app", "search", "open_app", {"app": "research"}, ["research", "研究", "调研"]),
    CommandDef("app_clipboard", "剪贴板历史", "打开智能剪贴板", "app", "clipboard", "open_app", {"app": "clipboard"}, ["clipboard", "剪贴板", "历史"]),
    CommandDef("app_workflow", "工作流构建", "打开工作流构建器", "app", "workflow", "open_app", {"app": "workflow"}, ["workflow", "工作流", "自动化"]),
    CommandDef("set_general", "通用设置", "语言、主题等通用设置", "setting", "sliders", "open_setting", {"tab": "general"}, ["general", "通用", "语言", "主题"]),
    CommandDef("set_agent", "Agent 设置", "模型配置、人格设置", "setting", "cpu", "open_setting", {"tab": "agent"}, ["agent", "模型", "人格", "persona"]),
    CommandDef("set_distributed", "分布式设置", "设备同步、GitHub 令牌", "setting", "share-2", "open_setting", {"tab": "distributed"}, ["distributed", "分布式", "同步"]),
    CommandDef("set_lab", "实验室", "本地推理、离线功能", "setting", "flask-conical", "open_setting", {"tab": "lab"}, ["lab", "实验室", "离线"]),
    CommandDef("act_research", "深度研究", "对任意主题进行多步骤深度研究", "action", "microscope", "deep_research", {}, ["research", "研究", "调研", "深度"]),
    CommandDef("act_summarize", "总结内容", "AI 总结当前内容", "action", "file-text", "ai_action", {"action": "summarize"}, ["summarize", "总结", "摘要"]),
    CommandDef("act_translate", "翻译", "AI 翻译选中文本", "action", "languages", "ai_action", {"action": "translate"}, ["translate", "翻译"]),
    CommandDef("act_explain", "解释", "AI 解释选中文本", "action", "help-circle", "ai_action", {"action": "explain"}, ["explain", "解释", "说明"]),
    CommandDef("act_rewrite", "改写", "AI 改写选中文本", "action", "edit", "ai_action", {"action": "rewrite"}, ["rewrite", "改写", "润色"]),
]

VALID_SCOPES = {
    "all", "knowledge", "memo", "todo", "document", "calendar",
    "chat", "command", "app", "setting", "action", "navigation",
    "memory",
}


class SearchService:
    def __init__(self):
        self._commands = {c.id: c for c in _BUILTIN_COMMANDS}
        self._recent: list[str] = []
        self._load_recent()

    def _load_recent(self):
        try:
            if os.path.exists(_RECENT_FILE):
                with open(_RECENT_FILE, "r", encoding="utf-8") as f:
                    self._recent = json.load(f)
        except Exception as e:
            logger.debug("Failed to load recent searches: %s", e)
            self._recent = []

    def _save_recent(self):
        try:
            os.makedirs(os.path.dirname(_RECENT_FILE), exist_ok=True)
            with open(_RECENT_FILE, "w", encoding="utf-8") as f:
                json.dump(self._recent[:100], f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.debug("Failed to save recent searches: %s", e)

    def _score(self, query: str, text: str, keywords: list[str]) -> float:
        q = query.lower()
        score = 0.0
        if q in text.lower():
            score += 0.5
            if text.lower().startswith(q):
                score += 0.3
        for kw in keywords:
            if q in kw.lower() or kw.lower().startswith(q):
                score += 0.2
        score += SequenceMatcher(None, q, text.lower()).ratio() * 0.3
        return min(score, 1.0)

    def _text_match_score(self, query: str, *texts: str) -> float:
        q = query.lower()
        score = 0.0
        for i, text in enumerate(texts):
            if not text:
                continue
            t = text.lower()
            if q in t:
                weight = 0.6 if i == 0 else 0.4
                score += weight
                if t.startswith(q):
                    score += 0.2
            score += SequenceMatcher(None, q, t).ratio() * 0.15
        return min(score, 1.0)

    async def search(
        self, query: str, category: Optional[str] = None,
        limit: int = 20, scope: Optional[str] = None,
    ) -> list[SearchResult]:
        if scope and scope not in VALID_SCOPES:
            scope = "all"
        if not scope:
            scope = "all"

        results: list[tuple[float, SearchResult]] = []

        if scope in ("all", "navigation", "command", "app", "setting", "action"):
            results.extend(await self._search_commands(query, category, scope))

        if scope in ("all", "knowledge"):
            results.extend(await self._search_knowledge(query))

        if scope in ("all", "memo"):
            results.extend(await self._search_memos(query))

        if scope in ("all", "todo"):
            results.extend(await self._search_todos(query))

        if scope in ("all", "document"):
            results.extend(await self._search_documents(query))

        if scope in ("all", "calendar"):
            results.extend(await self._search_calendar(query))

        if scope in ("all", "chat"):
            results.extend(await self._search_chat(query))

        if scope in ("all", "memory"):
            results.extend(await self._search_memory(query))

        results.sort(key=lambda x: x[0], reverse=True)

        if query not in self._recent:
            self._recent.insert(0, query)
            self._recent = self._recent[:100]
            self._save_recent()

        return [r for _, r in results[:limit]]

    async def _search_commands(
        self, query: str, category: Optional[str] = None,
        scope: Optional[str] = None,
    ) -> list[tuple[float, SearchResult]]:
        results: list[tuple[float, SearchResult]] = []
        for cmd in _BUILTIN_COMMANDS:
            if category and cmd.category != category:
                continue
            if scope and scope not in ("all", cmd.category):
                continue
            score = self._score(query, cmd.title, cmd.keywords)
            if score > 0.05:
                results.append((
                    score,
                    SearchResult(
                        id=cmd.id,
                        title=cmd.title,
                        description=cmd.description,
                        category=cmd.category,
                        icon=cmd.icon,
                        action=cmd.action,
                        action_data=cmd.action_data,
                        score=round(score, 3),
                    ),
                ))
        return results

    async def _search_knowledge(self, query: str) -> list[tuple[float, SearchResult]]:
        results: list[tuple[float, SearchResult]] = []
        try:
            from app.services.knowledge_service import knowledge_service
            entries = await knowledge_service.search(query, limit=10)
            for entry in entries:
                score = self._text_match_score(query, entry.title, entry.content)
                if score > 0.05:
                    results.append((
                        score,
                        SearchResult(
                            id=f"knowledge-{entry.entry_id}",
                            title=entry.title,
                            description=entry.content[:120] if entry.content else "",
                            category="knowledge",
                            icon="book-open",
                            action="open_app",
                            action_data={"app": "knowledge", "entry_id": entry.entry_id},
                            score=round(score, 3),
                        ),
                    ))
        except Exception as e:
            logger.debug("Search sub-task failed: %s", e)
        return results

    async def _search_memos(self, query: str) -> list[tuple[float, SearchResult]]:
        results: list[tuple[float, SearchResult]] = []
        try:
            from app.services.memo_service import memo_service
            memos = await memo_service.search_memos(query)
            for memo in memos[:10]:
                score = self._text_match_score(query, memo.title, memo.content)
                if score > 0.05:
                    results.append((
                        score,
                        SearchResult(
                            id=f"memo-{memo.memo_id}",
                            title=memo.title,
                            description=memo.content[:120] if memo.content else "",
                            category="memo",
                            icon="sticky-note",
                            action="open_app",
                            action_data={"app": "memo", "memo_id": memo.memo_id},
                            score=round(score, 3),
                        ),
                    ))
        except Exception as e:
            logger.debug("Search sub-task failed: %s", e)
        return results

    async def _search_todos(self, query: str) -> list[tuple[float, SearchResult]]:
        results: list[tuple[float, SearchResult]] = []
        try:
            from app.services.todo_service import todo_service
            todos = await todo_service.list_tasks()
            for todo in todos:
                score = self._text_match_score(query, todo["title"], todo.get("description", ""))
                if score > 0.05:
                    status_label = "已完成" if todo["status"] == "completed" else "待完成"
                    results.append((
                        score,
                        SearchResult(
                            id=f"todo-{todo['id']}",
                            title=todo["title"],
                            description=(
                                f"{status_label} · {todo.get('description', '')[:80]}"
                                if todo.get("description") else status_label
                            ),
                            category="todo",
                            icon="check-square",
                            action="open_app",
                            action_data={"app": "todo", "todo_id": todo.todo_id},
                            score=round(score, 3),
                        ),
                    ))
        except Exception as e:
            logger.debug("Search sub-task failed: %s", e)
        return results

    async def _search_documents(self, query: str) -> list[tuple[float, SearchResult]]:
        results: list[tuple[float, SearchResult]] = []
        try:
            from app.services.workspace_service import workspace_service
            docs = await workspace_service.list_documents()
            for doc in docs:
                score = self._text_match_score(query, doc.title, doc.content)
                if score > 0.05:
                    type_labels = {
                        "note": "笔记", "document": "文档", "spreadsheet": "表格",
                        "presentation": "演示", "pdf": "PDF", "code": "代码",
                    }
                    type_label = type_labels.get(doc.doc_type, doc.doc_type)
                    results.append((
                        score,
                        SearchResult(
                            id=f"document-{doc.doc_id}",
                            title=doc.title,
                            description=f"{type_label} · {doc.content[:80]}" if doc.content else type_label,
                            category="document",
                            icon="file-text",
                            action="open_document",
                            action_data={"app": "document", "doc_id": doc.doc_id},
                            score=round(score, 3),
                        ),
                    ))
        except Exception as e:
            logger.debug("Search sub-task failed: %s", e)
        return results

    async def _search_calendar(self, query: str) -> list[tuple[float, SearchResult]]:
        results: list[tuple[float, SearchResult]] = []
        try:
            from app.services.calendar_service import calendar_service
            events = await calendar_service.list_events()
            for event in events:
                score = self._text_match_score(query, event.title, event.description, event.location)
                if score > 0.05:
                    time_info = event.start_time[:16] if event.start_time else ""
                    results.append((
                        score,
                        SearchResult(
                            id=f"calendar-{event.event_id}",
                            title=event.title,
                            description=f"{time_info} · {event.description[:60]}" if event.description else time_info,
                            category="calendar",
                            icon="calendar",
                            action="open_app",
                            action_data={"app": "calendar", "event_id": event.event_id},
                            score=round(score, 3),
                        ),
                    ))
        except Exception as e:
            logger.debug("Search sub-task failed: %s", e)
        return results

    async def _search_chat(self, query: str) -> list[tuple[float, SearchResult]]:
        results: list[tuple[float, SearchResult]] = []
        try:
            from app.core.memory.manager import memory_manager
            memories = await memory_manager.retrieve(query, top_k=5)
            for mem in memories:
                content = mem.get("content", "")
                if not content:
                    continue
                score = self._text_match_score(query, content)
                if score > 0.05:
                    results.append((
                        score,
                        SearchResult(
                            id=f"chat-{mem.get('id', '')}",
                            title=content[:60],
                            description=content[:120],
                            category="chat",
                            icon="message-circle",
                            action="navigate",
                            action_data={"path": "/"},
                            score=round(score, 3),
                        ),
                    ))
        except Exception as e:
            logger.debug("Search sub-task failed: %s", e)
        return results

    async def _search_memory(self, query: str) -> list[tuple[float, SearchResult]]:
        results: list[tuple[float, SearchResult]] = []
        try:
            from app.core.memory.dual_memory import get_dual_memory
            dual = get_dual_memory()
            dual.ensure_loaded()
            search_result = dual.search_all(query, limit=10)
            working = search_result.get("working", [])
            for entry in working:
                content = entry.get("content", "") if isinstance(entry, dict) else str(entry)
                category = entry.get("category", "working") if isinstance(entry, dict) else "working"
                entry_id = entry.get("id", "") if isinstance(entry, dict) else ""
                tags = entry.get("tags", []) if isinstance(entry, dict) else []
                score = self._text_match_score(query, content, " ".join(tags) if isinstance(tags, list) else str(tags))
                if score > 0.05:
                    results.append((
                        score,
                        SearchResult(
                            id=f"memory-working-{entry_id}",
                            title=content[:60],
                            description=f"[工作记忆/{category}] {content[:100]}",
                            category="memory",
                            icon="map-pin",
                            action="open_memory",
                            action_data={"tab": "agent"},
                            score=round(score, 3),
                        ),
                    ))
            interaction = search_result.get("interaction", [])
            for entry in interaction:
                content = entry.get("content", "") if isinstance(entry, dict) else str(entry)
                category = entry.get("category", "interaction") if isinstance(entry, dict) else "interaction"
                entry_id = entry.get("id", "") if isinstance(entry, dict) else ""
                tags = entry.get("tags", []) if isinstance(entry, dict) else []
                score = self._text_match_score(query, content, " ".join(tags) if isinstance(tags, list) else str(tags))
                if score > 0.05:
                    results.append((
                        score,
                        SearchResult(
                            id=f"memory-interaction-{entry_id}",
                            title=content[:60],
                            description=f"[交互记忆/{category}] {content[:100]}",
                            category="memory",
                            icon="map-pin",
                            action="open_memory",
                            action_data={"tab": "agent"},
                            score=round(score, 3),
                        ),
                    ))
        except Exception as e:
            logger.debug("Search memory sub-task failed: %s", e)
        try:
            from app.core.memory.manager import memory_manager
            memories = await memory_manager.retrieve(query, top_k=5)
            for mem in memories:
                content = mem.get("content", "")
                if not content:
                    continue
                score = self._text_match_score(query, content)
                if score > 0.05:
                    mem_id = mem.get("id", "")
                    existing_ids = {r[1].id for r in results}
                    result_id = f"memory-mgr-{mem_id}"
                    if result_id in existing_ids:
                        continue
                    results.append((
                        score,
                        SearchResult(
                            id=result_id,
                            title=content[:60],
                            description=f"[记忆] {content[:100]}",
                            category="memory",
                            icon="map-pin",
                            action="open_memory",
                            action_data={"tab": "agent"},
                            score=round(score, 3),
                        ),
                    ))
        except Exception as e:
            logger.debug("Search memory manager sub-task failed: %s", e)
        return results

    async def suggest(self, query: str, limit: int = 5) -> list[str]:
        suggestions: list[tuple[float, str]] = []
        for cmd in _BUILTIN_COMMANDS:
            score = self._score(query, cmd.title, cmd.keywords)
            if score > 0.1:
                suggestions.append((score, cmd.title))
        suggestions.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in suggestions[:limit]]

    async def get_recent(self, limit: int = 10) -> list[str]:
        return self._recent[:limit]

    async def get_all_commands(self) -> list[dict]:
        return [
            {
                "id": c.id,
                "title": c.title,
                "description": c.description,
                "category": c.category,
                "icon": c.icon,
                "action": c.action,
                "action_data": c.action_data,
                "keywords": c.keywords,
            }
            for c in _BUILTIN_COMMANDS
        ]


search_service = SearchService()
