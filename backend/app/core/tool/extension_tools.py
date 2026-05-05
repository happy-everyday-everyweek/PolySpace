import logging
from typing import Any

from app.core.tool.base import BaseTool

logger = logging.getLogger(__name__)


class NotificationTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="notification",
            description="Notification management: list, dismiss, snooze, filter, priority, group, settings, schedule, template, batch, archive, stats",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["list", "dismiss", "snooze", "filter", "priority",
                                 "group", "settings", "schedule", "template",
                                 "batch", "archive", "stats"],
                        "description": "Notification action",
                    },
                    "notification_id": {"type": "string", "description": "Notification ID"},
                    "notification_ids": {"type": "array", "items": {"type": "string"}, "description": "Notification IDs for batch"},
                    "snooze_minutes": {"type": "integer", "description": "Snooze duration in minutes"},
                    "filter_by": {"type": "object", "description": "Filter criteria"},
                    "priority_level": {"type": "string", "enum": ["urgent", "high", "medium", "low"], "description": "Priority level"},
                    "group_name": {"type": "string", "description": "Group name"},
                    "schedule_time": {"type": "string", "description": "Schedule time (ISO format)"},
                    "template_name": {"type": "string", "description": "Template name"},
                    "title": {"type": "string", "description": "Notification title"},
                    "body": {"type": "string", "description": "Notification body"},
                    "category": {"type": "string", "description": "Notification category"},
                    "unread_only": {"type": "boolean", "description": "Only unread notifications"},
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
            if action in ("list", "filter", "stats"):
                from app.services.coordination_service import get_coordination_service
                coord = get_coordination_service()
                if action == "list":
                    notifs = coord.get_notifications(
                        unread_only=kwargs.get("unread_only", False),
                        limit=kwargs.get("limit", 50),
                    )
                    return {"notifications": notifs}
                elif action == "stats":
                    return {"total": 0, "unread": 0, "by_category": {}}
            return {
                "action": "workspace_command",
                "app": "notification",
                "command": action,
                "notification_id": kwargs.get("notification_id", ""),
                "notification_ids": kwargs.get("notification_ids", []),
                "snooze_minutes": kwargs.get("snooze_minutes", 15),
                "filter_by": kwargs.get("filter_by", {}),
                "priority_level": kwargs.get("priority_level", "medium"),
                "group_name": kwargs.get("group_name", ""),
                "schedule_time": kwargs.get("schedule_time", ""),
                "template_name": kwargs.get("template_name", ""),
                "title": kwargs.get("title", ""),
                "body": kwargs.get("body", ""),
                "category": kwargs.get("category", ""),
            }
        except Exception as e:
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        pass


class AutomationTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="automation",
            description="Automation rules: create, list, enable, disable, trigger, log, template, condition, action, schedule, test, import automation rules",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create", "list", "enable", "disable", "trigger",
                                 "log", "template", "condition", "action_rule",
                                 "schedule", "test", "import"],
                        "description": "Automation action",
                    },
                    "rule_id": {"type": "string", "description": "Rule ID"},
                    "rule_name": {"type": "string", "description": "Rule name"},
                    "description": {"type": "string", "description": "Rule description"},
                    "trigger_type": {"type": "string", "enum": ["event", "schedule", "condition", "manual"], "description": "Trigger type"},
                    "trigger_config": {"type": "object", "description": "Trigger configuration"},
                    "conditions": {"type": "array", "items": {"type": "object"}, "description": "Conditions"},
                    "actions": {"type": "array", "items": {"type": "object"}, "description": "Actions to execute"},
                    "schedule_time": {"type": "string", "description": "Schedule time"},
                    "template_name": {"type": "string", "description": "Template name"},
                    "import_path": {"type": "string", "description": "Import file path"},
                    "enabled": {"type": "boolean", "description": "Enable/disable rule"},
                    "test_params": {"type": "object", "description": "Test parameters"},
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
            "app": "automation",
            "command": action,
            "rule_id": kwargs.get("rule_id", ""),
            "rule_name": kwargs.get("rule_name", ""),
            "description": kwargs.get("description", ""),
            "trigger_type": kwargs.get("trigger_type", "event"),
            "trigger_config": kwargs.get("trigger_config", {}),
            "conditions": kwargs.get("conditions", []),
            "actions": kwargs.get("actions", []),
            "schedule_time": kwargs.get("schedule_time", ""),
            "template_name": kwargs.get("template_name", ""),
            "import_path": kwargs.get("import_path", ""),
            "enabled": kwargs.get("enabled", True),
            "test_params": kwargs.get("test_params", {}),
        }

    async def _on_hibernate(self) -> None:
        pass


class SyncTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="sync",
            description="Sync management: status, sync now, conflict resolution, resolve, history, schedule, settings, pause, resume, force, verify, cleanup",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["status", "sync_now", "conflict", "resolve",
                                 "history", "schedule", "settings", "pause",
                                 "resume", "force", "verify", "cleanup"],
                        "description": "Sync action",
                    },
                    "sync_id": {"type": "string", "description": "Sync ID"},
                    "source": {"type": "string", "description": "Sync source"},
                    "target": {"type": "string", "description": "Sync target"},
                    "conflict_id": {"type": "string", "description": "Conflict ID"},
                    "resolution": {"type": "string", "enum": ["source_wins", "target_wins", "merge", "manual"], "description": "Conflict resolution strategy"},
                    "schedule_time": {"type": "string", "description": "Schedule time"},
                    "sync_type": {"type": "string", "enum": ["full", "incremental", "delta"], "description": "Sync type"},
                    "data_types": {"type": "array", "items": {"type": "string"}, "description": "Data types to sync"},
                    "limit": {"type": "integer", "description": "Max history items"},
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
            "app": "sync",
            "command": action,
            "sync_id": kwargs.get("sync_id", ""),
            "source": kwargs.get("source", ""),
            "target": kwargs.get("target", ""),
            "conflict_id": kwargs.get("conflict_id", ""),
            "resolution": kwargs.get("resolution", "merge"),
            "schedule_time": kwargs.get("schedule_time", ""),
            "sync_type": kwargs.get("sync_type", "incremental"),
            "data_types": kwargs.get("data_types", []),
            "limit": kwargs.get("limit", 50),
        }

    async def _on_hibernate(self) -> None:
        pass


class BackupTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="backup",
            description="Backup and restore: create backup, restore, list backups, schedule, verify, cleanup, export, import, incremental, differential, encrypt, compare",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create", "restore", "list", "schedule", "verify",
                                 "cleanup", "export", "import", "incremental",
                                 "differential", "encrypt", "compare"],
                        "description": "Backup action",
                    },
                    "backup_id": {"type": "string", "description": "Backup ID"},
                    "backup_name": {"type": "string", "description": "Backup name"},
                    "description": {"type": "string", "description": "Backup description"},
                    "data_types": {"type": "array", "items": {"type": "string"}, "description": "Data types to include"},
                    "restore_point": {"type": "string", "description": "Restore point (ISO timestamp)"},
                    "schedule_time": {"type": "string", "description": "Schedule time"},
                    "password": {"type": "string", "description": "Encryption password"},
                    "export_path": {"type": "string", "description": "Export path"},
                    "import_path": {"type": "string", "description": "Import path"},
                    "compare_with": {"type": "string", "description": "Backup ID to compare with"},
                    "retention_days": {"type": "integer", "description": "Retention period in days"},
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
            "app": "backup",
            "command": action,
            "backup_id": kwargs.get("backup_id", ""),
            "backup_name": kwargs.get("backup_name", ""),
            "description": kwargs.get("description", ""),
            "data_types": kwargs.get("data_types", []),
            "restore_point": kwargs.get("restore_point", ""),
            "schedule_time": kwargs.get("schedule_time", ""),
            "password": kwargs.get("password", ""),
            "export_path": kwargs.get("export_path", ""),
            "import_path": kwargs.get("import_path", ""),
            "compare_with": kwargs.get("compare_with", ""),
            "retention_days": kwargs.get("retention_days", 30),
        }

    async def _on_hibernate(self) -> None:
        pass


class SecurityTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="security",
            description="Security operations: permissions, audit, encrypt/decrypt, vault, sanitize, check, report, policy, session, token management",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["permissions", "audit", "encrypt", "decrypt",
                                 "vault", "sanitize", "check", "report",
                                 "policy", "session", "token", "key_manage"],
                        "description": "Security action",
                    },
                    "resource_type": {"type": "string", "description": "Resource type"},
                    "resource_id": {"type": "string", "description": "Resource ID"},
                    "data": {"type": "string", "description": "Data to encrypt/decrypt"},
                    "password": {"type": "string", "description": "Password for vault/encrypt"},
                    "vault_name": {"type": "string", "description": "Vault name"},
                    "key_name": {"type": "string", "description": "Key name"},
                    "permission_level": {"type": "string", "enum": ["read", "write", "admin", "owner"], "description": "Permission level"},
                    "user_id": {"type": "string", "description": "User ID"},
                    "policy_name": {"type": "string", "description": "Policy name"},
                    "policy_rules": {"type": "object", "description": "Policy rules"},
                    "session_id": {"type": "string", "description": "Session ID"},
                    "token_type": {"type": "string", "description": "Token type"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "check")
        return {
            "action": "workspace_command",
            "app": "security",
            "command": action,
            "resource_type": kwargs.get("resource_type", ""),
            "resource_id": kwargs.get("resource_id", ""),
            "data": kwargs.get("data", ""),
            "password": kwargs.get("password", ""),
            "vault_name": kwargs.get("vault_name", ""),
            "key_name": kwargs.get("key_name", ""),
            "permission_level": kwargs.get("permission_level", "read"),
            "user_id": kwargs.get("user_id", ""),
            "policy_name": kwargs.get("policy_name", ""),
            "policy_rules": kwargs.get("policy_rules", {}),
            "session_id": kwargs.get("session_id", ""),
            "token_type": kwargs.get("token_type", ""),
        }

    async def _on_hibernate(self) -> None:
        pass


class DeviceBridgeTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="device_bridge",
            description="Device bridge management: list, connect, disconnect, capability, route, status, ping, config, update, group, share, debug devices",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["list", "connect", "disconnect", "capability",
                                 "route", "status", "ping", "config",
                                 "update", "group", "share", "debug"],
                        "description": "Device bridge action",
                    },
                    "device_id": {"type": "string", "description": "Device ID"},
                    "device_name": {"type": "string", "description": "Device name"},
                    "platform": {"type": "string", "description": "Device platform"},
                    "capability_name": {"type": "string", "description": "Capability name"},
                    "tool_name": {"type": "string", "description": "Tool name for routing"},
                    "action_name": {"type": "string", "description": "Action name for routing"},
                    "config_key": {"type": "string", "description": "Configuration key"},
                    "config_value": {"type": "string", "description": "Configuration value"},
                    "group_name": {"type": "string", "description": "Device group name"},
                    "share_with": {"type": "string", "description": "Share with user"},
                    "debug_level": {"type": "string", "enum": ["info", "debug", "trace"], "description": "Debug level"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "list")
        try:
            from app.core.connector.device_manager import device_manager
            if action == "list":
                devices = device_manager.list_devices()
                return {"devices": [{"device_id": d.device_id, "name": d.device_name, "platform": d.platform.value, "status": d.status.value} for d in devices]}
            elif action == "status":
                device_id = kwargs.get("device_id", "")
                device = device_manager.get_device(device_id)
                if device:
                    return {"device_id": device.device_id, "name": device.device_name, "status": device.status.value, "capabilities": len(device.capabilities)}
                return {"error": "Device not found"}
            elif action == "ping":
                device_id = kwargs.get("device_id", "")
                device = device_manager.get_device(device_id)
                if device:
                    return {"device_id": device_id, "online": device.status.value == "online"}
                return {"error": "Device not found"}
            else:
                return {
                    "action": "workspace_command",
                    "app": "device_bridge",
                    "command": action,
                    "device_id": kwargs.get("device_id", ""),
                    "device_name": kwargs.get("device_name", ""),
                    "platform": kwargs.get("platform", ""),
                    "capability_name": kwargs.get("capability_name", ""),
                    "tool_name": kwargs.get("tool_name", ""),
                    "action_name": kwargs.get("action_name", ""),
                    "config_key": kwargs.get("config_key", ""),
                    "config_value": kwargs.get("config_value", ""),
                    "group_name": kwargs.get("group_name", ""),
                    "share_with": kwargs.get("share_with", ""),
                    "debug_level": kwargs.get("debug_level", "info"),
                }
        except Exception as e:
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        pass


class PluginTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="plugin",
            description="Plugin management: list, install, uninstall, enable, disable, configure, update, search, dependency, settings, log, marketplace",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["list", "install", "uninstall", "enable", "disable",
                                 "configure", "update", "search", "dependency",
                                 "settings", "log", "marketplace"],
                        "description": "Plugin action",
                    },
                    "plugin_id": {"type": "string", "description": "Plugin ID"},
                    "plugin_name": {"type": "string", "description": "Plugin name"},
                    "version": {"type": "string", "description": "Plugin version"},
                    "source": {"type": "string", "description": "Install source (url, path, marketplace)"},
                    "config": {"type": "object", "description": "Plugin configuration"},
                    "query": {"type": "string", "description": "Search query"},
                    "category": {"type": "string", "description": "Plugin category"},
                    "enabled": {"type": "boolean", "description": "Enable/disable"},
                    "auto_update": {"type": "boolean", "description": "Enable auto-update"},
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
            "app": "plugin",
            "command": action,
            "plugin_id": kwargs.get("plugin_id", ""),
            "plugin_name": kwargs.get("plugin_name", ""),
            "version": kwargs.get("version", ""),
            "source": kwargs.get("source", ""),
            "config": kwargs.get("config", {}),
            "query": kwargs.get("query", ""),
            "category": kwargs.get("category", ""),
            "enabled": kwargs.get("enabled", True),
            "auto_update": kwargs.get("auto_update", False),
        }

    async def _on_hibernate(self) -> None:
        pass


class ApiBridgeTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="api_bridge",
            description="External API bridge: call external APIs, configure endpoints, test, auth, cache, rate limit, transform, validate, log, retry, batch, schedule",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["call", "configure", "test", "auth", "cache",
                                 "rate_limit", "transform", "validate", "log",
                                 "retry", "batch", "schedule"],
                        "description": "API bridge action",
                    },
                    "endpoint_name": {"type": "string", "description": "Endpoint name"},
                    "url": {"type": "string", "description": "API URL"},
                    "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"], "description": "HTTP method"},
                    "headers": {"type": "object", "description": "Request headers"},
                    "params": {"type": "object", "description": "Query parameters"},
                    "body": {"type": "object", "description": "Request body"},
                    "auth_type": {"type": "string", "enum": ["none", "api_key", "bearer", "oauth2", "basic"], "description": "Auth type"},
                    "auth_config": {"type": "object", "description": "Auth configuration"},
                    "cache_ttl": {"type": "integer", "description": "Cache TTL in seconds"},
                    "rate_limit_rpm": {"type": "integer", "description": "Rate limit requests per minute"},
                    "transform_rule": {"type": "object", "description": "Response transform rule"},
                    "validation_schema": {"type": "object", "description": "Response validation schema"},
                    "timeout_seconds": {"type": "integer", "description": "Request timeout"},
                    "batch_requests": {"type": "array", "items": {"type": "object"}, "description": "Batch API requests"},
                    "schedule_time": {"type": "string", "description": "Schedule time"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "configure")
        return {
            "action": "workspace_command",
            "app": "api_bridge",
            "command": action,
            "endpoint_name": kwargs.get("endpoint_name", ""),
            "url": kwargs.get("url", ""),
            "method": kwargs.get("method", "GET"),
            "headers": kwargs.get("headers", {}),
            "params": kwargs.get("params", {}),
            "body": kwargs.get("body", {}),
            "auth_type": kwargs.get("auth_type", "none"),
            "auth_config": kwargs.get("auth_config", {}),
            "cache_ttl": kwargs.get("cache_ttl", 300),
            "rate_limit_rpm": kwargs.get("rate_limit_rpm", 60),
            "transform_rule": kwargs.get("transform_rule", {}),
            "validation_schema": kwargs.get("validation_schema", {}),
            "timeout_seconds": kwargs.get("timeout_seconds", 30),
            "batch_requests": kwargs.get("batch_requests", []),
            "schedule_time": kwargs.get("schedule_time", ""),
        }

    async def _on_hibernate(self) -> None:
        pass


class TextProcessTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="text_process",
            description="Text processing: summarize, translate, rewrite, extract, compare, count, format, clean, tokenize, sentiment, keywords, readability",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["summarize", "translate", "rewrite", "extract",
                                 "compare", "count", "format", "clean",
                                 "tokenize", "sentiment", "keywords", "readability"],
                        "description": "Text process action",
                    },
                    "text": {"type": "string", "description": "Input text"},
                    "text_a": {"type": "string", "description": "First text for comparison"},
                    "text_b": {"type": "string", "description": "Second text for comparison"},
                    "target_language": {"type": "string", "description": "Target language for translation"},
                    "rewrite_style": {"type": "string", "enum": ["formal", "casual", "concise", "detailed", "academic", "creative"], "description": "Rewrite style"},
                    "extract_type": {"type": "string", "enum": ["emails", "urls", "phones", "dates", "names", "addresses", "numbers"], "description": "Extraction type"},
                    "format_type": {"type": "string", "enum": ["uppercase", "lowercase", "title_case", "sentence_case", "camel_case", "snake_case"], "description": "Format type"},
                    "max_length": {"type": "integer", "description": "Max length for summarize"},
                    "keywords_count": {"type": "integer", "description": "Number of keywords to extract"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "count")
        try:
            text = kwargs.get("text", "")
            if action == "count":
                words = len(text.split())
                chars = len(text)
                sentences = text.count(".") + text.count("!") + text.count("?")
                paragraphs = text.count("\n\n") + 1
                return {"characters": chars, "words": words, "sentences": max(sentences, 1), "paragraphs": paragraphs}
            elif action == "format":
                fmt = kwargs.get("format_type", "lowercase")
                if fmt == "uppercase":
                    result = text.upper()
                elif fmt == "lowercase":
                    result = text.lower()
                elif fmt == "title_case":
                    result = text.title()
                elif fmt == "sentence_case":
                    result = text.capitalize()
                elif fmt == "camel_case":
                    parts = text.lower().split()
                    result = parts[0] + "".join(p.capitalize() for p in parts[1:]) if parts else ""
                elif fmt == "snake_case":
                    result = "_".join(text.lower().split())
                else:
                    result = text
                return {"result": result, "format": fmt}
            elif action == "clean":
                import re
                cleaned = re.sub(r'\s+', ' ', text.strip())
                cleaned = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:\-()]', '', cleaned)
                return {"result": cleaned}
            elif action == "extract":
                import re
                extract_type = kwargs.get("extract_type", "emails")
                patterns = {
                    "emails": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                    "urls": r'https?://[^\s<>"]+|www\.[^\s<>"]+',
                    "phones": r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
                    "dates": r'\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',
                    "numbers": r'-?\d+\.?\d*',
                }
                pattern = patterns.get(extract_type, r'.*')
                matches = re.findall(pattern, text)
                return {"extracted": matches, "type": extract_type, "count": len(matches)}
            else:
                from app.core.llm.dispatcher import ModelDispatcher
                from app.core.llm.gateway import llm_gateway
                from app.services.ai_workspace_service import AIWorkspaceService
                svc = AIWorkspaceService(ModelDispatcher(gateway=llm_gateway))
                return await svc.ai_document_assist(action=action, content=text, context="")
        except Exception as e:
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        pass


class MediaConvertTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="media_convert",
            description="Media conversion: image, audio, video, document format conversion, batch conversion, resize, quality, metadata, thumbnail, optimize",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["image_convert", "audio_convert", "video_convert",
                                 "document_convert", "format_info", "batch",
                                 "resize", "quality", "metadata", "thumbnail",
                                 "optimize", "validate"],
                        "description": "Media convert action",
                    },
                    "file_path": {"type": "string", "description": "Source file path"},
                    "file_paths": {"type": "array", "items": {"type": "string"}, "description": "Source file paths for batch"},
                    "output_path": {"type": "string", "description": "Output file path"},
                    "output_format": {"type": "string", "description": "Output format"},
                    "width": {"type": "integer", "description": "Output width"},
                    "height": {"type": "integer", "description": "Output height"},
                    "quality": {"type": "integer", "description": "Quality (1-100)"},
                    "bitrate": {"type": "string", "description": "Audio/video bitrate"},
                    "fps": {"type": "integer", "description": "Video FPS"},
                    "sample_rate": {"type": "integer", "description": "Audio sample rate"},
                    "codec": {"type": "string", "description": "Codec name"},
                    "preserve_metadata": {"type": "boolean", "description": "Preserve metadata"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "format_info")
        try:
            if action == "format_info":
                return {
                    "image": ["png", "jpg", "webp", "bmp", "gif", "tiff", "svg"],
                    "audio": ["mp3", "wav", "ogg", "flac", "aac", "m4a"],
                    "video": ["mp4", "webm", "avi", "mov", "mkv", "gif"],
                    "document": ["pdf", "docx", "xlsx", "pptx", "html", "md", "txt"],
                }
            elif action == "document_convert":
                from markitdown import MarkItDown
                md = MarkItDown()
                file_path = kwargs.get("file_path", "")
                if file_path:
                    result = md.convert(file_path)
                    return {"markdown": result.text_content, "source": file_path}
                return {"error": "file_path required"}
            else:
                return {
                    "action": "workspace_command",
                    "app": "media_convert",
                    "command": action,
                    "file_path": kwargs.get("file_path", ""),
                    "file_paths": kwargs.get("file_paths", []),
                    "output_path": kwargs.get("output_path", ""),
                    "output_format": kwargs.get("output_format", ""),
                    "width": kwargs.get("width", 0),
                    "height": kwargs.get("height", 0),
                    "quality": kwargs.get("quality", 85),
                    "bitrate": kwargs.get("bitrate", ""),
                    "fps": kwargs.get("fps", 30),
                    "sample_rate": kwargs.get("sample_rate", 44100),
                    "codec": kwargs.get("codec", ""),
                    "preserve_metadata": kwargs.get("preserve_metadata", True),
                }
        except ImportError:
            return {"error": "markitdown not installed"}
        except Exception as e:
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        pass


class OcrTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="ocr",
            description="OCR operations: recognize text from images, extract text/tables, batch OCR, language selection, preprocess, export results",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["recognize", "extract_text", "extract_table",
                                 "batch", "language", "preprocess", "template",
                                 "validate", "export", "correct", "layout", "info"],
                        "description": "OCR action",
                    },
                    "image_path": {"type": "string", "description": "Image file path"},
                    "image_paths": {"type": "array", "items": {"type": "string"}, "description": "Image paths for batch"},
                    "language": {"type": "string", "description": "OCR language (eng, chi_sim, jpn, etc.)"},
                    "output_format": {"type": "string", "enum": ["text", "json", "html", "csv"], "description": "Output format"},
                    "preprocess_type": {"type": "string", "enum": ["denoise", "sharpen", "binarize", "deskew", "crop"], "description": "Preprocess type"},
                    "region": {"type": "string", "description": "Region to OCR (x,y,w,h)"},
                    "confidence_threshold": {"type": "number", "description": "Minimum confidence (0-1)"},
                    "export_path": {"type": "string", "description": "Export file path"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "info")
        try:
            if action == "recognize" or action == "extract_text":
                image_path = kwargs.get("image_path", "")
                if not image_path:
                    return {"error": "image_path required"}
                try:
                    import fitz
                    doc = fitz.open(image_path)
                    text = ""
                    for page in doc:
                        text += page.get_text()
                    doc.close()
                    return {"text": text, "source": image_path}
                except Exception:
                    return {"text": "", "source": image_path, "note": "OCR requires image input via PDF or dedicated OCR engine"}
            elif action == "language":
                return {"supported_languages": ["eng", "chi_sim", "chi_tra", "jpn", "kor", "fra", "deu", "spa", "rus", "ara"]}
            else:
                return {
                    "action": "workspace_command",
                    "app": "ocr",
                    "command": action,
                    "image_path": kwargs.get("image_path", ""),
                    "image_paths": kwargs.get("image_paths", []),
                    "language": kwargs.get("language", "eng"),
                    "output_format": kwargs.get("output_format", "text"),
                    "preprocess_type": kwargs.get("preprocess_type", ""),
                    "region": kwargs.get("region", ""),
                    "confidence_threshold": kwargs.get("confidence_threshold", 0.5),
                    "export_path": kwargs.get("export_path", ""),
                }
        except Exception as e:
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        pass


class TranslationTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="translation",
            description="Translation operations: translate text, detect language, batch translation, glossary management, history, compare, context, formalize, simplify",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["translate", "detect", "batch", "glossary",
                                 "history", "compare", "context", "formalize",
                                 "simplify", "localize", "quality", "settings"],
                        "description": "Translation action",
                    },
                    "text": {"type": "string", "description": "Text to translate"},
                    "texts": {"type": "array", "items": {"type": "string"}, "description": "Texts for batch translation"},
                    "source_language": {"type": "string", "description": "Source language code"},
                    "target_language": {"type": "string", "description": "Target language code"},
                    "glossary_name": {"type": "string", "description": "Glossary name"},
                    "glossary_terms": {"type": "object", "description": "Glossary terms (source: target)"},
                    "formality": {"type": "string", "enum": ["formal", "informal"], "description": "Formality level"},
                    "context": {"type": "string", "description": "Translation context"},
                    "domain": {"type": "string", "description": "Domain (tech, medical, legal, etc.)"},
                    "preserve_formatting": {"type": "boolean", "description": "Preserve original formatting"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "translate")
        try:
            if action in ("translate", "detect", "batch", "formalize", "simplify"):
                from app.core.llm.dispatcher import ModelDispatcher
                from app.core.llm.gateway import llm_gateway
                from app.services.ai_workspace_service import AIWorkspaceService
                svc = AIWorkspaceService(ModelDispatcher(gateway=llm_gateway))
                return await svc.ai_document_assist(
                    action=f"translate_{action}",
                    content=kwargs.get("text", ""),
                    context=f"source:{kwargs.get('source_language', '')} target:{kwargs.get('target_language', 'zh')}",
                )
            else:
                return {
                    "action": "workspace_command",
                    "app": "translation",
                    "command": action,
                    "text": kwargs.get("text", ""),
                    "source_language": kwargs.get("source_language", ""),
                    "target_language": kwargs.get("target_language", "zh"),
                    "glossary_name": kwargs.get("glossary_name", ""),
                    "glossary_terms": kwargs.get("glossary_terms", {}),
                    "formality": kwargs.get("formality", "formal"),
                    "context": kwargs.get("context", ""),
                    "domain": kwargs.get("domain", ""),
                }
        except Exception as e:
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        pass


class SpeechTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="speech",
            description="Speech operations: text-to-speech, speech-to-text, transcribe, voice settings, language, speed, emotion, batch, subtitle generation",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["tts", "stt", "transcribe", "voice_settings",
                                 "language", "speed", "emotion", "batch",
                                 "subtitle", "podcast", "clone", "mix"],
                        "description": "Speech action",
                    },
                    "text": {"type": "string", "description": "Text for TTS"},
                    "audio_path": {"type": "string", "description": "Audio file path for STT"},
                    "audio_paths": {"type": "array", "items": {"type": "string"}, "description": "Audio paths for batch"},
                    "voice": {"type": "string", "description": "Voice name or ID"},
                    "language": {"type": "string", "description": "Language code"},
                    "speed_rate": {"type": "number", "description": "Speech speed (0.5-2.0)"},
                    "pitch": {"type": "number", "description": "Pitch adjustment"},
                    "volume": {"type": "number", "description": "Volume (0-1)"},
                    "emotion": {"type": "string", "enum": ["neutral", "happy", "sad", "angry", "calm"], "description": "Voice emotion"},
                    "output_format": {"type": "string", "enum": ["mp3", "wav", "ogg", "flac"], "description": "Output format"},
                    "subtitle_format": {"type": "string", "enum": ["srt", "vtt", "ass"], "description": "Subtitle format"},
                    "output_path": {"type": "string", "description": "Output file path"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "tts")
        return {
            "action": "workspace_command",
            "app": "speech",
            "command": action,
            "text": kwargs.get("text", ""),
            "audio_path": kwargs.get("audio_path", ""),
            "audio_paths": kwargs.get("audio_paths", []),
            "voice": kwargs.get("voice", "default"),
            "language": kwargs.get("language", "zh"),
            "speed_rate": kwargs.get("speed_rate", 1.0),
            "pitch": kwargs.get("pitch", 1.0),
            "volume": kwargs.get("volume", 1.0),
            "emotion": kwargs.get("emotion", "neutral"),
            "output_format": kwargs.get("output_format", "mp3"),
            "subtitle_format": kwargs.get("subtitle_format", "srt"),
            "output_path": kwargs.get("output_path", ""),
        }

    async def _on_hibernate(self) -> None:
        pass


class DataAnalysisTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="data_analysis",
            description="Data analysis: statistics, trends, correlation, outlier detection, forecasting, visualization, comparison, segmentation, aggregation, pivot, regression, clustering",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["stats", "trend", "correlation", "outlier",
                                 "forecast", "visualize", "compare", "segment",
                                 "aggregate", "pivot", "regression", "cluster"],
                        "description": "Data analysis action",
                    },
                    "data": {"type": "array", "items": {"type": "object"}, "description": "Data array"},
                    "columns": {"type": "array", "items": {"type": "string"}, "description": "Column names"},
                    "target_column": {"type": "string", "description": "Target column for analysis"},
                    "group_by": {"type": "string", "description": "Group by column"},
                    "filter": {"type": "object", "description": "Filter conditions"},
                    "time_column": {"type": "string", "description": "Time column for trends"},
                    "value_column": {"type": "string", "description": "Value column"},
                    "forecast_periods": {"type": "integer", "description": "Number of forecast periods"},
                    "chart_type": {"type": "string", "enum": ["line", "bar", "scatter", "heatmap", "pie"], "description": "Chart type for visualization"},
                    "confidence_level": {"type": "number", "description": "Confidence level (0-1)"},
                    "n_clusters": {"type": "integer", "description": "Number of clusters"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "stats")
        try:
            data = kwargs.get("data", [])
            if action == "stats" and data:
                columns = kwargs.get("columns", [])
                if columns and data:
                    col = columns[0]
                    values = [row.get(col, 0) for row in data if isinstance(row.get(col), (int, float))]
                    if values:
                        n = len(values)
                        mean = sum(values) / n
                        variance = sum((x - mean) ** 2 for x in values) / n
                        return {
                            "column": col, "count": n, "mean": mean,
                            "min": min(values), "max": max(values),
                            "std_dev": variance ** 0.5, "median": sorted(values)[n // 2],
                        }
                return {"count": len(data), "columns": columns}
            else:
                from app.core.llm.dispatcher import ModelDispatcher
                from app.core.llm.gateway import llm_gateway
                from app.services.ai_workspace_service import AIWorkspaceService
                svc = AIWorkspaceService(ModelDispatcher(gateway=llm_gateway))
                return await svc.ai_finance_assist(action=action, params=kwargs)
        except Exception as e:
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        pass


class ChartTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="chart",
            description="Chart creation: bar, line, pie, scatter, heatmap, export, customize, animate, interactive, template, data binding, theme",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["bar", "line", "pie", "scatter", "heatmap",
                                 "export", "customize", "animate", "interactive",
                                 "template", "data_bind", "theme"],
                        "description": "Chart action",
                    },
                    "chart_id": {"type": "string", "description": "Chart ID"},
                    "title": {"type": "string", "description": "Chart title"},
                    "data": {"type": "object", "description": "Chart data"},
                    "labels": {"type": "array", "items": {"type": "string"}, "description": "Labels"},
                    "values": {"type": "array", "items": {"type": "number"}, "description": "Values"},
                    "series": {"type": "array", "items": {"type": "object"}, "description": "Data series"},
                    "x_axis": {"type": "string", "description": "X axis label"},
                    "y_axis": {"type": "string", "description": "Y axis label"},
                    "color_scheme": {"type": "string", "description": "Color scheme"},
                    "export_format": {"type": "string", "enum": ["png", "svg", "pdf", "html"], "description": "Export format"},
                    "theme": {"type": "string", "enum": ["light", "dark", "custom"], "description": "Chart theme"},
                    "width": {"type": "integer", "description": "Chart width"},
                    "height": {"type": "integer", "description": "Chart height"},
                    "show_legend": {"type": "boolean", "description": "Show legend"},
                    "show_grid": {"type": "boolean", "description": "Show grid"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "bar")
        return {
            "action": "workspace_command",
            "app": "chart",
            "command": action,
            "chart_id": kwargs.get("chart_id", ""),
            "title": kwargs.get("title", ""),
            "data": kwargs.get("data", {}),
            "labels": kwargs.get("labels", []),
            "values": kwargs.get("values", []),
            "series": kwargs.get("series", []),
            "x_axis": kwargs.get("x_axis", ""),
            "y_axis": kwargs.get("y_axis", ""),
            "color_scheme": kwargs.get("color_scheme", ""),
            "export_format": kwargs.get("export_format", "png"),
            "theme": kwargs.get("theme", "light"),
            "width": kwargs.get("width", 800),
            "height": kwargs.get("height", 400),
            "show_legend": kwargs.get("show_legend", True),
            "show_grid": kwargs.get("show_grid", True),
        }

    async def _on_hibernate(self) -> None:
        pass


class DatabaseTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="database",
            description="Database operations: query, insert, update, delete, schema, export, backup, migrate, index, optimize, relations, transactions",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["query", "insert", "update", "delete", "schema",
                                 "export", "backup", "migrate", "index",
                                 "optimize", "relation", "transaction"],
                        "description": "Database action",
                    },
                    "table": {"type": "string", "description": "Table name"},
                    "query": {"type": "string", "description": "SQL query or filter"},
                    "data": {"type": "object", "description": "Data for insert/update"},
                    "conditions": {"type": "object", "description": "Conditions for update/delete"},
                    "columns": {"type": "array", "items": {"type": "string"}, "description": "Columns to select"},
                    "order_by": {"type": "string", "description": "Order by clause"},
                    "limit": {"type": "integer", "description": "Result limit"},
                    "offset": {"type": "integer", "description": "Result offset"},
                    "export_format": {"type": "string", "enum": ["csv", "json", "sql"], "description": "Export format"},
                    "export_path": {"type": "string", "description": "Export file path"},
                    "index_column": {"type": "string", "description": "Column to index"},
                    "migration_name": {"type": "string", "description": "Migration name"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "schema")
        return {
            "action": "workspace_command",
            "app": "database",
            "command": action,
            "table": kwargs.get("table", ""),
            "query": kwargs.get("query", ""),
            "data": kwargs.get("data", {}),
            "conditions": kwargs.get("conditions", {}),
            "columns": kwargs.get("columns", []),
            "order_by": kwargs.get("order_by", ""),
            "limit": kwargs.get("limit", 100),
            "offset": kwargs.get("offset", 0),
            "export_format": kwargs.get("export_format", "json"),
            "export_path": kwargs.get("export_path", ""),
            "index_column": kwargs.get("index_column", ""),
            "migration_name": kwargs.get("migration_name", ""),
        }

    async def _on_hibernate(self) -> None:
        pass


class WebhookTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="webhook",
            description="Webhook management: create, list, test, delete, log, retry, filter, transform, batch, schedule, security, stats",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create", "list", "test", "delete", "log",
                                 "retry", "filter", "transform", "batch",
                                 "schedule", "security", "stats"],
                        "description": "Webhook action",
                    },
                    "webhook_id": {"type": "string", "description": "Webhook ID"},
                    "name": {"type": "string", "description": "Webhook name"},
                    "url": {"type": "string", "description": "Webhook URL"},
                    "events": {"type": "array", "items": {"type": "string"}, "description": "Events to listen for"},
                    "secret": {"type": "string", "description": "Webhook secret"},
                    "headers": {"type": "object", "description": "Custom headers"},
                    "filter_rules": {"type": "object", "description": "Filter rules"},
                    "transform_rule": {"type": "object", "description": "Transform rules"},
                    "retry_count": {"type": "integer", "description": "Retry count"},
                    "retry_delay_seconds": {"type": "integer", "description": "Retry delay"},
                    "batch_size": {"type": "integer", "description": "Batch size"},
                    "enabled": {"type": "boolean", "description": "Enable webhook"},
                    "payload": {"type": "object", "description": "Test payload"},
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
            "app": "webhook",
            "command": action,
            "webhook_id": kwargs.get("webhook_id", ""),
            "name": kwargs.get("name", ""),
            "url": kwargs.get("url", ""),
            "events": kwargs.get("events", []),
            "secret": kwargs.get("secret", ""),
            "headers": kwargs.get("headers", {}),
            "filter_rules": kwargs.get("filter_rules", {}),
            "transform_rule": kwargs.get("transform_rule", {}),
            "retry_count": kwargs.get("retry_count", 3),
            "retry_delay_seconds": kwargs.get("retry_delay_seconds", 60),
            "batch_size": kwargs.get("batch_size", 1),
            "enabled": kwargs.get("enabled", True),
            "payload": kwargs.get("payload", {}),
        }

    async def _on_hibernate(self) -> None:
        pass


class CronTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="cron",
            description="Cron/schedule management: create, list, update, delete, run, log, pause, resume, validate, import, export, duplicate scheduled tasks",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create", "list", "update", "delete", "run",
                                 "log", "pause", "resume", "validate",
                                 "import", "export", "duplicate"],
                        "description": "Cron action",
                    },
                    "job_id": {"type": "string", "description": "Job ID"},
                    "name": {"type": "string", "description": "Job name"},
                    "description": {"type": "string", "description": "Job description"},
                    "cron_expression": {"type": "string", "description": "Cron expression (e.g., '0 9 * * 1-5')"},
                    "task_type": {"type": "string", "description": "Task type (tool_call, workflow, script, api_call)"},
                    "task_config": {"type": "object", "description": "Task configuration"},
                    "timezone": {"type": "string", "description": "Timezone"},
                    "enabled": {"type": "boolean", "description": "Enable/disable"},
                    "max_retries": {"type": "integer", "description": "Max retries on failure"},
                    "retry_delay_seconds": {"type": "integer", "description": "Retry delay"},
                    "timeout_seconds": {"type": "integer", "description": "Task timeout"},
                    "import_path": {"type": "string", "description": "Import file path"},
                    "export_format": {"type": "string", "description": "Export format"},
                    "limit": {"type": "integer", "description": "Max log entries"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "list")
        try:
            if action == "validate":
                expr = kwargs.get("cron_expression", "")
                parts = expr.split()
                return {"valid": len(parts) == 5, "expression": expr}
            else:
                return {
                    "action": "workspace_command",
                    "app": "cron",
                    "command": action,
                    "job_id": kwargs.get("job_id", ""),
                    "name": kwargs.get("name", ""),
                    "description": kwargs.get("description", ""),
                    "cron_expression": kwargs.get("cron_expression", ""),
                    "task_type": kwargs.get("task_type", "tool_call"),
                    "task_config": kwargs.get("task_config", {}),
                    "timezone": kwargs.get("timezone", "UTC"),
                    "enabled": kwargs.get("enabled", True),
                    "max_retries": kwargs.get("max_retries", 3),
                    "retry_delay_seconds": kwargs.get("retry_delay_seconds", 60),
                    "timeout_seconds": kwargs.get("timeout_seconds", 300),
                    "import_path": kwargs.get("import_path", ""),
                    "export_format": kwargs.get("export_format", "json"),
                    "limit": kwargs.get("limit", 50),
                }
        except Exception as e:
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        pass


def register_extension_tools():
    from app.core.tool.registry import tool_registry
    tools = [
        NotificationTool(),
        AutomationTool(),
        SyncTool(),
        BackupTool(),
        SecurityTool(),
        DeviceBridgeTool(),
        PluginTool(),
        ApiBridgeTool(),
        TextProcessTool(),
        MediaConvertTool(),
        OcrTool(),
        TranslationTool(),
        SpeechTool(),
        DataAnalysisTool(),
        ChartTool(),
        DatabaseTool(),
        WebhookTool(),
        CronTool(),
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
    logger.info(f"Registered {len(registered)} extension tools: {registered}")
    return registered
