from __future__ import annotations

import logging
from typing import Any, Optional

from app.core.capability.base import (
    CapabilityCallContext,
    CapabilityCategory,
    CapabilityMeta,
    CapabilityPlatform,
    CapabilityProvider,
    CapabilityResult,
    CapabilitySource,
)
from app.core.tool.base import BaseTool, ToolState

logger = logging.getLogger(__name__)

_CATEGORY_MAP: dict[str, CapabilityCategory] = {
    "email": CapabilityCategory.COMMUNICATION,
    "calendar": CapabilityCategory.SCHEDULER,
    "todo": CapabilityCategory.PRODUCTIVITY,
    "knowledge": CapabilityCategory.KNOWLEDGE,
    "memo": CapabilityCategory.PRODUCTIVITY,
    "kanban": CapabilityCategory.PRODUCTIVITY,
    "memory": CapabilityCategory.MEMORY,
    "coordination": CapabilityCategory.COORDINATION,
    "pdf": CapabilityCategory.DOCUMENT,
    "markitdown": CapabilityCategory.DOCUMENT,
    "task_supplement": CapabilityCategory.PRODUCTIVITY,
    "document": CapabilityCategory.DOCUMENT,
    "ppt": CapabilityCategory.DOCUMENT,
    "excel": CapabilityCategory.DOCUMENT,
    "notes": CapabilityCategory.PRODUCTIVITY,
    "mindmap": CapabilityCategory.PRODUCTIVITY,
    "reader": CapabilityCategory.PRODUCTIVITY,
    "code_editor": CapabilityCategory.DEVELOPMENT,
    "image_editor": CapabilityCategory.MEDIA,
    "video_editor": CapabilityCategory.MEDIA,
    "calculator": CapabilityCategory.PRODUCTIVITY,
    "contacts": CapabilityCategory.COMMUNICATION,
    "weather": CapabilityCategory.LIFESTYLE,
    "focus_timer": CapabilityCategory.PRODUCTIVITY,
    "music": CapabilityCategory.MEDIA,
    "screen_recorder": CapabilityCategory.MEDIA,
    "finance": CapabilityCategory.FINANCE,
    "notification": CapabilityCategory.NOTIFICATION,
    "automation": CapabilityCategory.AUTOMATION,
    "sync": CapabilityCategory.INTEGRATION,
    "backup": CapabilityCategory.INTEGRATION,
    "security": CapabilityCategory.SECURITY,
    "device_bridge": CapabilityCategory.INTEGRATION,
    "plugin": CapabilityCategory.INTEGRATION,
    "api_bridge": CapabilityCategory.INTEGRATION,
    "text_process": CapabilityCategory.CONTENT,
    "media_convert": CapabilityCategory.MEDIA,
    "ocr": CapabilityCategory.DOCUMENT,
    "translation": CapabilityCategory.CONTENT,
    "speech": CapabilityCategory.MEDIA,
    "data_analysis": CapabilityCategory.ANALYTICS,
    "chart": CapabilityCategory.ANALYTICS,
    "database": CapabilityCategory.DATABASE,
    "webhook": CapabilityCategory.INTEGRATION,
    "cron": CapabilityCategory.SCHEDULER,
    "workspace": CapabilityCategory.WORKFLOW,
    "workflow": CapabilityCategory.WORKFLOW,
    "data_bridge": CapabilityCategory.WORKFLOW,
    "batch": CapabilityCategory.WORKFLOW,
    "template_mgr": CapabilityCategory.PRODUCTIVITY,
    "clipboard": CapabilityCategory.CLIPBOARD,
    "quick_action": CapabilityCategory.AUTOMATION,
    "global_search": CapabilityCategory.SEARCH,
    "bookmark": CapabilityCategory.PRODUCTIVITY,
    "tag_manager": CapabilityCategory.PRODUCTIVITY,
    "browser": CapabilityCategory.BROWSER,
    "screen_operation": CapabilityCategory.ACCESSIBILITY,
    "file": CapabilityCategory.FILE,
    "scheduler": CapabilityCategory.SCHEDULER,
    "search": CapabilityCategory.SEARCH,
    "shell": CapabilityCategory.PROCESS,
    "ext_pdf": CapabilityCategory.DOCUMENT,
}


def _map_category(tool_name: str) -> CapabilityCategory:
    for prefix, category in _CATEGORY_MAP.items():
        if tool_name.startswith(prefix):
            return category
    return CapabilityCategory.PRODUCTIVITY


