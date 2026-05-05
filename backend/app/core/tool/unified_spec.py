from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ToolPlatform(str, Enum):
    ANDROID = "android"
    DESKTOP = "desktop"
    WEB = "web"
    LINUX = "linux"
    MACOS = "macos"
    BACKEND = "backend"


class ToolCategory(str, Enum):
    SYSTEM = "system"
    FILE = "file"
    COMMUNICATION = "communication"
    NETWORK = "network"
    MEDIA = "media"
    HARDWARE = "hardware"
    ACCESSIBILITY = "accessibility"
    AUTOMATION = "automation"
    BROWSER = "browser"
    STORAGE = "storage"
    PROCESS = "process"
    CLIPBOARD = "clipboard"
    WINDOW = "window"
    NOTIFICATION = "notification"
    SEARCH = "search"
    SCHEDULER = "scheduler"
    DOCUMENT = "document"
    KNOWLEDGE = "knowledge"
    MEMORY = "memory"
    COORDINATION = "coordination"
    PRODUCTIVITY = "productivity"
    CREATIVE = "creative"
    LIFESTYLE = "lifestyle"
    WORKFLOW = "workflow"
    INTEGRATION = "integration"
    CONTENT = "content"
    ANALYTICS = "analytics"
    FINANCE = "finance"
    SECURITY = "security"
    DATABASE = "database"


@dataclass
class UnifiedToolSpec:
    name: str
    display_name: str
    description: str
    category: ToolCategory
    platforms: list[ToolPlatform]
    actions: list[str] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)
    required_permissions: list[str] = field(default_factory=list)
    version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "category": self.category.value,
            "platforms": [p.value for p in self.platforms],
            "actions": self.actions,
            "parameters": self.parameters,
            "required_permissions": self.required_permissions,
            "version": self.version,
        }

    def is_available_on(self, platform: ToolPlatform) -> bool:
        return platform in self.platforms

    def to_openai_function(self) -> dict:
        properties: dict[str, Any] = {
            "action": {
                "type": "string",
                "enum": self.actions if self.actions else ["execute"],
                "description": f"Action to perform on {self.name}",
            },
        }
        for param_name, param_schema in self.parameters.items():
            if param_name != "action":
                properties[param_name] = param_schema
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": ["action"],
                },
            },
        }


