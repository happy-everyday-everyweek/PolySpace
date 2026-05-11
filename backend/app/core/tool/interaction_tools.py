import asyncio
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from app.config import settings
from app.core.tool.base import BaseTool

logger = logging.getLogger(__name__)


class AsyncTaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AsyncTask:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    goal: str = ""
    status: AsyncTaskStatus = AsyncTaskStatus.PENDING
    result: Any = None
    error: str = ""
    progress: float = 0.0
    progress_message: str = ""
    supplements: list[dict[str, Any]] = field(default_factory=list)
    steps: list[dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    completed_at: float | None = None
    session_id: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "description": self.description,
            "goal": self.goal,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "progress": self.progress,
            "progress_message": self.progress_message,
            "supplements": self.supplements,
            "steps": self.steps,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "session_id": self.session_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AsyncTask":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            description=data.get("description", ""),
            goal=data.get("goal", ""),
            status=AsyncTaskStatus(data.get("status", "pending")),
            result=data.get("result"),
            error=data.get("error", ""),
            progress=data.get("progress", 0.0),
            progress_message=data.get("progress_message", ""),
            supplements=data.get("supplements", []),
            steps=data.get("steps", []),
            created_at=data.get("created_at", time.time()),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            session_id=data.get("session_id", ""),
        )