_TOOL_IMPORTS: list[tuple[str, str, str]] = [
    ("app.core.tool.internal_tools", "EmailTool", "email"),
    ("app.core.tool.internal_tools", "CalendarTool", "calendar"),
    ("app.core.tool.internal_tools", "TodoTool", "todo"),
    ("app.core.tool.internal_tools", "KnowledgeTool", "knowledge"),
    ("app.core.tool.internal_tools", "MemoTool", "memo"),
    ("app.core.tool.internal_tools", "KanbanTool", "kanban"),
    ("app.core.tool.internal_tools", "MemoryTool", "memory"),
    ("app.core.tool.internal_tools", "CoordinationTool", "coordination"),
    ("app.core.tool.internal_tools", "PdfTool", "pdf"),
    ("app.core.tool.internal_tools", "MarkitdownTool", "markitdown"),
    ("app.core.tool.internal_tools", "TaskSupplementTool", "task_supplement"),
    ("app.core.tool.workspace_tools", "DocumentTool", "document"),
    ("app.core.tool.workspace_tools", "PptTool", "ppt"),
    ("app.core.tool.workspace_tools", "ExcelTool", "excel"),
    ("app.core.tool.workspace_tools", "NotesTool", "notes"),
    ("app.core.tool.workspace_tools", "MindmapTool", "mindmap"),
    ("app.core.tool.workspace_tools", "ReaderTool", "reader"),
    ("app.core.tool.workspace_tools", "CodeEditorTool", "code_editor"),
    ("app.core.tool.workspace_tools", "ImageEditorTool", "image_editor"),
    ("app.core.tool.workspace_tools", "VideoEditorTool", "video_editor"),
    ("app.core.tool.workspace_tools", "CalculatorTool", "calculator"),
    ("app.core.tool.workspace_tools", "ContactsTool", "contacts"),
    ("app.core.tool.workspace_tools", "WeatherTool", "weather"),
    ("app.core.tool.workspace_tools", "FocusTimerTool", "focus_timer"),
    ("app.core.tool.workspace_tools", "MusicTool", "music"),
    ("app.core.tool.workspace_tools", "ScreenRecorderTool", "screen_recorder"),
    ("app.core.tool.workspace_tools", "FinanceTool", "finance"),
    ("app.core.tool.enhanced_tools", "EmailManageTool", "email_manage"),
    ("app.core.tool.enhanced_tools", "CalendarManageTool", "calendar_manage"),
    ("app.core.tool.enhanced_tools", "TodoManageTool", "todo_manage"),
    ("app.core.tool.enhanced_tools", "KnowledgeManageTool", "knowledge_manage"),
    ("app.core.tool.enhanced_tools", "KanbanManageTool", "kanban_manage"),
    ("app.core.tool.enhanced_tools", "MemoManageTool", "memo_manage"),
    ("app.core.tool.enhanced_tools", "MemoryManageTool", "memory_manage"),
    ("app.core.tool.enhanced_tools", "CoordinationManageTool", "coordination_manage"),
    ("app.core.tool.enhanced_tools", "PdfManageTool", "pdf_manage"),
    ("app.core.tool.enhanced_tools", "FileManageTool", "file_manage"),
    ("app.core.tool.enhanced_tools", "BrowserManageTool", "browser_manage"),
    ("app.core.tool.enhanced_tools", "SearchManageTool", "search_manage"),
    ("app.core.tool.cross_app_tools", "WorkspaceTool", "workspace"),
    ("app.core.tool.cross_app_tools", "WorkflowTool", "workflow"),
    ("app.core.tool.cross_app_tools", "DataBridgeTool", "data_bridge"),
    ("app.core.tool.cross_app_tools", "BatchTool", "batch"),
    ("app.core.tool.cross_app_tools", "TemplateMgrTool", "template_mgr"),
    ("app.core.tool.cross_app_tools", "ClipboardTool", "clipboard"),
    ("app.core.tool.cross_app_tools", "QuickActionTool", "quick_action"),
    ("app.core.tool.cross_app_tools", "GlobalSearchTool", "global_search"),
    ("app.core.tool.cross_app_tools", "BookmarkTool", "bookmark"),
    ("app.core.tool.cross_app_tools", "TagManagerTool", "tag_manager"),
    ("app.core.tool.extension_tools", "NotificationTool", "notification"),
    ("app.core.tool.extension_tools", "AutomationTool", "automation"),
    ("app.core.tool.extension_tools", "SyncTool", "sync"),
    ("app.core.tool.extension_tools", "BackupTool", "backup"),
    ("app.core.tool.extension_tools", "SecurityTool", "security"),
    ("app.core.tool.extension_tools", "PluginTool", "plugin"),
    ("app.core.tool.extension_tools", "ApiBridgeTool", "api_bridge"),
    ("app.core.tool.extension_tools", "TextProcessTool", "text_process"),
    ("app.core.tool.extension_tools", "MediaConvertTool", "media_convert"),
    ("app.core.tool.extension_tools", "OcrTool", "ocr"),
    ("app.core.tool.extension_tools", "TranslationTool", "translation"),
    ("app.core.tool.extension_tools", "SpeechTool", "speech"),
    ("app.core.tool.extension_tools", "DataAnalysisTool", "data_analysis"),
    ("app.core.tool.extension_tools", "ChartTool", "chart"),
    ("app.core.tool.extension_tools", "DatabaseTool", "database"),
    ("app.core.tool.extension_tools", "WebhookTool", "webhook"),
    ("app.core.tool.extension_tools", "CronTool", "cron"),
    ("app.core.tools.browser_tool", "BrowserTool", "browser"),
    ("app.core.tools.desktop_tool", "DesktopTool", "screen_operation"),
    ("app.core.tools.file_tool", "FileTool", "file_ext"),
    ("app.core.tools.pdf_tool", "PDFTool", "ext_pdf"),
    ("app.core.tools.scheduler_tool", "SchedulerTool", "scheduler"),
    ("app.core.tools.search_tool", "SearchTool", "search_ext"),
    ("app.core.tools.shell_tool", "ShellTool", "shell"),
]