UNIFIED_TOOL_SPECIFICATIONS: list[UnifiedToolSpec] = [
    UnifiedToolSpec(
        name="screen_operation",
        display_name="屏幕操作",
        description="通过多模态AI分析屏幕截图并执行点击、滑动、输入等操作，支持桌面端和移动端",
        category=ToolCategory.ACCESSIBILITY,
        platforms=[ToolPlatform.ANDROID, ToolPlatform.DESKTOP],
        actions=["click", "double_click", "right_click", "long_press", "swipe",
                 "drag", "hover", "input_text", "key_tap", "key_combo",
                 "scroll_up", "scroll_down", "scroll",
                 "move_mouse", "get_mouse_pos", "get_screen_size",
                 "screenshot", "analyze",
                 "back", "home", "recents",
                 "notifications", "quick_settings", "power_dialog", "lock_screen",
                 "take_screenshot", "open_app", "get_app_list", "wait"],
        parameters={
            "x": {"type": "integer", "description": "X coordinate"},
            "y": {"type": "integer", "description": "Y coordinate"},
            "start_x": {"type": "integer", "description": "Swipe/Drag start X"},
            "start_y": {"type": "integer", "description": "Swipe/Drag start Y"},
            "end_x": {"type": "integer", "description": "Swipe/Drag end X"},
            "end_y": {"type": "integer", "description": "Swipe/Drag end Y"},
            "duration": {"type": "integer", "description": "Duration in ms"},
            "text": {"type": "string", "description": "Text to input"},
            "key": {"type": "string", "description": "Key or key combination"},
            "keys": {"type": "array", "items": {"type": "string"}, "description": "Key combination array"},
            "amount": {"type": "integer", "description": "Scroll amount"},
            "button": {"type": "string", "enum": ["left", "right", "middle"], "description": "Mouse button"},
            "node_id": {"type": "string", "description": "Accessibility node ID"},
            "action_id": {"type": "integer", "description": "Global action ID"},
            "package_name": {"type": "string", "description": "App package name"},
            "instruction": {"type": "string", "description": "Natural language instruction for AI analysis"},
            "wait_ms": {"type": "integer", "description": "Wait duration in milliseconds"},
        },
        required_permissions=[],
    ),
    UnifiedToolSpec(
        name="desktop_file",
        display_name="文件操作",
        description="桌面端文件读写、列表、复制、移动、删除等操作",
        category=ToolCategory.FILE,
        platforms=[ToolPlatform.DESKTOP],
        actions=["read", "write", "list", "delete", "copy", "move", "exists",
                 "mkdir", "stat", "search"],
        parameters={
            "path": {"type": "string", "description": "File or directory path"},
            "content": {"type": "string", "description": "Content to write"},
            "destination": {"type": "string", "description": "Destination path for copy/move"},
            "recursive": {"type": "boolean", "description": "Recursive operation"},
            "pattern": {"type": "string", "description": "Glob pattern for search"},
            "encoding": {"type": "string", "description": "File encoding (default: utf-8)"},
        },
    ),
    UnifiedToolSpec(
        name="desktop_window",
        display_name="窗口管理",
        description="桌面端窗口列表、聚焦、最小化、最大化、关闭等操作",
        category=ToolCategory.WINDOW,
        platforms=[ToolPlatform.DESKTOP],
        actions=["list", "focus", "minimize", "maximize", "close",
                 "get_active", "screenshot", "move", "resize"],
        parameters={
            "window_id": {"type": "string", "description": "Window identifier"},
            "title": {"type": "string", "description": "Window title to find"},
            "x": {"type": "integer", "description": "Window X position"},
            "y": {"type": "integer", "description": "Window Y position"},
            "width": {"type": "integer", "description": "Window width"},
            "height": {"type": "integer", "description": "Window height"},
        },
    ),
    UnifiedToolSpec(
        name="desktop_system",
        display_name="系统信息",
        description="桌面端系统信息查询：CPU、内存、磁盘、网络、环境变量等",
        category=ToolCategory.SYSTEM,
        platforms=[ToolPlatform.DESKTOP],
        actions=["cpu_info", "memory_info", "disk_info", "network_info",
                 "env_info", "os_info", "uptime", "battery_info"],
        parameters={
            "drive": {"type": "string", "description": "Drive letter for disk info (Windows)"},
            "interface": {"type": "string", "description": "Network interface name"},
        },
    ),
    UnifiedToolSpec(
        name="desktop_clipboard",
        display_name="剪贴板",
        description="桌面端剪贴板读写操作",
        category=ToolCategory.CLIPBOARD,
        platforms=[ToolPlatform.DESKTOP],
        actions=["read", "write", "clear", "read_image", "write_image"],
        parameters={
            "text": {"type": "string", "description": "Text to write to clipboard"},
            "image_path": {"type": "string", "description": "Image file path"},
        },
    ),
    UnifiedToolSpec(
        name="desktop_process",
        display_name="进程管理",
        description="桌面端进程列表、启动、终止等操作",
        category=ToolCategory.PROCESS,
        platforms=[ToolPlatform.DESKTOP],
        actions=["list", "kill", "spawn", "get_info", "monitor"],
        parameters={
            "pid": {"type": "integer", "description": "Process ID"},
            "name": {"type": "string", "description": "Process name"},
            "command": {"type": "string", "description": "Command to spawn"},
            "args": {"type": "array", "items": {"type": "string"}, "description": "Command arguments"},
            "signal": {"type": "string", "description": "Signal to send (default: SIGTERM)"},
        },
    ),
    UnifiedToolSpec(
        name="web_browser",
        display_name="浏览器操作",
        description="Web端浏览器标签页、导航、书签等操作",
        category=ToolCategory.BROWSER,
        platforms=[ToolPlatform.WEB],
        actions=["get_url", "navigate", "get_title", "get_cookies",
                 "set_cookie", "get_local_storage", "set_local_storage",
                 "get_session_storage", "set_session_storage",
                 "get_user_agent", "get_viewport", "go_back", "go_forward",
                 "refresh", "get_history"],
        parameters={
            "url": {"type": "string", "description": "URL to navigate to"},
            "key": {"type": "string", "description": "Storage key"},
            "value": {"type": "string", "description": "Storage value"},
            "name": {"type": "string", "description": "Cookie name"},
            "cookie_value": {"type": "string", "description": "Cookie value"},
        },
    ),
    UnifiedToolSpec(
        name="web_storage",
        display_name="Web存储",
        description="Web端IndexedDB、Cache API等存储操作",
        category=ToolCategory.STORAGE,
        platforms=[ToolPlatform.WEB],
        actions=["indexeddb_list_stores", "indexeddb_get", "indexeddb_put",
                 "indexeddb_delete", "cache_list", "cache_get", "cache_put",
                 "cache_delete", "estimate"],
        parameters={
            "store_name": {"type": "string", "description": "IndexedDB store name"},
            "key": {"type": "string", "description": "Storage key"},
            "value": {"type": "string", "description": "Value to store"},
            "cache_name": {"type": "string", "description": "Cache name"},
            "url": {"type": "string", "description": "URL for cache entry"},
        },
    ),
    UnifiedToolSpec(
        name="web_clipboard",
        display_name="Web剪贴板",
        description="Web端剪贴板读写操作（需用户授权）",
        category=ToolCategory.CLIPBOARD,
        platforms=[ToolPlatform.WEB],
        actions=["read_text", "write_text", "read_image", "write_image"],
        parameters={
            "text": {"type": "string", "description": "Text to write"},
            "image_data": {"type": "string", "description": "Base64 image data"},
        },
    ),
    UnifiedToolSpec(
        name="web_notification",
        display_name="Web通知",
        description="Web端浏览器通知操作",
        category=ToolCategory.NOTIFICATION,
        platforms=[ToolPlatform.WEB],
        actions=["request_permission", "send", "get_permission"],
        parameters={
            "title": {"type": "string", "description": "Notification title"},
            "body": {"type": "string", "description": "Notification body"},
            "icon": {"type": "string", "description": "Notification icon URL"},
            "tag": {"type": "string", "description": "Notification tag"},
        },
    ),
    UnifiedToolSpec(
        name="web_media",
        display_name="Web媒体",
        description="Web端摄像头、麦克风、屏幕捕获等媒体操作",
        category=ToolCategory.MEDIA,
        platforms=[ToolPlatform.WEB],
        actions=["get_cameras", "get_microphones", "capture_screenshot",
                 "capture_video", "get_media_devices"],
        parameters={
            "device_id": {"type": "string", "description": "Media device ID"},
            "width": {"type": "integer", "description": "Capture width"},
            "height": {"type": "integer", "description": "Capture height"},
            "duration": {"type": "integer", "description": "Capture duration in seconds"},
        },
    ),
    UnifiedToolSpec(
        name="web_geolocation",
        display_name="Web定位",
        description="Web端地理位置获取",
        category=ToolCategory.HARDWARE,
        platforms=[ToolPlatform.WEB],
        actions=["get_current", "watch", "clear_watch"],
        parameters={
            "enable_high_accuracy": {"type": "boolean", "description": "Enable high accuracy"},
            "timeout": {"type": "integer", "description": "Timeout in ms"},
        },
    ),
    UnifiedToolSpec(
        name="android_audio",
        display_name="音频录制",
        description="Android端音频录制与播放",
        category=ToolCategory.MEDIA,
        platforms=[ToolPlatform.ANDROID],
        actions=["start_record", "stop_record", "play"],
        parameters={
            "duration": {"type": "integer", "description": "Recording duration in ms"},
            "sample_rate": {"type": "integer", "description": "Sample rate"},
            "file_path": {"type": "string", "description": "Audio file path"},
        },
        required_permissions=["RECORD_AUDIO"],
    ),
    UnifiedToolSpec(
        name="android_communication",
        display_name="通讯操作",
        description="Android端电话、短信、联系人操作",
        category=ToolCategory.COMMUNICATION,
        platforms=[ToolPlatform.ANDROID],
        actions=["call", "send_sms", "get_contacts", "search_contacts"],
        parameters={
            "phone_number": {"type": "string", "description": "Phone number"},
            "message": {"type": "string", "description": "SMS message body"},
            "query": {"type": "string", "description": "Search query"},
        },
        required_permissions=["CALL_PHONE", "SEND_SMS", "READ_CONTACTS"],
    ),
    UnifiedToolSpec(
        name="android_network",
        display_name="网络操作",
        description="Android端网络状态、WiFi操作",
        category=ToolCategory.NETWORK,
        platforms=[ToolPlatform.ANDROID],
        actions=["get_status", "get_wifi_info", "scan_wifi", "ping"],
        parameters={
            "host": {"type": "string", "description": "Host to ping"},
            "count": {"type": "integer", "description": "Ping count"},
        },
        required_permissions=["ACCESS_NETWORK_STATE", "ACCESS_WIFI_STATE"],
    ),
    UnifiedToolSpec(
        name="android_hardware",
        display_name="硬件操作",
        description="Android端手电筒、振动等硬件操作",
        category=ToolCategory.HARDWARE,
        platforms=[ToolPlatform.ANDROID],
        actions=["flashlight_on", "flashlight_off", "vibrate", "get_battery"],
        parameters={
            "duration": {"type": "integer", "description": "Vibration duration in ms"},
            "pattern": {"type": "array", "items": {"type": "integer"}, "description": "Vibration pattern"},
        },
    ),
    UnifiedToolSpec(
        name="document",
        display_name="文档编辑",
        description="文档编辑器操作：创建、编辑、格式化、插入元素、导出、摘要、大纲",
        category=ToolCategory.PRODUCTIVITY,
        platforms=[ToolPlatform.WEB, ToolPlatform.DESKTOP],
        actions=["create", "open", "edit", "format_text", "insert_image", "insert_table", "export", "summarize", "outline", "word_count", "find_replace", "comment", "save", "close"],
        parameters={"doc_id": {"type": "string", "description": "Document ID"}, "title": {"type": "string", "description": "Document title"}, "content": {"type": "string", "description": "Document content"}, "format": {"type": "string", "description": "Text format type"}, "export_format": {"type": "string", "description": "Export format"}},
    ),
    UnifiedToolSpec(
        name="ppt",
        display_name="PPT编辑",
        description="PPT编辑器操作：创建、添加/编辑幻灯片、应用主题、添加动画、导出、摘要",
        category=ToolCategory.PRODUCTIVITY,
        platforms=[ToolPlatform.WEB, ToolPlatform.DESKTOP],
        actions=["create", "add_slide", "edit_slide", "delete_slide", "reorder_slides", "apply_theme", "add_animation", "export", "summarize", "add_notes", "insert_image", "duplicate_slide", "add_transition", "save", "close"],
        parameters={"ppt_id": {"type": "string", "description": "PPT file ID"}, "title": {"type": "string", "description": "Presentation or slide title"}, "slide_index": {"type": "integer", "description": "Slide index"}, "layout": {"type": "string", "description": "Slide layout"}, "theme": {"type": "string", "description": "Theme name"}, "export_format": {"type": "string", "description": "Export format"}},
    ),
    UnifiedToolSpec(
        name="excel",
        display_name="电子表格",
        description="电子表格操作：创建、编辑单元格/范围、公式、图表、排序、筛选、数据透视、导出",
        category=ToolCategory.PRODUCTIVITY,
        platforms=[ToolPlatform.WEB, ToolPlatform.DESKTOP],
        actions=["create", "edit_cell", "edit_range", "formula", "create_chart", "sort", "filter", "pivot", "export", "import_csv", "merge_cells", "conditional_format", "save", "close", "auto_fit", "freeze_panes", "data_validation"],
        parameters={"sheet_id": {"type": "string", "description": "Spreadsheet ID"}, "cell": {"type": "string", "description": "Cell reference"}, "value": {"type": "string", "description": "Cell value"}, "range": {"type": "string", "description": "Cell range"}, "formula_expr": {"type": "string", "description": "Formula expression"}, "chart_type": {"type": "string", "description": "Chart type"}, "export_format": {"type": "string", "description": "Export format"}},
    ),
    UnifiedToolSpec(
        name="notes",
        display_name="笔记管理",
        description="笔记管理：创建、编辑、组织、搜索、标签、链接、导出、大纲、模板",
        category=ToolCategory.PRODUCTIVITY,
        platforms=[ToolPlatform.WEB, ToolPlatform.DESKTOP, ToolPlatform.ANDROID],
        actions=["create", "edit", "organize", "search", "tag", "link", "export", "outline", "template", "archive", "pin", "group", "list", "delete", "duplicate"],
        parameters={"note_id": {"type": "string", "description": "Note ID"}, "title": {"type": "string", "description": "Note title"}, "content": {"type": "string", "description": "Note content"}, "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags"}, "query": {"type": "string", "description": "Search query"}, "export_format": {"type": "string", "description": "Export format"}},
    ),
    UnifiedToolSpec(
        name="mindmap",
        display_name="思维导图",
        description="思维导图操作：创建、添加/编辑/删除节点、连接、布局、折叠/展开、导出",
        category=ToolCategory.CREATIVE,
        platforms=[ToolPlatform.WEB, ToolPlatform.DESKTOP],
        actions=["create", "add_node", "edit_node", "delete_node", "connect", "disconnect", "layout", "collapse", "expand", "export", "style", "center", "list", "search"],
        parameters={"map_id": {"type": "string", "description": "Mind map ID"}, "node_id": {"type": "string", "description": "Node ID"}, "parent_id": {"type": "string", "description": "Parent node ID"}, "layout_type": {"type": "string", "description": "Layout type"}, "export_format": {"type": "string", "description": "Export format"}, "topic": {"type": "string", "description": "Central topic"}},
    ),
    UnifiedToolSpec(
        name="reader",
        display_name="阅读器",
        description="阅读器操作：导入文档、书签、注释、高亮、进度跟踪、目录、导出笔记",
        category=ToolCategory.PRODUCTIVITY,
        platforms=[ToolPlatform.WEB, ToolPlatform.DESKTOP],
        actions=["import", "bookmark", "annotate", "highlight", "progress", "toc", "export_notes", "search", "next_page", "prev_page", "jump", "settings", "list_bookmarks", "list_annotations"],
        parameters={"file_path": {"type": "string", "description": "File path to import"}, "page": {"type": "integer", "description": "Page number"}, "text": {"type": "string", "description": "Text for annotation"}, "note": {"type": "string", "description": "Annotation note"}, "export_format": {"type": "string", "description": "Export format"}},
    ),
    UnifiedToolSpec(
        name="code_editor",
        display_name="代码编辑器",
        description="代码编辑器操作：创建、编辑、格式化、检查、运行、保存、模板、代码片段",
        category=ToolCategory.PRODUCTIVITY,
        platforms=[ToolPlatform.WEB, ToolPlatform.DESKTOP],
        actions=["create", "edit", "format", "lint", "run", "save", "template", "snippet", "find_replace", "goto_line", "autocomplete", "diff", "close", "list_files", "open_file"],
        parameters={"file_path": {"type": "string", "description": "File path"}, "content": {"type": "string", "description": "File content"}, "language": {"type": "string", "description": "Programming language"}, "template_name": {"type": "string", "description": "Template name"}, "line": {"type": "integer", "description": "Line number"}},
    ),
    UnifiedToolSpec(
        name="image_editor",
        display_name="图片编辑器",
        description="图片编辑操作：打开、裁剪、调整大小、旋转、翻转、滤镜、标注、压缩、转换",
        category=ToolCategory.CREATIVE,
        platforms=[ToolPlatform.WEB, ToolPlatform.DESKTOP],
        actions=["open", "crop", "resize", "rotate", "flip", "filter", "annotate", "compress", "convert", "export", "undo", "redo", "info", "thumbnail", "watermark", "adjust"],
        parameters={"file_path": {"type": "string", "description": "Image file path"}, "width": {"type": "integer", "description": "Width"}, "height": {"type": "integer", "description": "Height"}, "angle": {"type": "integer", "description": "Rotation angle"}, "filter_name": {"type": "string", "description": "Filter name"}, "quality": {"type": "integer", "description": "Compression quality"}, "output_format": {"type": "string", "description": "Output format"}},
    ),
    UnifiedToolSpec(
        name="video_editor",
        display_name="视频编辑器",
        description="视频编辑操作：导入、裁剪、分割、合并、添加字幕/特效/转场、导出、分析",
        category=ToolCategory.CREATIVE,
        platforms=[ToolPlatform.WEB, ToolPlatform.DESKTOP],
        actions=["import", "trim", "split", "merge", "add_subtitle", "add_effect", "add_transition", "export", "analyze", "thumbnail", "speed", "audio_extract", "info", "add_text", "crop_video", "resize_video"],
        parameters={"file_path": {"type": "string", "description": "Video file path"}, "start_time": {"type": "string", "description": "Start time"}, "end_time": {"type": "string", "description": "End time"}, "export_format": {"type": "string", "description": "Export format"}, "speed_factor": {"type": "number", "description": "Speed factor"}},
    ),
    UnifiedToolSpec(
        name="calculator",
        display_name="计算器",
        description="计算器操作：求值、单位/货币转换、公式、历史、百分比、进制转换、解方程",
        category=ToolCategory.PRODUCTIVITY,
        platforms=[ToolPlatform.WEB, ToolPlatform.DESKTOP, ToolPlatform.ANDROID],
        actions=["evaluate", "convert_unit", "convert_currency", "formula", "history", "percentage", "base_convert", "solve", "graph", "statistics", "clear", "save"],
        parameters={"expression": {"type": "string", "description": "Mathematical expression"}, "value": {"type": "number", "description": "Numeric value"}, "from_unit": {"type": "string", "description": "Source unit"}, "to_unit": {"type": "string", "description": "Target unit"}, "equation": {"type": "string", "description": "Equation to solve"}},
    ),
    UnifiedToolSpec(
        name="contacts",
        display_name="通讯录",
        description="通讯录管理：列表、搜索、添加、编辑、删除、分组、导入导出、合并",
        category=ToolCategory.COMMUNICATION,
        platforms=[ToolPlatform.WEB, ToolPlatform.DESKTOP, ToolPlatform.ANDROID],
        actions=["list", "search", "add", "edit", "delete", "group", "import", "export", "merge", "favorite", "tag", "detail", "add_to_group", "remove_from_group"],
        parameters={"contact_id": {"type": "string", "description": "Contact ID"}, "name": {"type": "string", "description": "Contact name"}, "email": {"type": "string", "description": "Contact email"}, "phone": {"type": "string", "description": "Contact phone"}, "query": {"type": "string", "description": "Search query"}, "group_name": {"type": "string", "description": "Group name"}},
    ),
    UnifiedToolSpec(
        name="weather",
        display_name="天气",
        description="天气操作：搜索城市、当前天气、预报、空气质量、预警、逐小时、紫外线",
        category=ToolCategory.LIFESTYLE,
        platforms=[ToolPlatform.WEB, ToolPlatform.DESKTOP, ToolPlatform.ANDROID],
        actions=["search_city", "current", "forecast", "air_quality", "alert", "hourly", "uv_index", "sunrise", "moon_phase", "compare", "history", "radar"],
        parameters={"city": {"type": "string", "description": "City name"}, "latitude": {"type": "number", "description": "Latitude"}, "longitude": {"type": "number", "description": "Longitude"}, "forecast_days": {"type": "integer", "description": "Number of forecast days"}},
    ),
    UnifiedToolSpec(
        name="focus_timer",
        display_name="专注计时",
        description="专注计时操作：开始/暂停/停止、统计、设置、休息、历史、预设、每日报告",
        category=ToolCategory.LIFESTYLE,
        platforms=[ToolPlatform.WEB, ToolPlatform.DESKTOP, ToolPlatform.ANDROID],
        actions=["start", "pause", "stop", "stats", "settings", "break", "history", "preset", "daily_report", "streak", "goal", "reminder"],
        parameters={"duration_minutes": {"type": "integer", "description": "Focus duration"}, "task_name": {"type": "string", "description": "Task name"}, "break_minutes": {"type": "integer", "description": "Break duration"}, "preset_name": {"type": "string", "description": "Preset name"}},
    ),
    UnifiedToolSpec(
        name="music",
        display_name="音乐播放",
        description="音乐播放器操作：播放/暂停、上下曲、播放列表、搜索、音量、歌词",
        category=ToolCategory.LIFESTYLE,
        platforms=[ToolPlatform.WEB, ToolPlatform.DESKTOP, ToolPlatform.ANDROID],
        actions=["play", "pause", "next", "prev", "playlist", "search", "volume", "lyrics", "favorite", "queue", "shuffle", "repeat", "create_playlist", "add_to_playlist", "remove_from_playlist", "info"],
        parameters={"song_id": {"type": "string", "description": "Song ID"}, "song_name": {"type": "string", "description": "Song name"}, "artist": {"type": "string", "description": "Artist name"}, "playlist_id": {"type": "string", "description": "Playlist ID"}, "volume_level": {"type": "integer", "description": "Volume level (0-100)"}},
    ),
    UnifiedToolSpec(
        name="screen_recorder",
        display_name="屏幕录制",
        description="屏幕录制操作：开始/停止/暂停、截图、录制列表、裁剪、转码、AI分析、OCR、分享、设置",
        category=ToolCategory.CREATIVE,
        platforms=[ToolPlatform.WEB, ToolPlatform.DESKTOP, ToolPlatform.ANDROID],
        actions=["start", "stop", "pause", "resume", "screenshot", "list_recordings", "trim", "settings", "schedule", "annotate", "convert", "share", "delete", "analyze", "generate_thumbnail", "extract_text", "mix_narration", "generate_narration"],
        parameters={"recording_id": {"type": "string", "description": "Recording ID"}, "output_format": {"type": "string", "description": "Output format"}, "quality": {"type": "string", "description": "Recording quality"}, "fps": {"type": "integer", "description": "Frames per second"}, "audio_enabled": {"type": "boolean", "description": "Enable audio"}, "analyze_action": {"type": "string", "description": "AI analysis action"}, "start_time": {"type": "string", "description": "Trim start time"}, "end_time": {"type": "string", "description": "Trim end time"}, "region": {"type": "string", "description": "Screen region"}, "voice": {"type": "string", "description": "TTS voice"}, "annotation_text": {"type": "string", "description": "Annotation or narration text"}},
    ),
    UnifiedToolSpec(
        name="finance",
        display_name="财务记账",
        description="财务记账操作：记录交易、分类、预算、报告、统计、导出",
        category=ToolCategory.FINANCE,
        platforms=[ToolPlatform.WEB, ToolPlatform.DESKTOP, ToolPlatform.ANDROID],
        actions=["record", "list", "categorize", "budget", "report", "statistics", "export", "import", "delete", "summary", "trend", "category_list"],
        parameters={"amount": {"type": "number", "description": "Transaction amount"}, "type": {"type": "string", "description": "Transaction type"}, "category": {"type": "string", "description": "Transaction category"}, "description": {"type": "string", "description": "Transaction description"}, "date": {"type": "string", "description": "Transaction date"}, "export_format": {"type": "string", "description": "Export format"}},
    ),
    UnifiedToolSpec(
        name="workspace",
        display_name="工作台管理",
        description="工作台管理：状态、打开/关闭/切换应用、布局、标签页、最近、全屏、分屏",
        category=ToolCategory.WORKFLOW,
        platforms=[ToolPlatform.WEB, ToolPlatform.DESKTOP],
        actions=["status", "open_app", "close_app", "switch_app", "layout", "tabs", "recent", "pin", "fullscreen", "split_view", "settings", "shortcuts", "resize", "move", "minimize", "maximize"],
        parameters={"app_name": {"type": "string", "description": "Application name"}, "layout_type": {"type": "string", "description": "Layout type"}, "position": {"type": "string", "description": "Position for split view"}},
    ),
    UnifiedToolSpec(
        name="workflow",
        display_name="工作流",
        description="工作流编排：创建、运行、暂停、恢复、步骤、分支、日志、模板、条件、循环、并行",
        category=ToolCategory.WORKFLOW,
        platforms=[ToolPlatform.BACKEND],
        actions=["create", "run", "pause", "resume", "step", "branch", "log", "template", "schedule", "condition", "loop", "parallel", "list", "delete", "status", "cancel"],
        parameters={"workflow_id": {"type": "string", "description": "Workflow ID"}, "name": {"type": "string", "description": "Workflow name"}, "steps": {"type": "array", "items": {"type": "object"}, "description": "Workflow steps"}, "template_name": {"type": "string", "description": "Template name"}, "variables": {"type": "object", "description": "Workflow variables"}},
    ),
    UnifiedToolSpec(
        name="data_bridge",
        display_name="数据桥接",
        description="应用间数据传输：复制到其他应用、导出为格式、导入、转换、同步、变换、验证",
        category=ToolCategory.WORKFLOW,
        platforms=[ToolPlatform.BACKEND],
        actions=["copy_to", "export_as", "import_from", "convert", "sync", "transform", "validate", "map_fields", "preview", "schedule", "history", "rollback"],
        parameters={"source_app": {"type": "string", "description": "Source application"}, "target_app": {"type": "string", "description": "Target application"}, "data": {"type": "object", "description": "Data to transfer"}, "mapping": {"type": "object", "description": "Field mapping"}, "sync_direction": {"type": "string", "description": "Sync direction"}},
    ),
    UnifiedToolSpec(
        name="batch",
        display_name="批量操作",
        description="批量操作：批量创建、更新、删除、移动、标签、导出、导入、变换、验证",
        category=ToolCategory.WORKFLOW,
        platforms=[ToolPlatform.BACKEND],
        actions=["create_batch", "update_batch", "delete_batch", "move_batch", "tag_batch", "export_batch", "import_batch", "transform_batch", "validate_batch", "schedule_batch", "undo_batch", "report"],
        parameters={"app_name": {"type": "string", "description": "Target application"}, "items": {"type": "array", "items": {"type": "object"}, "description": "Items"}, "item_ids": {"type": "array", "items": {"type": "string"}, "description": "Item IDs"}, "updates": {"type": "object", "description": "Updates to apply"}},
    ),
    UnifiedToolSpec(
        name="global_search",
        display_name="全局搜索",
        description="跨所有工作台应用的全局搜索：搜索全部、按类型搜索、最近、建议、筛选",
        category=ToolCategory.SEARCH,
        platforms=[ToolPlatform.WEB, ToolPlatform.DESKTOP],
        actions=["search_all", "search_by_type", "recent", "suggestions", "filter", "index", "reindex", "scope", "highlight", "navigate", "preview", "stats"],
        parameters={"query": {"type": "string", "description": "Search query"}, "search_types": {"type": "array", "items": {"type": "string"}, "description": "Types to search"}, "scope": {"type": "string", "description": "Search scope"}, "limit": {"type": "integer", "description": "Max results"}},
    ),
    UnifiedToolSpec(
        name="text_process",
        display_name="文本处理",
        description="文本处理：摘要、翻译、改写、提取、比较、计数、格式化、清洗、分词、情感分析",
        category=ToolCategory.CONTENT,
        platforms=[ToolPlatform.BACKEND],
        actions=["summarize", "translate", "rewrite", "extract", "compare", "count", "format", "clean", "tokenize", "sentiment", "keywords", "readability"],
        parameters={"text": {"type": "string", "description": "Input text"}, "target_language": {"type": "string", "description": "Target language"}, "rewrite_style": {"type": "string", "description": "Rewrite style"}, "extract_type": {"type": "string", "description": "Extraction type"}, "format_type": {"type": "string", "description": "Format type"}},
    ),
    UnifiedToolSpec(
        name="data_analysis",
        display_name="数据分析",
        description="数据分析：统计、趋势、相关性、异常检测、预测、可视化、比较、聚类",
        category=ToolCategory.ANALYTICS,
        platforms=[ToolPlatform.BACKEND],
        actions=["stats", "trend", "correlation", "outlier", "forecast", "visualize", "compare", "segment", "aggregate", "pivot", "regression", "cluster"],
        parameters={"data": {"type": "array", "items": {"type": "object"}, "description": "Data array"}, "columns": {"type": "array", "items": {"type": "string"}, "description": "Column names"}, "target_column": {"type": "string", "description": "Target column"}, "chart_type": {"type": "string", "description": "Chart type"}},
    ),
    UnifiedToolSpec(
        name="automation",
        display_name="自动化规则",
        description="自动化规则：创建、列表、启用、禁用、触发、日志、模板、条件、动作、定时",
        category=ToolCategory.AUTOMATION,
        platforms=[ToolPlatform.BACKEND],
        actions=["create", "list", "enable", "disable", "trigger", "log", "template", "condition", "action_rule", "schedule", "test", "import"],
        parameters={"rule_name": {"type": "string", "description": "Rule name"}, "trigger_type": {"type": "string", "description": "Trigger type"}, "conditions": {"type": "array", "items": {"type": "object"}, "description": "Conditions"}, "actions": {"type": "array", "items": {"type": "object"}, "description": "Actions to execute"}},
    ),
    UnifiedToolSpec(
        name="notification",
        display_name="通知管理",
        description="通知管理：列表、消除、暂停、筛选、优先级、分组、设置、定时、模板",
        category=ToolCategory.NOTIFICATION,
        platforms=[ToolPlatform.WEB, ToolPlatform.DESKTOP, ToolPlatform.ANDROID],
        actions=["list", "dismiss", "snooze", "filter", "priority", "group", "settings", "schedule", "template", "batch", "archive", "stats"],
        parameters={"notification_id": {"type": "string", "description": "Notification ID"}, "snooze_minutes": {"type": "integer", "description": "Snooze duration"}, "priority_level": {"type": "string", "description": "Priority level"}, "filter_by": {"type": "object", "description": "Filter criteria"}},
    ),
    UnifiedToolSpec(
        name="backup",
        display_name="备份恢复",
        description="备份和恢复：创建备份、恢复、列表、定时、验证、清理、导出、导入",
        category=ToolCategory.INTEGRATION,
        platforms=[ToolPlatform.BACKEND],
        actions=["create", "restore", "list", "schedule", "verify", "cleanup", "export", "import", "incremental", "differential", "encrypt", "compare"],
        parameters={"backup_id": {"type": "string", "description": "Backup ID"}, "backup_name": {"type": "string", "description": "Backup name"}, "data_types": {"type": "array", "items": {"type": "string"}, "description": "Data types to include"}, "password": {"type": "string", "description": "Encryption password"}},
    ),
    UnifiedToolSpec(
        name="security",
        display_name="安全管理",
        description="安全操作：权限、审计、加密/解密、保险库、清理、检查、报告、策略",
        category=ToolCategory.SECURITY,
        platforms=[ToolPlatform.BACKEND],
        actions=["permissions", "audit", "encrypt", "decrypt", "vault", "sanitize", "check", "report", "policy", "session", "token", "key_manage"],
        parameters={"resource_type": {"type": "string", "description": "Resource type"}, "resource_id": {"type": "string", "description": "Resource ID"}, "data": {"type": "string", "description": "Data to encrypt/decrypt"}, "password": {"type": "string", "description": "Password"}, "permission_level": {"type": "string", "description": "Permission level"}},
    ),
]


