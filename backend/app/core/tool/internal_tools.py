from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

from app.core.tool.base import BaseTool


class EmailTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="email",
            description="Send emails and manage inbox. Compose, read, search emails.",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["send", "list", "search", "read", "delete", "mark_read"],
                        "description": "Email action",
                    },
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "body": {"type": "string", "description": "Email body content"},
                    "email_id": {"type": "string", "description": "Email ID for read/delete"},
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "integer", "description": "Max results to return"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "list")
        try:
            from app.services.email_service import email_service
            if action == "send":
                return await email_service.send_email(
                    to=kwargs.get("to", ""),
                    subject=kwargs.get("subject", ""),
                    body=kwargs.get("body", ""),
                )
            elif action == "list":
                limit = kwargs.get("limit", 20)
                return await email_service.list_emails(limit=limit)
            elif action == "search":
                return await email_service.search_emails(query=kwargs.get("query", ""))
            elif action == "read":
                return await email_service.read_email(email_id=kwargs.get("email_id", ""))
            elif action == "delete":
                return await email_service.delete_email(email_id=kwargs.get("email_id", ""))
            elif action == "mark_read":
                return await email_service.mark_read(email_id=kwargs.get("email_id", ""))
            else:
                return {"error": f"Unknown action: {action}"}
        except Exception as e:
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        pass


class CalendarTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="calendar",
            description="Manage calendar events. Create, list, search, update, delete events.",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create", "list", "search", "update", "delete", "today"],
                        "description": "Calendar action",
                    },
                    "title": {"type": "string", "description": "Event title"},
                    "start_time": {"type": "string", "description": "Event start time (ISO format)"},
                    "end_time": {"type": "string", "description": "Event end time (ISO format)"},
                    "description": {"type": "string", "description": "Event description"},
                    "event_id": {"type": "string", "description": "Event ID"},
                    "query": {"type": "string", "description": "Search query"},
                    "date": {"type": "string", "description": "Date filter (YYYY-MM-DD)"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "list")
        try:
            from app.services.calendar_service import calendar_service
            if action == "create":
                return await calendar_service.create_event(
                    title=kwargs.get("title", ""),
                    start_time=kwargs.get("start_time", ""),
                    end_time=kwargs.get("end_time", ""),
                    description=kwargs.get("description", ""),
                )
            elif action == "list":
                return await calendar_service.list_events(date=kwargs.get("date"))
            elif action == "search":
                return await calendar_service.search_events(query=kwargs.get("query", ""))
            elif action == "update":
                return await calendar_service.update_event(
                    event_id=kwargs.get("event_id", ""),
                    **{k: v for k, v in kwargs.items() if k in ("title", "start_time", "end_time", "description")},
                )
            elif action == "delete":
                return await calendar_service.delete_event(event_id=kwargs.get("event_id", ""))
            elif action == "today":
                return await calendar_service.list_events(date=datetime.now().strftime("%Y-%m-%d"))
            else:
                return {"error": f"Unknown action: {action}"}
        except Exception as e:
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        pass


class TodoTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="todo",
            description="Manage todo items. Create, list, update, delete tasks.",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create", "list", "update", "delete", "complete"],
                        "description": "Todo action",
                    },
                    "title": {"type": "string", "description": "Task title"},
                    "description": {"type": "string", "description": "Task description"},
                    "todo_id": {"type": "string", "description": "Task ID"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"], "description": "Priority"},
                    "due_date": {"type": "string", "description": "Due date"},
                    "status": {"type": "string", "description": "Task status"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "list")
        try:
            from app.services.todo_service import todo_service
            if action == "create":
                return await todo_service.create_todo(
                    title=kwargs.get("title", ""),
                    description=kwargs.get("description", ""),
                    priority=kwargs.get("priority", "medium"),
                    due_date=kwargs.get("due_date"),
                )
            elif action == "list":
                return await todo_service.list_todos()
            elif action == "update":
                return await todo_service.update_todo(
                    todo_id=kwargs.get("todo_id", ""),
                    **{k: v for k, v in kwargs.items() if k in ("title", "description", "priority", "due_date", "status")},
                )
            elif action == "delete":
                return await todo_service.delete_todo(todo_id=kwargs.get("todo_id", ""))
            elif action == "complete":
                return await todo_service.update_todo(
                    todo_id=kwargs.get("todo_id", ""),
                    status="completed",
                )
            else:
                return {"error": f"Unknown action: {action}"}
        except Exception as e:
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        pass


class KnowledgeTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="knowledge",
            description="Manage knowledge base. Add, search, list, delete knowledge entries.",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["add", "search", "list", "delete", "update"],
                        "description": "Knowledge action",
                    },
                    "title": {"type": "string", "description": "Entry title"},
                    "content": {"type": "string", "description": "Entry content"},
                    "entry_id": {"type": "string", "description": "Entry ID"},
                    "query": {"type": "string", "description": "Search query"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags"},
                    "category": {"type": "string", "description": "Category"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "list")
        try:
            from app.services.knowledge_service import knowledge_service
            if action == "add":
                return await knowledge_service.add_entry(
                    title=kwargs.get("title", ""),
                    content=kwargs.get("content", ""),
                    tags=kwargs.get("tags", []),
                    category=kwargs.get("category", ""),
                )
            elif action == "search":
                return await knowledge_service.search_entries(query=kwargs.get("query", ""))
            elif action == "list":
                return await knowledge_service.list_entries(category=kwargs.get("category"))
            elif action == "delete":
                return await knowledge_service.delete_entry(entry_id=kwargs.get("entry_id", ""))
            elif action == "update":
                return await knowledge_service.update_entry(
                    entry_id=kwargs.get("entry_id", ""),
                    **{k: v for k, v in kwargs.items() if k in ("title", "content", "tags", "category")},
                )
            else:
                return {"error": f"Unknown action: {action}"}
        except Exception as e:
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        pass


class KanbanTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="kanban",
            description="Manage kanban board. Create, list, move, delete cards and columns.",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create_card", "list_cards", "move_card", "delete_card", "list_columns", "create_column"],
                        "description": "Kanban action",
                    },
                    "title": {"type": "string", "description": "Card title"},
                    "description": {"type": "string", "description": "Card description"},
                    "card_id": {"type": "string", "description": "Card ID"},
                    "column_id": {"type": "string", "description": "Column ID"},
                    "target_column_id": {"type": "string", "description": "Target column ID for move"},
                    "color": {"type": "string", "description": "Card color"},
                    "priority": {"type": "string", "description": "Card priority"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "list_cards")
        try:
            from app.services.kanban_service import kanban_service
            if action == "create_card":
                return await kanban_service.create_card(
                    title=kwargs.get("title", ""),
                    description=kwargs.get("description", ""),
                    column_id=kwargs.get("column_id", ""),
                    color=kwargs.get("color"),
                    priority=kwargs.get("priority"),
                )
            elif action == "list_cards":
                return await kanban_service.list_cards(column_id=kwargs.get("column_id"))
            elif action == "move_card":
                return await kanban_service.move_card(
                    card_id=kwargs.get("card_id", ""),
                    target_column_id=kwargs.get("target_column_id", ""),
                )
            elif action == "delete_card":
                return await kanban_service.delete_card(card_id=kwargs.get("card_id", ""))
            elif action == "list_columns":
                return await kanban_service.list_columns()
            elif action == "create_column":
                return await kanban_service.create_column(title=kwargs.get("title", ""))
            else:
                return {"error": f"Unknown action: {action}"}
        except Exception as e:
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        pass


class MemoryTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="memory",
            description="Manage agent memory. Store, search, recall memories and interactions.",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["store", "search", "recall", "list", "delete"],
                        "description": "Memory action",
                    },
                    "content": {"type": "string", "description": "Memory content to store"},
                    "query": {"type": "string", "description": "Search query"},
                    "memory_id": {"type": "string", "description": "Memory ID"},
                    "memory_type": {"type": "string", "description": "Memory type (working/interaction)"},
                    "limit": {"type": "integer", "description": "Max results"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "list")
        try:
            from app.services.memory_service import memory_service
            if action == "store":
                return await memory_service.store_memory(
                    content=kwargs.get("content", ""),
                    memory_type=kwargs.get("memory_type", "working"),
                )
            elif action == "search":
                return await memory_service.search_memories(
                    query=kwargs.get("query", ""),
                    limit=kwargs.get("limit", 10),
                )
            elif action == "recall":
                return await memory_service.recall_memory(memory_id=kwargs.get("memory_id", ""))
            elif action == "list":
                return await memory_service.list_memories(
                    memory_type=kwargs.get("memory_type"),
                    limit=kwargs.get("limit", 20),
                )
            elif action == "delete":
                return await memory_service.delete_memory(memory_id=kwargs.get("memory_id", ""))
            else:
                return {"error": f"Unknown action: {action}"}
        except Exception as e:
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        pass


class CoordinationTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="coordination",
            description="Coordinate proactive services, schedule tasks, manage context-aware assistance.",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["schedule", "list_services", "trigger", "cancel", "get_context"],
                        "description": "Coordination action",
                    },
                    "service_name": {"type": "string", "description": "Service name"},
                    "schedule_time": {"type": "string", "description": "Schedule time (ISO format)"},
                    "task_id": {"type": "string", "description": "Task ID"},
                    "context_type": {"type": "string", "description": "Context type to retrieve"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "list_services")
        try:
            from app.services.coordination_service import coordination_service
            if action == "schedule":
                return await coordination_service.schedule_task(
                    service_name=kwargs.get("service_name", ""),
                    schedule_time=kwargs.get("schedule_time", ""),
                )
            elif action == "list_services":
                return await coordination_service.list_services()
            elif action == "trigger":
                return await coordination_service.trigger_service(
                    service_name=kwargs.get("service_name", ""),
                )
            elif action == "cancel":
                return await coordination_service.cancel_task(task_id=kwargs.get("task_id", ""))
            elif action == "get_context":
                return await coordination_service.get_context(
                    context_type=kwargs.get("context_type", "current"),
                )
            else:
                return {"error": f"Unknown action: {action}"}
        except Exception as e:
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        pass


class PdfTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="pdf",
            description="Process PDF files. Extract text, summarize, and analyze PDF documents.",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["extract_text", "summarize", "analyze", "list"],
                        "description": "PDF action",
                    },
                    "file_path": {"type": "string", "description": "PDF file path"},
                    "page_range": {"type": "string", "description": "Page range (e.g., '1-5')"},
                    "query": {"type": "string", "description": "Query for analysis"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "list")
        try:
            from app.services.pdf_service import pdf_service
            if action == "extract_text":
                return await pdf_service.extract_text(
                    file_path=kwargs.get("file_path", ""),
                    page_range=kwargs.get("page_range"),
                )
            elif action == "summarize":
                return await pdf_service.summarize(
                    file_path=kwargs.get("file_path", ""),
                )
            elif action == "analyze":
                return await pdf_service.analyze(
                    file_path=kwargs.get("file_path", ""),
                    query=kwargs.get("query", ""),
                )
            elif action == "list":
                return await pdf_service.list_pdfs()
            else:
                return {"error": f"Unknown action: {action}"}
        except Exception as e:
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        pass


class MarkitdownTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="markitdown",
            description="Convert various document formats to Markdown. Support Word, Excel, PPT, HTML, etc.",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["convert", "list_supported"],
                        "description": "Markitdown action",
                    },
                    "file_path": {"type": "string", "description": "Source file path"},
                    "output_path": {"type": "string", "description": "Output Markdown file path"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "list_supported")
        try:
            if action == "convert":
                from app.services.markitdown_service import markitdown_service
                return await markitdown_service.convert(
                    file_path=kwargs.get("file_path", ""),
                    output_path=kwargs.get("output_path"),
                )
            elif action == "list_supported":
                return {
                    "supported_formats": [
                        ".docx", ".xlsx", ".pptx", ".html", ".htm",
                        ".csv", ".json", ".xml", ".yaml", ".yml",
                        ".md", ".txt", ".rtf", ".odt", ".pdf",
                    ]
                }
            else:
                return {"error": f"Unknown action: {action}"}
        except Exception as e:
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        pass


class TaskSupplementTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="task_supplement",
            description="Supplement task details with additional context, subtasks, or metadata.",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["add_context", "add_subtask", "get_details", "update_status"],
                        "description": "Task supplement action",
                    },
                    "task_id": {"type": "string", "description": "Task ID"},
                    "context": {"type": "string", "description": "Additional context"},
                    "subtask_title": {"type": "string", "description": "Subtask title"},
                    "status": {"type": "string", "description": "New status"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "get_details")
        try:
            from app.services.task_service import task_service
            if action == "add_context":
                return await task_service.add_context(
                    task_id=kwargs.get("task_id", ""),
                    context=kwargs.get("context", ""),
                )
            elif action == "add_subtask":
                return await task_service.add_subtask(
                    task_id=kwargs.get("task_id", ""),
                    subtask_title=kwargs.get("subtask_title", ""),
                )
            elif action == "get_details":
                return await task_service.get_details(task_id=kwargs.get("task_id", ""))
            elif action == "update_status":
                return await task_service.update_status(
                    task_id=kwargs.get("task_id", ""),
                    status=kwargs.get("status", ""),
                )
            else:
                return {"error": f"Unknown action: {action}"}
        except Exception as e:
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        pass


def register_internal_tools() -> list[BaseTool]:
    return [
        EmailTool(),
        CalendarTool(),
        TodoTool(),
        KnowledgeTool(),
        KanbanTool(),
        MemoryTool(),
        CoordinationTool(),
        PdfTool(),
        MarkitdownTool(),
        TaskSupplementTool(),
    ]