class InternalProvider(CapabilityProvider):
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}
        self._tool_classes: dict[str, tuple[type, str]] = {}

    @property
    def name(self) -> str:
        return "internal"

    @property
    def source_type(self) -> CapabilitySource:
        return CapabilitySource.INTERNAL

    def _ensure_loaded(self, cap_name: str) -> Optional[BaseTool]:
        if cap_name in self._tools:
            return self._tools[cap_name]
        entry = self._tool_classes.get(cap_name)
        if not entry:
            return None
        cls, _ = entry
        try:
            tool = cls()
            self._tools[cap_name] = tool
            return tool
        except Exception as e:
            logger.error(f"Failed to instantiate tool '{cap_name}': {e}")
            return None

    async def discover(self) -> list[CapabilityMeta]:
        self._tool_classes.clear()
        self._tools.clear()
        metas: list[CapabilityMeta] = []
        for module_path, class_name, cap_name in _TOOL_IMPORTS:
            try:
                import importlib
                module = importlib.import_module(module_path)
                cls = getattr(module, class_name)
                self._tool_classes[cap_name] = (cls, module_path)
                tool = cls()
                self._tools[cap_name] = tool
                meta = CapabilityMeta(
                    name=cap_name,
                    display_name=tool.name,
                    description=tool.description,
                    source_type=CapabilitySource.INTERNAL,
                    category=_map_category(cap_name),
                    platforms=[CapabilityPlatform.BACKEND],
                    parameters=tool.parameters if isinstance(tool.parameters, dict) else {},
                    provider_name=self.name,
                )
                metas.append(meta)
            except Exception as e:
                logger.warning(f"Skip tool {class_name} from {module_path}: {e}")
        return metas

    async def activate(self, capability_name: str) -> None:
        tool = self._ensure_loaded(capability_name)
        if tool and tool.state == ToolState.INACTIVE:
            await tool.activate()

    async def execute(
        self,
        capability_name: str,
        params: dict[str, Any],
        context: CapabilityCallContext,
    ) -> CapabilityResult:
        tool = self._ensure_loaded(capability_name)
        if not tool:
            return CapabilityResult(success=False, error=f"Tool '{capability_name}' not available")
        try:
            if tool.state == ToolState.INACTIVE:
                await tool.activate()
            result = await tool.call(**params)
            return CapabilityResult(success=True, data=result)
        except Exception as e:
            return CapabilityResult(success=False, error=str(e))

    async def deactivate(self, capability_name: str) -> None:
        tool = self._tools.get(capability_name)
        if tool and tool.state in (ToolState.ACTIVE, ToolState.CALLING):
            await tool.hibernate()

    async def health_check(self, capability_name: str) -> bool:
        tool = self._tools.get(capability_name)
        return tool is not None and tool.state in (ToolState.ACTIVE, ToolState.CALLING)

    def get_capability(self, name: str) -> Optional[CapabilityMeta]:
        tool = self._tools.get(name)
        if not tool:
            return None
        return CapabilityMeta(
            name=name,
            display_name=tool.name,
            description=tool.description,
            source_type=CapabilitySource.INTERNAL,
            category=_map_category(name),
            platforms=[CapabilityPlatform.BACKEND],
            parameters=tool.parameters if isinstance(tool.parameters, dict) else {},
            provider_name=self.name,
        )