class AsyncTaskStore:
    _BASE_DIR = Path(settings.DATA_DIR)

    def __init__(self, storage_dir: Path | str | None = None):
        if storage_dir is None:
            storage_dir = self._BASE_DIR / "tasks"
        self._dir = Path(storage_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._pending_count: int = 0
        self._flush_threshold: int = 5
        self._flush_task: asyncio.Task | None = None

    def _file_path(self) -> Path:
        return self._dir / "async_tasks.json"

    def load_all(self) -> dict[str, AsyncTask]:
        fp = self._file_path()
        if not fp.exists():
            return {}
        try:
            raw = fp.read_text(encoding="utf-8")
            data = json.loads(raw)
            tasks = {}
            for item in data.get("tasks", []):
                task = AsyncTask.from_dict(item)
                tasks[task.id] = task
            return tasks
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Failed to load async tasks: %s", e)
            return {}

    def save_all(self, tasks: dict[str, AsyncTask]) -> None:
        fp = self._file_path()
        try:
            data = {"tasks": [t.to_dict() for t in tasks.values()]}
            tmp = fp.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(fp)
        except OSError as e:
            logger.error("Failed to save async tasks: %s", e)

    def schedule_flush(self, tasks: dict[str, AsyncTask]) -> None:
        self._pending_count += 1
        if self._pending_count >= self._flush_threshold:
            self.save_all(tasks)
            self._pending_count = 0
        else:
            self._deferred_flush(tasks)

    def _deferred_flush(self, tasks: dict[str, AsyncTask]) -> None:
        if self._flush_task is None or self._flush_task.done():
            try:
                loop = asyncio.get_running_loop()
                self._flush_task = loop.create_task(self._delayed_flush(tasks))
            except RuntimeError:
                self.save_all(tasks)
                self._pending_count = 0

    async def _delayed_flush(self, tasks: dict[str, AsyncTask]) -> None:
        await asyncio.sleep(2.0)
        self.save_all(tasks)
        self._pending_count = 0


class AsyncTaskManager:
    _instance: Optional["AsyncTaskManager"] = None

    def __init__(self):
        self._tasks: dict[str, AsyncTask] = {}
        self._store = AsyncTaskStore()
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        self._on_task_event = None
        self._load_persisted_tasks()

    def _load_persisted_tasks(self) -> None:
        persisted = self._store.load_all()
        for task_id, task in persisted.items():
            if task.status in (AsyncTaskStatus.PENDING, AsyncTaskStatus.RUNNING):
                task.status = AsyncTaskStatus.PENDING
                task.progress = 0.0
                task.progress_message = "Awaiting retry after restart"
            self._tasks[task_id] = task
        if persisted:
            pending_count = sum(
                1 for t in persisted.values()
                if t.status == AsyncTaskStatus.PENDING
            )
            logger.info(
                f"Loaded {len(persisted)} persisted tasks "
                f"({pending_count} pending retry)"
            )

    def set_task_event_callback(self, callback) -> None:
        self._on_task_event = callback

    def _emit_event(self, event_type: str, task: AsyncTask, **extra) -> None:
        if self._on_task_event:
            try:
                self._on_task_event(event_type, task, **extra)
            except Exception as e:
                logger.error(f"Task event callback error: {e}")

    def _persist(self) -> None:
        self._store.schedule_flush(self._tasks)

    @classmethod
    def get_instance(cls) -> "AsyncTaskManager":
        if cls._instance is None:
            cls._instance = AsyncTaskManager()
        return cls._instance

    def create_task(
        self,
        description: str,
        goal: str = "",
        session_id: str = "",
    ) -> AsyncTask:
        task = AsyncTask(
            description=description,
            goal=goal,
            session_id=session_id,
        )
        self._tasks[task.id] = task
        self._queue.put_nowait(task.id)
        self._persist()
        logger.info(f"Created async task {task.id}: {description[:80]}")
        self._emit_event("created", task)
        return task

    def supplement_task(self, task_id: str, info: str, source: str = "user") -> dict:
        task = self._tasks.get(task_id)
        if task is None:
            return {"error": f"Task {task_id} not found"}
        if task.status in (AsyncTaskStatus.COMPLETED, AsyncTaskStatus.CANCELLED):
            return {"error": f"Task {task_id} is already {task.status.value}"}
        supplement = {
            "info": info,
            "source": source,
            "timestamp": time.time(),
        }
        task.supplements.append(supplement)
        self._persist()
        logger.info(f"Supplemented task {task_id}: {info[:80]}")
        self._emit_event("supplemented", task, supplement=info)
        return {"task_id": task_id, "supplemented": True, "total_supplements": len(task.supplements)}

    def get_task(self, task_id: str) -> Optional[AsyncTask]:
        return self._tasks.get(task_id)

    def list_tasks(self, session_id: str = "", limit: int = 50) -> list[dict]:
        tasks = list(self._tasks.values())
        if session_id:
            tasks = [t for t in tasks if t.session_id == session_id]
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return [t.to_dict() for t in tasks[:limit]]

    def update_task_progress(self, task_id: str, progress: float, message: str = "") -> None:
        task = self._tasks.get(task_id)
        if task:
            task.progress = min(1.0, max(0.0, progress))
            task.progress_message = message
            self._persist()

    def add_task_step(self, task_id: str, step: dict) -> None:
        task = self._tasks.get(task_id)
        if task:
            task.steps.append(step)
            self._persist()

    async def start_worker(self) -> None:
        if self._running:
            return
        self._running = True
        self._worker_task = asyncio.create_task(self._worker_loop())
        logger.info("AsyncTaskManager worker started")

    async def stop_worker(self) -> None:
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            self._worker_task = None
        self._persist()
        logger.info("AsyncTaskManager worker stopped")

    async def _worker_loop(self) -> None:
        while self._running:
            try:
                task_id = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                asyncio.create_task(self._execute_task(task_id))
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker loop error: {e}")

    async def _execute_task(self, task_id: str) -> None:
        task = self._tasks.get(task_id)
        if task is None:
            return

        task.status = AsyncTaskStatus.RUNNING
        task.started_at = time.time()
        task.progress = 0.0
        task.progress_message = "Starting execution..."
        self._persist()
        self._emit_event("started", task)

        try:
            from app.core.agent.execution import ExecutionAgent
            from app.core.llm.dispatcher import get_model_dispatcher
            from app.core.tool.registry import tool_registry

            dispatcher = get_model_dispatcher()
            agent = ExecutionAgent(
                model_dispatcher=dispatcher,
                tool_registry=tool_registry,
            )

            full_prompt = task.description
            if task.goal:
                full_prompt += f"\nGoal: {task.goal}"
            for supp in task.supplements:
                full_prompt += f"\nAdditional requirement ({supp['source']}): {supp['info']}"

            def on_step(step):
                task.progress = min(0.9, task.progress + 0.1)
                task.progress_message = f"Step {step.step_number}: {step.action or 'thinking...'}"
                self.add_task_step(task_id, {
                    "step_number": step.step_number,
                    "thought": step.thought[:200] if step.thought else "",
                    "action": step.action,
                    "observation": (step.observation or "")[:200],
                    "duration_ms": step.duration_ms,
                })

            agent.set_step_callback(on_step)

            result = await agent.run(full_prompt, thread_id=task_id)

            task.result = result
            task.status = AsyncTaskStatus.COMPLETED
            task.progress = 1.0
            task.progress_message = "Completed"
            task.completed_at = time.time()
            self._persist()
            logger.info(f"Task {task_id} completed")
            self._emit_event("completed", task, result=result)

        except Exception as e:
            task.status = AsyncTaskStatus.FAILED
            task.error = str(e)
            task.progress_message = f"Failed: {str(e)[:100]}"
            task.completed_at = time.time()
            self._persist()
            logger.error(f"Task {task_id} failed: {e}")
            self._emit_event("failed", task, error=str(e))


async_task_manager = AsyncTaskManager.get_instance()


class ReadFileTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="read_file",
            description=(
                "读取文件内容。当用户要求查看、读取、打开某个文件时必须调用此工具。"
                "支持文档、PDF、代码文件、图片、电子表格等多种格式。"
                "系统会根据自然语言描述自动匹配并返回文件内容。"
            ),
            parameters={
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "要读取的文件的自然语言描述，例如'昨天的会议纪要'、'Q3财务报告'",
                    },
                    "file_path": {
                        "type": "string",
                        "description": "可选的精确文件路径，如果已知的话",
                    },
                },
                "required": ["description"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        description = kwargs.get("description", "")
        file_path = kwargs.get("file_path", "")

        if file_path and os.path.exists(file_path):
            return await self._read_file(file_path)

        matched_path = await self._find_file(description)
        if matched_path:
            return await self._read_file(matched_path)

        return {"error": f"Could not find a file matching: {description}"}

    async def _find_file(self, description: str) -> str | None:
        safe_base_dirs = [
            os.path.realpath(os.path.join(os.getcwd(), "data", "uploads")),
            os.path.realpath(os.path.join(os.getcwd(), "data", "documents")),
            os.path.realpath(os.path.join(os.getcwd(), "data", "files")),
        ]

        desc_lower = description.lower()
        keywords = [w for w in desc_lower.replace(",", " ").replace(".", " ").split() if len(w) > 1]

        candidates: list[tuple[float, str]] = []

        for search_dir in safe_base_dirs:
            if not os.path.exists(search_dir):
                continue
            for root, dirs, files in os.walk(search_dir):
                real_root = os.path.realpath(root)
                if not any(real_root.startswith(safe) for safe in safe_base_dirs):
                    continue
                for fname in files:
                    fpath = os.path.join(root, fname)
                    real_fpath = os.path.realpath(fpath)
                    if not any(real_fpath.startswith(safe) for safe in safe_base_dirs):
                        continue
                    fname_lower = fname.lower()
                    score = 0.0
                    for kw in keywords:
                        if kw in fname_lower:
                            score += 1.0
                    if score > 0:
                        candidates.append((score, fpath))

        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1] if candidates else None

    async def _read_file(self, file_path: str) -> dict:
        try:
            resolved_path = os.path.realpath(file_path)
            safe_dirs = [
                os.path.realpath(os.path.join(os.getcwd(), "data", "uploads")),
                os.path.realpath(os.path.join(os.getcwd(), "data", "documents")),
                os.path.realpath(os.path.join(os.getcwd(), "data", "files")),
                os.path.realpath(os.getcwd()),
            ]
            if not any(resolved_path.startswith(safe_dir) for safe_dir in safe_dirs):
                return {"error": "Access denied: file path outside allowed directories"}

            if not os.path.isfile(resolved_path):
                return {"error": "Not a file or file does not exist"}

            ext = os.path.splitext(file_path)[1].lower()

            if ext == ".pdf":
                try:
                    import fitz
                    doc = fitz.open(file_path)
                    page_count = len(doc)
                    text = ""
                    for page in doc:
                        text += page.get_text()
                    doc.close()
                    return {
                        "file_path": file_path,
                        "type": "pdf",
                        "content": text[:100000],
                        "pages": page_count,
                    }
                except ImportError:
                    return {"error": "PyMuPDF not installed"}

            elif ext in (".docx", ".pptx", ".xlsx", ".html", ".csv", ".json", ".xml"):
                try:
                    from markitdown import MarkItDown
                    md = MarkItDown()
                    result = md.convert(file_path)
                    return {
                        "file_path": file_path,
                        "type": ext.lstrip("."),
                        "content": result.text_content[:100000],
                    }
                except ImportError:
                    pass

            if ext in (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg"):
                return {
                    "file_path": file_path,
                    "type": "image",
                    "content": f"[Image file: {os.path.basename(file_path)}]",
                    "size": os.path.getsize(file_path),
                }

            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(100000)

            return {
                "file_path": file_path,
                "type": "text",
                "content": content,
                "size": os.path.getsize(file_path),
            }

        except Exception as e:
            return {"error": f"Failed to read file: {str(e)}"}

    async def _on_hibernate(self) -> None:
        pass


class SearchAggregateTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="search",
            description=(
                "聚合搜索查询。当用户要求搜索、查找、查询某些信息时必须调用此工具。"
                "可跨知识库、备忘录、待办、邮件、文件和网络进行搜索，返回汇总结果。"
            ),
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "自然语言搜索查询，描述你想查找的内容",
                    },
                    "scope": {
                        "type": "string",
                        "enum": ["all", "knowledge", "memos", "todos", "emails", "files", "web"],
                        "description": "搜索范围。使用'all'搜索所有来源，或指定特定来源。",
                        "default": "all",
                    },
                },
                "required": ["query"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        query = kwargs.get("query", "")
        scope = kwargs.get("scope", "all")

        if not query:
            return {"error": "Query is required"}

        results: dict[str, Any] = {"query": query, "scope": scope, "sources": {}}

        if scope in ("all", "knowledge"):
            try:
                from app.services.knowledge_service import KnowledgeService
                svc = KnowledgeService()
                entries = await svc.search(query, limit=5)
                if entries:
                    results["sources"]["knowledge"] = [
                        {"id": e.entry_id, "title": e.title, "preview": (e.content or "")[:200]}
                        for e in entries
                    ]
            except Exception:
                pass

        if scope in ("all", "notes"):
            try:
                from app.services.notes_service import notes_service
                notes = await notes_service.search_notes(query)
                if notes:
                    results["sources"]["notes"] = [
                        {"id": n.id, "title": n.title, "preview": (n.content or "")[:200]}
                        for n in notes[:5]
                    ]
            except Exception:
                pass

        if scope in ("all", "todos"):
            try:
                from app.services.todo_service import todo_service
                todos = await todo_service.list_tasks()
                matched = [t for t in todos if query.lower() in t["title"].lower()][:5]
                if matched:
                    results["sources"]["todos"] = [
                        {"id": t["id"], "title": t["title"], "status": t["status"], "priority": t["priority"]}
                        for t in matched
                    ]
            except Exception:
                pass

        if scope in ("all", "emails"):
            try:
                from app.services.email.service import get_email_service
                svc = get_email_service()
                emails = await svc.fetch_emails(1, folder="INBOX", limit=10, search=query)
                if emails:
                    results["sources"]["emails"] = [
                        {"id": e.get("id"), "subject": e.get("subject", ""), "from": e.get("from", "")}
                        for e in emails[:5]
                    ]
            except Exception:
                pass

        if scope in ("all", "files"):
            try:
                file_results = await self._search_files(query)
                if file_results:
                    results["sources"]["files"] = file_results
            except Exception:
                pass

        if scope in ("all", "web"):
            try:
                from app.core.tools.search_tool import SearchTool
                search = SearchTool()
                web_results = await search._on_call(query=query, max_results=5)
                if web_results and ((not isinstance(web_results, dict)) or web_results.get("results")):
                    results["sources"]["web"] = web_results.get("results", web_results)
            except Exception:
                pass

        if scope in ("all",) and "memory" not in scope:
            try:
                from app.core.memory.dual_memory import get_dual_memory
                dual = get_dual_memory()
                dual.ensure_loaded()
                memory_results = dual.search_all(query, limit=5)
                if memory_results:
                    results["sources"]["memory"] = [
                        {"id": r.id, "content": r.content[:200], "category": r.category}
                        for r in memory_results
                    ]
            except Exception:
                pass

        total = sum(len(v) for v in results["sources"].values() if isinstance(v, list))
        results["total_results"] = total
        results["summary"] = self._generate_summary(results)

        return results

    async def _search_files(self, query: str) -> list[dict]:
        import os
        search_dirs = [
            os.path.join(os.getcwd(), "data", "uploads"),
            os.path.join(os.getcwd(), "data", "documents"),
        ]
        results = []
        desc_lower = query.lower()
        keywords = [w for w in desc_lower.replace(",", " ").replace(".", " ").split() if len(w) > 1]

        for search_dir in search_dirs:
            if not os.path.exists(search_dir):
                continue
            for root, dirs, files in os.walk(search_dir):
                for fname in files:
                    fname_lower = fname.lower()
                    if any(kw in fname_lower for kw in keywords):
                        results.append({
                            "name": fname,
                            "path": os.path.join(root, fname),
                            "size": os.path.getsize(os.path.join(root, fname)),
                        })
                        if len(results) >= 10:
                            return results
        return results

    def _generate_summary(self, results: dict) -> str:
        parts = []
        sources = results.get("sources", {})
        if not sources:
            return "No results found across any data source."

        for source_name, items in sources.items():
            if isinstance(items, list) and items:
                parts.append(f"{source_name}: {len(items)} result(s)")
            elif isinstance(items, dict) and items:
                parts.append(f"{source_name}: results found")

        total = results.get("total_results", 0)
        return f"Found {total} result(s) across {len(parts)} source(s): {', '.join(parts)}."

    async def _on_hibernate(self) -> None:
        pass


class ExecuteTaskTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="execute_task",
            description=(
                "创建异步执行任务。这是最重要的工具！"
                "当用户要求创建、修改、编辑文档/文件，或执行任何需要'做某事'的操作时，"
                "你必须立即调用此工具，而不是只回复文字。"
                "返回任务ID和进度卡片，用户可随时查询进度或补充要求。"
            ),
            parameters={
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "任务的详细描述，说明要做什么",
                    },
                    "goal": {
                        "type": "string",
                        "description": "任务的预期目标或成果",
                    },
                    "task_id": {
                        "type": "string",
                        "description": "已有任务的ID，用于补充额外要求。创建新任务时留空。",
                    },
                    "supplement": {
                        "type": "string",
                        "description": "要补充到已有任务中的额外信息或要求（仅在提供task_id时使用）",
                    },
                },
                "required": ["description"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        description = kwargs.get("description", "")
        goal = kwargs.get("goal", "")
        task_id = kwargs.get("task_id", "")
        supplement = kwargs.get("supplement", "")

        if task_id:
            if not supplement:
                return {"error": "supplement is required when task_id is provided"}
            result = async_task_manager.supplement_task(task_id, supplement, source="interaction_agent")
            if "error" in result:
                return result
            task = async_task_manager.get_task(task_id)
            return {
                "task_id": task_id,
                "action": "supplemented",
                "supplement": supplement,
                "total_supplements": len(task.supplements) if task else 0,
                "card": self._build_card(task) if task else None,
            }

        if not description:
            return {"error": "description is required for new tasks"}

        from app.dependencies import container
        session_id = ""
        try:
            chat_svc = container.get("chat_service")
            if chat_svc and hasattr(chat_svc, "_current_session_id"):
                session_id = chat_svc._current_session_id
        except Exception:
            pass

        task = async_task_manager.create_task(
            description=description,
            goal=goal,
            session_id=session_id,
        )

        return {
            "task_id": task.id,
            "action": "created",
            "status": task.status.value,
            "card": self._build_card(task),
        }

    def _build_card(self, task: AsyncTask) -> dict:
        return {
            "type": "task",
            "task_id": task.id,
            "description": task.description[:100],
            "status": task.status.value,
            "progress": task.progress,
            "progress_message": task.progress_message,
        }

    async def _on_hibernate(self) -> None:
        pass


def register_interaction_tools():
    from app.core.tool.registry import ToolRegistry as _ToolRegistry

    registry = _ToolRegistry()
    tools = [
        ReadFileTool(),
        SearchAggregateTool(),
        ExecuteTaskTool(),
    ]
    registered = []
    for tool in tools:
        try:
            registry.register(tool)
            registered.append(tool.name)
        except Exception as e:
            logger.error(f"Failed to register interaction tool {tool.name}: {e}")

    logger.info(f"Registered {len(registered)} interaction tools: {registered}")
    return registry, registered