class UnifiedToolRegistry:
    _instance: Optional[UnifiedToolRegistry] = None
    _specs: dict[str, UnifiedToolSpec] = {}

    def __new__(cls) -> UnifiedToolRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._specs = {spec.name: spec for spec in UNIFIED_TOOL_SPECIFICATIONS}
        return cls._instance

    def get_spec(self, name: str) -> Optional[UnifiedToolSpec]:
        return self._specs.get(name)

    def get_specs_by_platform(self, platform: ToolPlatform) -> list[UnifiedToolSpec]:
        return [s for s in self._specs.values() if s.is_available_on(platform)]

    def get_specs_by_category(self, category: ToolCategory) -> list[UnifiedToolSpec]:
        return [s for s in self._specs.values() if s.category == category]

    def get_all_specs(self) -> list[UnifiedToolSpec]:
        return list(self._specs.values())

    def get_platform_summary(self) -> dict[str, Any]:
        summary = {}
        for platform in ToolPlatform:
            specs = self.get_specs_by_platform(platform)
            summary[platform.value] = {
                "tool_count": len(specs),
                "categories": list(set(s.category.value for s in specs)),
                "tools": [s.name for s in specs],
            }
        return summary

    def register_spec(self, spec: UnifiedToolSpec) -> None:
        self._specs[spec.name] = spec

    def unregister_spec(self, name: str) -> None:
        self._specs.pop(name, None)


unified_tool_registry = UnifiedToolRegistry()
