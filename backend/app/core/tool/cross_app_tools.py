import logging
from typing import Any

from app.core.tool.base import BaseTool

logger = logging.getLogger(__name__)


class WorkspaceTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="workspace",
            description="Workspace management: status, open/close/switch apps, layout, tabs, recent, pin, fullscreen, split view, settings, shortcuts",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["status", "open_app", "close_app", "switch_app",
                                 "layout", "tabs", "recent", "pin", "fullscreen",
                                 "split_view", "settings", "shortcuts", "resize",
                                 "move", "minimize", "maximize"],
                        "description": "Workspace action",
                    },
                    "app_name": {"type": "string", "description": "Application name (document, ppt, excel, notes, etc.)"},
                    "app_id": {"type": "string", "description": "Application instance ID"},
                    "tab_id": {"type": "string", "description": "Tab ID"},
                    "layout_type": {"type": "string", "enum": ["single", "split_h", "split_v", "grid", "tabs"], "description": "Layout type"},
                    "position": {"type": "string", "enum": ["left", "right", "top", "bottom", "center"], "description": "Position for split view"},
                    "width": {"type": "integer", "description": "Window width"},
                    "height": {"type": "integer", "description": "Window height"},
                    "x": {"type": "integer", "description": "Window X position"},
                    "y": {"type": "integer", "description": "Window Y position"},
                    "setting_key": {"type": "string", "description": "Setting key"},
                    "setting_value": {"type": "string", "description": "Setting value"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "status")
        return {
            "action": "workspace_command",
            "app": "workspace",
            "command": action,
            "app_name": kwargs.get("app_name", ""),
            "app_id": kwargs.get("app_id", ""),
            "tab_id": kwargs.get("tab_id", ""),
            "layout_type": kwargs.get("layout_type", "single"),
            "position": kwargs.get("position", "center"),
            "width": kwargs.get("width", 0),
            "height": kwargs.get("height", 0),
            "x": kwargs.get("x", 0),
            "y": kwargs.get("y", 0),
            "setting_key": kwargs.get("setting_key", ""),
            "setting_value": kwargs.get("setting_value", ""),
        }

    async def _on_hibernate(self) -> None:
        pass


class WorkflowTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="workflow",
            description="Workflow orchestration: create, run, pause, resume, step through, branch, log, template, schedule, condition, loop, parallel execution",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create", "run", "pause", "resume", "step",
                                 "branch", "log", "template", "schedule",
                                 "condition", "loop", "parallel", "list",
                                 "delete", "status", "cancel"],
                        "description": "Workflow action",
                    },
                    "workflow_id": {"type": "string", "description": "Workflow ID"},
                    "name": {"type": "string", "description": "Workflow name"},
                    "description": {"type": "string", "description": "Workflow description"},
                    "steps": {"type": "array", "items": {"type": "object"}, "description": "Workflow steps"},
                    "template_name": {"type": "string", "description": "Template name"},
                    "schedule_time": {"type": "string", "description": "Schedule time (ISO format)"},
                    "condition_expr": {"type": "string", "description": "Condition expression"},
                    "loop_count": {"type": "integer", "description": "Loop iteration count"},
                    "parallel_steps": {"type": "array", "items": {"type": "object"}, "description": "Parallel step definitions"},
                    "branch_condition": {"type": "object", "description": "Branch condition"},
                    "branch_steps": {"type": "object", "description": "Branch step mappings"},
                    "step_index": {"type": "integer", "description": "Step index for step action"},
                    "variables": {"type": "object", "description": "Workflow variables"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "list")
        return {
            "action": "workspace_command",
            "app": "workflow",
            "command": action,
            "workflow_id": kwargs.get("workflow_id", ""),
            "name": kwargs.get("name", ""),
            "description": kwargs.get("description", ""),
            "steps": kwargs.get("steps", []),
            "template_name": kwargs.get("template_name", ""),
            "schedule_time": kwargs.get("schedule_time", ""),
            "condition_expr": kwargs.get("condition_expr", ""),
            "loop_count": kwargs.get("loop_count", 1),
            "parallel_steps": kwargs.get("parallel_steps", []),
            "branch_condition": kwargs.get("branch_condition", {}),
            "branch_steps": kwargs.get("branch_steps", {}),
            "step_index": kwargs.get("step_index", 0),
            "variables": kwargs.get("variables", {}),
        }

    async def _on_hibernate(self) -> None:
        pass


class DataBridgeTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="data_bridge",
            description="Data transfer between apps: copy data to another app, export as format, import from source, convert, sync, transform, validate, map fields",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["copy_to", "export_as", "import_from", "convert",
                                 "sync", "transform", "validate", "map_fields",
                                 "preview", "schedule", "history", "rollback"],
                        "description": "Data bridge action",
                    },
                    "source_app": {"type": "string", "description": "Source application name"},
                    "target_app": {"type": "string", "description": "Target application name"},
                    "source_id": {"type": "string", "description": "Source item ID"},
                    "source_ids": {"type": "array", "items": {"type": "string"}, "description": "Source item IDs"},
                    "data": {"type": "object", "description": "Data to transfer"},
                    "format": {"type": "string", "description": "Data format"},
                    "mapping": {"type": "object", "description": "Field mapping (source_field: target_field)"},
                    "transform_rule": {"type": "object", "description": "Transform rules"},
                    "validation_rules": {"type": "array", "items": {"type": "object"}, "description": "Validation rules"},
                    "sync_direction": {"type": "string", "enum": ["push", "pull", "bidirectional"], "description": "Sync direction"},
                    "schedule_time": {"type": "string", "description": "Schedule time"},
                    "import_path": {"type": "string", "description": "Import file path"},
                    "export_path": {"type": "string", "description": "Export file path"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "preview")
        return {
            "action": "workspace_command",
            "app": "data_bridge",
            "command": action,
            "source_app": kwargs.get("source_app", ""),
            "target_app": kwargs.get("target_app", ""),
            "source_id": kwargs.get("source_id", ""),
            "source_ids": kwargs.get("source_ids", []),
            "data": kwargs.get("data", {}),
            "format": kwargs.get("format", ""),
            "mapping": kwargs.get("mapping", {}),
            "transform_rule": kwargs.get("transform_rule", {}),
            "validation_rules": kwargs.get("validation_rules", []),
            "sync_direction": kwargs.get("sync_direction", "push"),
            "schedule_time": kwargs.get("schedule_time", ""),
            "import_path": kwargs.get("import_path", ""),
            "export_path": kwargs.get("export_path", ""),
        }

    async def _on_hibernate(self) -> None:
        pass


class BatchTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="batch",
            description="Batch operations: create, update, delete, move, tag, export, import, transform, validate, schedule multiple items at once",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create_batch", "update_batch", "delete_batch",
                                 "move_batch", "tag_batch", "export_batch",
                                 "import_batch", "transform_batch", "validate_batch",
                                 "schedule_batch", "undo_batch", "report"],
                        "description": "Batch action",
                    },
                    "app_name": {"type": "string", "description": "Target application name"},
                    "items": {"type": "array", "items": {"type": "object"}, "description": "Items for batch operation"},
                    "item_ids": {"type": "array", "items": {"type": "string"}, "description": "Item IDs for batch operation"},
                    "updates": {"type": "object", "description": "Updates to apply to all items"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags to add/remove"},
                    "target_folder": {"type": "string", "description": "Target folder for move"},
                    "export_format": {"type": "string", "description": "Export format"},
                    "import_path": {"type": "string", "description": "Import file path"},
                    "transform_rule": {"type": "object", "description": "Transform rule"},
                    "schedule_time": {"type": "string", "description": "Schedule time"},
                    "batch_id": {"type": "string", "description": "Batch ID for undo/report"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "report")
        return {
            "action": "workspace_command",
            "app": "batch",
            "command": action,
            "app_name": kwargs.get("app_name", ""),
            "items": kwargs.get("items", []),
            "item_ids": kwargs.get("item_ids", []),
            "updates": kwargs.get("updates", {}),
            "tags": kwargs.get("tags", []),
            "target_folder": kwargs.get("target_folder", ""),
            "export_format": kwargs.get("export_format", ""),
            "import_path": kwargs.get("import_path", ""),
            "transform_rule": kwargs.get("transform_rule", {}),
            "schedule_time": kwargs.get("schedule_time", ""),
            "batch_id": kwargs.get("batch_id", ""),
        }

    async def _on_hibernate(self) -> None:
        pass


class TemplateMgrTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="template_mgr",
            description="Template management: list, create, apply, customize, share, import, export, delete, preview, duplicate, categorize templates",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["list", "create", "apply", "customize", "share",
                                 "import", "export", "delete", "preview",
                                 "duplicate", "category", "favorite"],
                        "description": "Template action",
                    },
                    "template_id": {"type": "string", "description": "Template ID"},
                    "template_name": {"type": "string", "description": "Template name"},
                    "template_type": {"type": "string", "description": "Template type (document, ppt, excel, email, etc.)"},
                    "content": {"type": "string", "description": "Template content"},
                    "variables": {"type": "object", "description": "Template variables"},
                    "category": {"type": "string", "description": "Template category"},
                    "share_with": {"type": "string", "description": "Share with user"},
                    "import_path": {"type": "string", "description": "Import file path"},
                    "export_format": {"type": "string", "description": "Export format"},
                    "target_app": {"type": "string", "description": "Target app to apply template"},
                    "description": {"type": "string", "description": "Template description"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "list")
        return {
            "action": "workspace_command",
            "app": "template_mgr",
            "command": action,
            "template_id": kwargs.get("template_id", ""),
            "template_name": kwargs.get("template_name", ""),
            "template_type": kwargs.get("template_type", ""),
            "content": kwargs.get("content", ""),
            "variables": kwargs.get("variables", {}),
            "category": kwargs.get("category", ""),
            "share_with": kwargs.get("share_with", ""),
            "import_path": kwargs.get("import_path", ""),
            "export_format": kwargs.get("export_format", ""),
            "target_app": kwargs.get("target_app", ""),
            "description": kwargs.get("description", ""),
        }

    async def _on_hibernate(self) -> None:
        pass


class ClipboardTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="clipboard",
            description="Clipboard manager: copy, paste, history, clear, pin items, search, format conversion, multi-copy, templates, sync",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["copy", "paste", "history", "clear", "pin",
                                 "search", "format", "multi_copy", "template",
                                 "sync", "settings", "export"],
                        "description": "Clipboard action",
                    },
                    "content": {"type": "string", "description": "Content to copy"},
                    "item_id": {"type": "string", "description": "Clipboard item ID"},
                    "format_type": {"type": "string", "enum": ["text", "html", "markdown", "json", "csv"], "description": "Format type"},
                    "query": {"type": "string", "description": "Search query"},
                    "items": {"type": "array", "items": {"type": "string"}, "description": "Multiple items for multi_copy"},
                    "limit": {"type": "integer", "description": "Max history items"},
                    "export_format": {"type": "string", "description": "Export format"},
                    "template_name": {"type": "string", "description": "Template name"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "history")
        return {
            "action": "workspace_command",
            "app": "clipboard",
            "command": action,
            "content": kwargs.get("content", ""),
            "item_id": kwargs.get("item_id", ""),
            "format_type": kwargs.get("format_type", "text"),
            "query": kwargs.get("query", ""),
            "items": kwargs.get("items", []),
            "limit": kwargs.get("limit", 50),
            "export_format": kwargs.get("export_format", "json"),
            "template_name": kwargs.get("template_name", ""),
        }

    async def _on_hibernate(self) -> None:
        pass


class QuickActionTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="quick_action",
            description="Quick actions: shortcuts, macros, action chains, schedule actions, favorites, recent actions, custom actions, share, import/export",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["shortcut", "macro", "chain", "schedule",
                                 "favorite", "recent", "custom", "share",
                                 "import", "export", "test", "debug"],
                        "description": "Quick action type",
                    },
                    "action_name": {"type": "string", "description": "Action name"},
                    "action_id": {"type": "string", "description": "Action ID"},
                    "shortcut_key": {"type": "string", "description": "Keyboard shortcut"},
                    "steps": {"type": "array", "items": {"type": "object"}, "description": "Action steps for macro/chain"},
                    "schedule_time": {"type": "string", "description": "Schedule time"},
                    "share_with": {"type": "string", "description": "Share with user"},
                    "import_path": {"type": "string", "description": "Import file path"},
                    "export_format": {"type": "string", "description": "Export format"},
                    "params": {"type": "object", "description": "Action parameters"},
                    "description": {"type": "string", "description": "Action description"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "recent")
        return {
            "action": "workspace_command",
            "app": "quick_action",
            "command": action,
            "action_name": kwargs.get("action_name", ""),
            "action_id": kwargs.get("action_id", ""),
            "shortcut_key": kwargs.get("shortcut_key", ""),
            "steps": kwargs.get("steps", []),
            "schedule_time": kwargs.get("schedule_time", ""),
            "share_with": kwargs.get("share_with", ""),
            "import_path": kwargs.get("import_path", ""),
            "export_format": kwargs.get("export_format", ""),
            "params": kwargs.get("params", {}),
        }

    async def _on_hibernate(self) -> None:
        pass


class GlobalSearchTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="global_search",
            description="Global search across all workspace apps: search all, search by type, recent items, suggestions, filter, index management, scope, navigate",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["search_all", "search_by_type", "recent", "suggestions",
                                 "filter", "index", "reindex", "scope",
                                 "highlight", "navigate", "preview", "stats"],
                        "description": "Global search action",
                    },
                    "query": {"type": "string", "description": "Search query"},
                    "search_types": {"type": "array", "items": {"type": "string"}, "description": "Types to search (document, note, todo, email, etc.)"},
                    "filters": {"type": "object", "description": "Search filters"},
                    "scope": {"type": "string", "description": "Search scope (all, current_app, recent)"},
                    "limit": {"type": "integer", "description": "Max results"},
                    "offset": {"type": "integer", "description": "Result offset for pagination"},
                    "sort_by": {"type": "string", "enum": ["relevance", "date", "name", "type"], "description": "Sort by"},
                    "date_range": {"type": "object", "description": "Date range filter"},
                    "item_id": {"type": "string", "description": "Item ID for navigate/preview"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "search_all")
        query = kwargs.get("query", "")
        if action == "search_all" and query:
            results = []
            try:
                from app.services.todo_service import todo_service
                todos = await todo_service.list_tasks()
                for t in todos:
                    if query.lower() in t["title"].lower():
                        results.append({"type": "todo", "id": t["id"], "title": t["title"]})
            except Exception:
                pass
            try:
                from app.services.notes_service import notes_service
                notes = await notes_service.search_notes(query)
                for n in notes:
                    results.append({"type": "notes", "id": n.id, "title": n.title})
            except Exception:
                pass
            try:
                from app.services.knowledge_service import KnowledgeService
                svc = KnowledgeService()
                entries = await svc.search(query, limit=5)
                for e in entries:
                    results.append({"type": "knowledge", "id": e.entry_id, "title": e.title})
            except Exception:
                pass
            return {"results": results, "total": len(results), "query": query}
        return {
            "action": "workspace_command",
            "app": "global_search",
            "command": action,
            "query": query,
            "search_types": kwargs.get("search_types", []),
            "filters": kwargs.get("filters", {}),
            "scope": kwargs.get("scope", "all"),
            "limit": kwargs.get("limit", 20),
            "offset": kwargs.get("offset", 0),
            "sort_by": kwargs.get("sort_by", "relevance"),
            "date_range": kwargs.get("date_range", {}),
            "item_id": kwargs.get("item_id", ""),
        }

    async def _on_hibernate(self) -> None:
        pass


class BookmarkTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="bookmark",
            description="Bookmark management: add, list, organize, search, tag, export/import, folders, recent, share bookmarks across workspace",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["add", "list", "organize", "search", "tag",
                                 "export", "import", "folder", "recent",
                                 "share", "thumbnail", "sync", "delete"],
                        "description": "Bookmark action",
                    },
                    "bookmark_id": {"type": "string", "description": "Bookmark ID"},
                    "title": {"type": "string", "description": "Bookmark title"},
                    "url": {"type": "string", "description": "Bookmark URL"},
                    "folder": {"type": "string", "description": "Folder name"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags"},
                    "query": {"type": "string", "description": "Search query"},
                    "export_format": {"type": "string", "enum": ["html", "json", "csv"], "description": "Export format"},
                    "import_path": {"type": "string", "description": "Import file path"},
                    "share_with": {"type": "string", "description": "Share with user"},
                    "description": {"type": "string", "description": "Bookmark description"},
                    "icon_url": {"type": "string", "description": "Favicon URL"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "list")
        return {
            "action": "workspace_command",
            "app": "bookmark",
            "command": action,
            "bookmark_id": kwargs.get("bookmark_id", ""),
            "title": kwargs.get("title", ""),
            "url": kwargs.get("url", ""),
            "folder": kwargs.get("folder", ""),
            "tags": kwargs.get("tags", []),
            "query": kwargs.get("query", ""),
            "export_format": kwargs.get("export_format", "html"),
            "import_path": kwargs.get("import_path", ""),
            "share_with": kwargs.get("share_with", ""),
            "description": kwargs.get("description", ""),
        }

    async def _on_hibernate(self) -> None:
        pass


class TagManagerTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="tag_manager",
            description="Tag management across all apps: create, list, rename, merge, delete, search, stats, auto-tag, suggest, hierarchy, color coding, batch tag",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create", "list", "rename", "merge", "delete",
                                 "search", "stats", "auto_tag", "suggest",
                                 "hierarchy", "color", "batch_tag"],
                        "description": "Tag action",
                    },
                    "tag_name": {"type": "string", "description": "Tag name"},
                    "new_name": {"type": "string", "description": "New name for rename"},
                    "source_tag": {"type": "string", "description": "Source tag for merge"},
                    "target_tag": {"type": "string", "description": "Target tag for merge"},
                    "color": {"type": "string", "description": "Tag color"},
                    "parent_tag": {"type": "string", "description": "Parent tag for hierarchy"},
                    "item_type": {"type": "string", "description": "Item type (todo, memo, knowledge, etc.)"},
                    "item_ids": {"type": "array", "items": {"type": "string"}, "description": "Item IDs for batch tag"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags for batch operations"},
                    "query": {"type": "string", "description": "Search query"},
                    "app_name": {"type": "string", "description": "App to search tags in"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "list")
        return {
            "action": "workspace_command",
            "app": "tag_manager",
            "command": action,
            "tag_name": kwargs.get("tag_name", ""),
            "new_name": kwargs.get("new_name", ""),
            "source_tag": kwargs.get("source_tag", ""),
            "target_tag": kwargs.get("target_tag", ""),
            "color": kwargs.get("color", ""),
            "parent_tag": kwargs.get("parent_tag", ""),
            "item_type": kwargs.get("item_type", ""),
            "item_ids": kwargs.get("item_ids", []),
            "tags": kwargs.get("tags", []),
            "query": kwargs.get("query", ""),
            "app_name": kwargs.get("app_name", ""),
        }

    async def _on_hibernate(self) -> None:
        pass


def register_cross_app_tools():
    from app.core.tool.registry import tool_registry
    tools = [
        WorkspaceTool(),
        WorkflowTool(),
        DataBridgeTool(),
        BatchTool(),
        TemplateMgrTool(),
        ClipboardTool(),
        QuickActionTool(),
        GlobalSearchTool(),
        BookmarkTool(),
        TagManagerTool(),
    ]
    registered = []
    for tool in tools:
        try:
            existing = tool_registry.get(tool.name)
            if existing:
                tool_registry.unregister(tool.name)
            tool_registry.register(tool)
            registered.append(tool.name)
        except Exception as e:
            logger.error(f"Failed to register tool {tool.name}: {e}")
    logger.info(f"Registered {len(registered)} cross-app tools: {registered}")
    return registered
