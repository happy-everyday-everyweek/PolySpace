import logging
from typing import Any

from app.core.tool.base import BaseTool

logger = logging.getLogger(__name__)


class DocumentTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="document",
            description="Document editor operations: create, edit, format, insert elements, export, summarize, outline, find/replace, comment",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create", "open", "edit", "format_text", "insert_image",
                                 "insert_table", "export", "summarize", "outline",
                                 "word_count", "find_replace", "comment", "save", "close"],
                        "description": "Document action to perform",
                    },
                    "doc_id": {"type": "string", "description": "Document ID"},
                    "title": {"type": "string", "description": "Document title"},
                    "content": {"type": "string", "description": "Document content or text to insert"},
                    "format": {"type": "string", "enum": ["bold", "italic", "underline", "heading1", "heading2", "heading3", "bullet", "numbered", "quote", "code"], "description": "Text format type"},
                    "export_format": {"type": "string", "enum": ["pdf", "docx", "html", "markdown", "txt"], "description": "Export format"},
                    "find_text": {"type": "string", "description": "Text to find"},
                    "replace_text": {"type": "string", "description": "Replacement text"},
                    "comment_text": {"type": "string", "description": "Comment text"},
                    "position": {"type": "integer", "description": "Cursor position or line number"},
                    "image_url": {"type": "string", "description": "Image URL or path to insert"},
                    "table_rows": {"type": "integer", "description": "Number of table rows"},
                    "table_cols": {"type": "integer", "description": "Number of table columns"},
                    "context": {"type": "string", "description": "Additional context for AI operations"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "create")
        try:
            if action in ("summarize", "outline"):
                from app.core.llm.dispatcher import ModelDispatcher
                from app.core.llm.gateway import llm_gateway
                from app.services.ai_workspace_service import AIWorkspaceService
                svc = AIWorkspaceService(ModelDispatcher(gateway=llm_gateway))
                return await svc.ai_document_assist(
                    action=action,
                    content=kwargs.get("content", ""),
                    context=kwargs.get("context", ""),
                )
            elif action == "create":
                return {
                    "action": "workspace_command",
                    "app": "document",
                    "command": "create",
                    "title": kwargs.get("title", "Untitled Document"),
                    "content": kwargs.get("content", ""),
                }
            elif action == "open":
                return {
                    "action": "workspace_command",
                    "app": "document",
                    "command": "open",
                    "doc_id": kwargs.get("doc_id", ""),
                }
            elif action == "edit":
                return {
                    "action": "workspace_command",
                    "app": "document",
                    "command": "edit",
                    "doc_id": kwargs.get("doc_id", ""),
                    "content": kwargs.get("content", ""),
                    "position": kwargs.get("position", 0),
                }
            elif action == "format_text":
                return {
                    "action": "workspace_command",
                    "app": "document",
                    "command": "format_text",
                    "format": kwargs.get("format", "bold"),
                    "doc_id": kwargs.get("doc_id", ""),
                }
            elif action == "insert_image":
                return {
                    "action": "workspace_command",
                    "app": "document",
                    "command": "insert_image",
                    "doc_id": kwargs.get("doc_id", ""),
                    "image_url": kwargs.get("image_url", ""),
                }
            elif action == "insert_table":
                return {
                    "action": "workspace_command",
                    "app": "document",
                    "command": "insert_table",
                    "doc_id": kwargs.get("doc_id", ""),
                    "rows": kwargs.get("table_rows", 3),
                    "cols": kwargs.get("table_cols", 3),
                }
            elif action == "export":
                return await self._export_document(kwargs)
            elif action == "word_count":
                return {
                    "action": "workspace_command",
                    "app": "document",
                    "command": "word_count",
                    "doc_id": kwargs.get("doc_id", ""),
                }
            elif action == "find_replace":
                return {
                    "action": "workspace_command",
                    "app": "document",
                    "command": "find_replace",
                    "doc_id": kwargs.get("doc_id", ""),
                    "find": kwargs.get("find_text", ""),
                    "replace": kwargs.get("replace_text", ""),
                }
            elif action == "comment":
                return {
                    "action": "workspace_command",
                    "app": "document",
                    "command": "comment",
                    "doc_id": kwargs.get("doc_id", ""),
                    "comment": kwargs.get("comment_text", ""),
                    "position": kwargs.get("position", 0),
                }
            elif action == "save":
                return {
                    "action": "workspace_command",
                    "app": "document",
                    "command": "save",
                    "doc_id": kwargs.get("doc_id", ""),
                }
            elif action == "close":
                return {
                    "action": "workspace_command",
                    "app": "document",
                    "command": "close",
                    "doc_id": kwargs.get("doc_id", ""),
                }
            return {"error": f"Unknown action: {action}"}
        except Exception as e:
            return {"error": str(e)}

    async def _export_document(self, kwargs: dict) -> Any:
        from app.services.doc_conversion_service import doc_conversion_service
        export_format = kwargs.get("export_format", "pdf")
        doc_id = kwargs.get("doc_id", "")
        content = kwargs.get("content", "")
        title = kwargs.get("title", "Untitled Document")

        if content and export_format in ("docx", "pdf", "odt", "rtf"):
            if export_format == "docx":
                result = await doc_conversion_service.html_to_docx(content, title)
            elif export_format == "pdf":
                result = await doc_conversion_service.html_to_pdf(content, title)
            else:
                result = await doc_conversion_service.html_to_docx(content, title)
                if "error" not in result and export_format != "docx":
                    convert_result = await doc_conversion_service.convert_file(
                        result["output_path"], export_format, "docx"
                    )
                    if "error" not in convert_result:
                        result = convert_result
            if "error" not in result:
                return result
            return {
                "action": "workspace_command",
                "app": "document",
                "command": "export",
                "doc_id": doc_id,
                "format": export_format,
                "fallback": True,
                "error_detail": result.get("error", ""),
            }

        if doc_id:
            from app.services.workspace_service import workspace_service
            doc = await workspace_service.get_document(doc_id)
            if doc and doc.content:
                if export_format in ("docx", "pdf"):
                    if export_format == "docx":
                        result = await doc_conversion_service.html_to_docx(doc.content, doc.title)
                    else:
                        result = await doc_conversion_service.html_to_pdf(doc.content, doc.title)
                    if "error" not in result:
                        return result

        return {
            "action": "workspace_command",
            "app": "document",
            "command": "export",
            "doc_id": doc_id,
            "format": export_format,
        }

    async def _on_hibernate(self) -> None:
        pass


class PptTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="ppt",
            description="PPT editor operations: create, add/edit/delete slides, apply themes, add animations, export, summarize, AI assist",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create", "add_slide", "edit_slide", "delete_slide",
                                 "reorder_slides", "apply_theme", "add_animation",
                                 "export", "summarize", "add_notes", "insert_image",
                                 "duplicate_slide", "add_transition", "save", "close",
                                 "generate_slides", "improve_slide", "suggest_design",
                                 "outline_to_slides", "expand_content", "condense_content",
                                 "translate", "tone_adjust", "smart_layout", "image_suggest",
                                 "coaching", "check_consistency", "audience_analysis", "timing_estimate"],
                        "description": "PPT action to perform",
                    },
                    "ppt_id": {"type": "string", "description": "PPT file ID"},
                    "title": {"type": "string", "description": "Presentation or slide title"},
                    "slide_index": {"type": "integer", "description": "Slide index (0-based)"},
                    "content": {"type": "string", "description": "Slide content or notes"},
                    "layout": {"type": "string", "enum": ["title", "title_content", "two_content", "blank", "image", "comparison"], "description": "Slide layout"},
                    "theme": {"type": "string", "description": "Theme name or ID"},
                    "animation_type": {"type": "string", "enum": ["fade", "slide", "zoom", "fly", "appear"], "description": "Animation type"},
                    "transition_type": {"type": "string", "enum": ["fade", "push", "wipe", "split", "dissolve"], "description": "Transition type"},
                    "export_format": {"type": "string", "enum": ["pdf", "pptx", "images", "html"], "description": "Export format"},
                    "image_url": {"type": "string", "description": "Image URL or path"},
                    "target_index": {"type": "integer", "description": "Target position for reorder"},
                    "slides": {"type": "array", "items": {"type": "object"}, "description": "Slides data for summarize"},
                    "params": {"type": "object", "description": "Additional parameters for AI actions"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "create")
        ai_actions = {
            "summarize", "add_slide", "edit_slide", "apply_theme", "add_animation", "add_notes",
            "generate_slides", "improve_slide", "suggest_design", "outline_to_slides",
            "expand_content", "condense_content", "translate", "tone_adjust",
            "smart_layout", "image_suggest", "coaching", "check_consistency",
            "audience_analysis", "timing_estimate",
        }
        try:
            if action in ai_actions:
                from app.core.llm.dispatcher import ModelDispatcher
                from app.core.llm.gateway import llm_gateway
                from app.services.ai_workspace_service import AIWorkspaceService
                svc = AIWorkspaceService(ModelDispatcher(gateway=llm_gateway))
                if action == "summarize":
                    return await svc.ai_ppt_summary(kwargs.get("slides", []))
                return await svc.ai_ppt_assist(action=action, params=kwargs.get("params", kwargs))
            if action == "export":
                return await self._export_ppt(kwargs)
            else:
                return {
                    "action": "workspace_command",
                    "app": "ppt",
                    "command": action,
                    "ppt_id": kwargs.get("ppt_id", ""),
                    "title": kwargs.get("title", ""),
                    "slide_index": kwargs.get("slide_index", 0),
                    "content": kwargs.get("content", ""),
                    "layout": kwargs.get("layout", "title_content"),
                    "theme": kwargs.get("theme", ""),
                    "export_format": kwargs.get("export_format", "pptx"),
                    "image_url": kwargs.get("image_url", ""),
                    "target_index": kwargs.get("target_index", 0),
                }
        except Exception as e:
            return {"error": str(e)}

    async def _export_ppt(self, kwargs: dict) -> Any:
        from app.services.doc_conversion_service import doc_conversion_service
        export_format = kwargs.get("export_format", "pptx")
        ppt_id = kwargs.get("ppt_id", "")
        slides = kwargs.get("slides", [])
        title = kwargs.get("title", "Untitled Presentation")

        if export_format == "pptx" and slides:
            result = await doc_conversion_service.slides_data_to_pptx(slides, title)
            if "error" not in result:
                return result

        if export_format == "pdf" and slides:
            pptx_result = await doc_conversion_service.slides_data_to_pptx(slides, title)
            if "error" not in pptx_result:
                pdf_result = await doc_conversion_service.convert_file(
                    pptx_result["output_path"], "pdf", "pptx"
                )
                if "error" not in pdf_result:
                    return pdf_result

        return {
            "action": "workspace_command",
            "app": "ppt",
            "command": "export",
            "ppt_id": ppt_id,
            "format": export_format,
        }

    async def _on_hibernate(self) -> None:
        pass


class ExcelTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="excel",
            description="Spreadsheet operations: create, edit cells/ranges, formulas, charts, sort, filter, pivot, export, import CSV",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create", "edit_cell", "edit_range", "formula",
                                 "create_chart", "sort", "filter", "pivot",
                                 "export", "import_csv", "merge_cells",
                                 "conditional_format", "save", "close", "auto_fit",
                                 "freeze_panes", "data_validation"],
                        "description": "Excel action to perform",
                    },
                    "sheet_id": {"type": "string", "description": "Spreadsheet ID"},
                    "title": {"type": "string", "description": "Spreadsheet title"},
                    "sheet_name": {"type": "string", "description": "Sheet name"},
                    "cell": {"type": "string", "description": "Cell reference (e.g., A1)"},
                    "value": {"type": "string", "description": "Cell value"},
                    "range": {"type": "string", "description": "Cell range (e.g., A1:C10)"},
                    "values": {"type": "array", "items": {"type": "array"}, "description": "2D array of values for range"},
                    "formula_expr": {"type": "string", "description": "Formula expression (e.g., =SUM(A1:A10))"},
                    "chart_type": {"type": "string", "enum": ["bar", "line", "pie", "scatter", "area", "combo"], "description": "Chart type"},
                    "chart_range": {"type": "string", "description": "Data range for chart"},
                    "sort_column": {"type": "string", "description": "Column to sort by"},
                    "sort_order": {"type": "string", "enum": ["asc", "desc"], "description": "Sort order"},
                    "filter_column": {"type": "string", "description": "Column to filter"},
                    "filter_value": {"type": "string", "description": "Filter value"},
                    "export_format": {"type": "string", "enum": ["xlsx", "csv", "pdf", "html"], "description": "Export format"},
                    "csv_path": {"type": "string", "description": "CSV file path to import"},
                    "condition": {"type": "string", "description": "Conditional format rule"},
                    "condition_style": {"type": "object", "description": "Style for conditional format"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "create")
        try:
            if action in ("formula", "create_chart", "pivot", "conditional_format", "data_validation"):
                from app.core.llm.dispatcher import ModelDispatcher
                from app.core.llm.gateway import llm_gateway
                from app.services.ai_workspace_service import AIWorkspaceService
                svc = AIWorkspaceService(ModelDispatcher(gateway=llm_gateway))
                return await svc.ai_excel_assist(action=action, params=kwargs)
            if action == "export":
                return await self._export_excel(kwargs)
            else:
                return {
                    "action": "workspace_command",
                    "app": "excel",
                    "command": action,
                    "sheet_id": kwargs.get("sheet_id", ""),
                    "title": kwargs.get("title", "Untitled Spreadsheet"),
                    "sheet_name": kwargs.get("sheet_name", "Sheet1"),
                    "cell": kwargs.get("cell", "A1"),
                    "value": kwargs.get("value", ""),
                    "range": kwargs.get("range", ""),
                    "values": kwargs.get("values", []),
                    "formula_expr": kwargs.get("formula_expr", ""),
                    "chart_type": kwargs.get("chart_type", "bar"),
                    "chart_range": kwargs.get("chart_range", ""),
                    "sort_column": kwargs.get("sort_column", ""),
                    "sort_order": kwargs.get("sort_order", "asc"),
                    "filter_column": kwargs.get("filter_column", ""),
                    "filter_value": kwargs.get("filter_value", ""),
                    "export_format": kwargs.get("export_format", "xlsx"),
                    "csv_path": kwargs.get("csv_path", ""),
                    "condition": kwargs.get("condition", ""),
                }
        except Exception as e:
            return {"error": str(e)}

    async def _export_excel(self, kwargs: dict) -> Any:
        from app.services.doc_conversion_service import doc_conversion_service
        export_format = kwargs.get("export_format", "xlsx")
        sheet_id = kwargs.get("sheet_id", "")
        values = kwargs.get("values", [])
        headers = kwargs.get("headers")
        title = kwargs.get("title", "Untitled Spreadsheet")

        if export_format == "xlsx" and values:
            result = await doc_conversion_service.spreadsheet_data_to_xlsx(values, title, headers)
            if "error" not in result:
                return result

        if export_format == "csv" and values:
            result = await doc_conversion_service.spreadsheet_data_to_csv(values, headers)
            if "error" not in result:
                return result

        if export_format == "pdf" and values:
            xlsx_result = await doc_conversion_service.spreadsheet_data_to_xlsx(values, title, headers)
            if "error" not in xlsx_result:
                pdf_result = await doc_conversion_service.convert_file(
                    xlsx_result["output_path"], "pdf", "xlsx"
                )
                if "error" not in pdf_result:
                    return pdf_result

        return {
            "action": "workspace_command",
            "app": "excel",
            "command": "export",
            "sheet_id": sheet_id,
            "format": export_format,
        }

    async def _on_hibernate(self) -> None:
        pass


class NotesTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="notes",
            description="Notes management: create, edit, organize, search, tag, link notes, export, outline, template, archive",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create", "edit", "organize", "search", "tag",
                                 "link", "export", "outline", "template",
                                 "archive", "pin", "group", "list", "delete", "duplicate"],
                        "description": "Notes action to perform",
                    },
                    "note_id": {"type": "string", "description": "Note ID"},
                    "title": {"type": "string", "description": "Note title"},
                    "content": {"type": "string", "description": "Note content"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags"},
                    "query": {"type": "string", "description": "Search query"},
                    "link_to": {"type": "string", "description": "Note ID to link to"},
                    "export_format": {"type": "string", "enum": ["markdown", "html", "pdf", "txt"], "description": "Export format"},
                    "group_name": {"type": "string", "description": "Group name for organizing"},
                    "template_name": {"type": "string", "description": "Template name to apply"},
                    "folder": {"type": "string", "description": "Folder path"},
                    "color": {"type": "string", "description": "Note color"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "list")
        try:
            if action in ("outline", "template", "organize"):
                from app.core.llm.dispatcher import ModelDispatcher
                from app.core.llm.gateway import llm_gateway
                from app.services.ai_workspace_service import AIWorkspaceService
                svc = AIWorkspaceService(ModelDispatcher(gateway=llm_gateway))
                return await svc.ai_notes_assist(action=action, params=kwargs)
            else:
                return {
                    "action": "workspace_command",
                    "app": "notes",
                    "command": action,
                    "note_id": kwargs.get("note_id", ""),
                    "title": kwargs.get("title", ""),
                    "content": kwargs.get("content", ""),
                    "tags": kwargs.get("tags", []),
                    "query": kwargs.get("query", ""),
                    "link_to": kwargs.get("link_to", ""),
                    "export_format": kwargs.get("export_format", "markdown"),
                    "group_name": kwargs.get("group_name", ""),
                    "folder": kwargs.get("folder", ""),
                    "color": kwargs.get("color", "default"),
                }
        except Exception as e:
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        pass


class MindmapTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="mindmap",
            description="Mind map operations: create, add/edit/delete nodes, connect, layout, collapse/expand, export, style",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create", "add_node", "edit_node", "delete_node",
                                 "connect", "disconnect", "layout", "collapse",
                                 "expand", "export", "style", "center", "list", "search"],
                        "description": "Mind map action to perform",
                    },
                    "map_id": {"type": "string", "description": "Mind map ID"},
                    "title": {"type": "string", "description": "Map or node title"},
                    "node_id": {"type": "string", "description": "Node ID"},
                    "parent_id": {"type": "string", "description": "Parent node ID"},
                    "content": {"type": "string", "description": "Node content or description"},
                    "source_id": {"type": "string", "description": "Source node ID for connection"},
                    "target_id": {"type": "string", "description": "Target node ID for connection"},
                    "layout_type": {"type": "string", "enum": ["tree", "radial", "organic", "right", "bottom"], "description": "Layout type"},
                    "export_format": {"type": "string", "enum": ["png", "svg", "pdf", "json", "markdown"], "description": "Export format"},
                    "style_name": {"type": "string", "description": "Style name or theme"},
                    "color": {"type": "string", "description": "Node color"},
                    "query": {"type": "string", "description": "Search query"},
                    "topic": {"type": "string", "description": "Central topic for creation"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "list")
        try:
            if action in ("create", "add_node", "edit_node", "layout", "style"):
                from app.core.llm.dispatcher import ModelDispatcher
                from app.core.llm.gateway import llm_gateway
                from app.services.ai_workspace_service import AIWorkspaceService
                svc = AIWorkspaceService(ModelDispatcher(gateway=llm_gateway))
                return await svc.ai_mindmap_assist(action=action, params=kwargs)
            else:
                return {
                    "action": "workspace_command",
                    "app": "mindmap",
                    "command": action,
                    "map_id": kwargs.get("map_id", ""),
                    "node_id": kwargs.get("node_id", ""),
                    "parent_id": kwargs.get("parent_id", ""),
                    "source_id": kwargs.get("source_id", ""),
                    "target_id": kwargs.get("target_id", ""),
                    "layout_type": kwargs.get("layout_type", "tree"),
                    "export_format": kwargs.get("export_format", "json"),
                    "style_name": kwargs.get("style_name", ""),
                    "color": kwargs.get("color", ""),
                    "query": kwargs.get("query", ""),
                }
        except Exception as e:
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        pass


class ReaderTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="reader",
            description="Reader operations: import documents, bookmark, annotate, highlight, track progress, table of contents, export notes",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["import", "bookmark", "annotate", "highlight",
                                 "progress", "toc", "export_notes", "search",
                                 "next_page", "prev_page", "jump", "settings",
                                 "list_bookmarks", "list_annotations"],
                        "description": "Reader action to perform",
                    },
                    "reader_id": {"type": "string", "description": "Reader session ID"},
                    "file_path": {"type": "string", "description": "File path to import"},
                    "page": {"type": "integer", "description": "Page number"},
                    "text": {"type": "string", "description": "Text for annotation or highlight"},
                    "note": {"type": "string", "description": "Annotation note"},
                    "color": {"type": "string", "description": "Highlight color"},
                    "query": {"type": "string", "description": "Search query"},
                    "export_format": {"type": "string", "enum": ["markdown", "html", "txt", "pdf"], "description": "Export format"},
                    "font_size": {"type": "integer", "description": "Font size"},
                    "theme": {"type": "string", "enum": ["light", "dark", "sepia"], "description": "Reading theme"},
                    "line_height": {"type": "number", "description": "Line height multiplier"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "toc")
        try:
            if action in ("annotate", "highlight", "export_notes"):
                from app.core.llm.dispatcher import ModelDispatcher
                from app.core.llm.gateway import llm_gateway
                from app.services.ai_workspace_service import AIWorkspaceService
                svc = AIWorkspaceService(ModelDispatcher(gateway=llm_gateway))
                return await svc.ai_reader_assist(action=action, params=kwargs)
            else:
                return {
                    "action": "workspace_command",
                    "app": "reader",
                    "command": action,
                    "reader_id": kwargs.get("reader_id", ""),
                    "file_path": kwargs.get("file_path", ""),
                    "page": kwargs.get("page", 1),
                    "text": kwargs.get("text", ""),
                    "note": kwargs.get("note", ""),
                    "color": kwargs.get("color", "yellow"),
                    "query": kwargs.get("query", ""),
                    "export_format": kwargs.get("export_format", "markdown"),
                    "font_size": kwargs.get("font_size", 16),
                    "theme": kwargs.get("theme", "light"),
                    "line_height": kwargs.get("line_height", 1.6),
                }
        except Exception as e:
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        pass


class CodeEditorTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="code_editor",
            description="Code editor operations: create, edit, format, lint, run, save, use templates and snippets, find/replace, goto line, diff",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create", "edit", "format", "lint", "run",
                                 "save", "template", "snippet", "find_replace",
                                 "goto_line", "autocomplete", "diff", "close",
                                 "list_files", "open_file"],
                        "description": "Code editor action to perform",
                    },
                    "file_id": {"type": "string", "description": "File ID"},
                    "file_path": {"type": "string", "description": "File path"},
                    "content": {"type": "string", "description": "File content or code"},
                    "language": {"type": "string", "description": "Programming language"},
                    "template_name": {"type": "string", "description": "Template name"},
                    "snippet_name": {"type": "string", "description": "Snippet name"},
                    "find_text": {"type": "string", "description": "Text to find"},
                    "replace_text": {"type": "string", "description": "Replacement text"},
                    "line": {"type": "integer", "description": "Line number"},
                    "column": {"type": "integer", "description": "Column number"},
                    "args": {"type": "array", "items": {"type": "string"}, "description": "Run arguments"},
                    "stdin": {"type": "string", "description": "Standard input for run"},
                    "original_content": {"type": "string", "description": "Original content for diff"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "list_files")
        try:
            if action in ("autocomplete", "lint", "format", "template", "snippet", "diff"):
                from app.core.llm.dispatcher import ModelDispatcher
                from app.core.llm.gateway import llm_gateway
                from app.services.ai_workspace_service import AIWorkspaceService
                svc = AIWorkspaceService(ModelDispatcher(gateway=llm_gateway))
                return await svc.ai_code_assist(action=action, params=kwargs)
            elif action == "run":
                from app.core.agent.sandbox import LocalSandbox
                sandbox = LocalSandbox()
                code = kwargs.get("content", "")
                language = kwargs.get("language", "python")
                result = await sandbox.execute(code, language=language, timeout=30)
                return result
            else:
                return {
                    "action": "workspace_command",
                    "app": "code_editor",
                    "command": action,
                    "file_id": kwargs.get("file_id", ""),
                    "file_path": kwargs.get("file_path", ""),
                    "content": kwargs.get("content", ""),
                    "language": kwargs.get("language", "python"),
                    "find_text": kwargs.get("find_text", ""),
                    "replace_text": kwargs.get("replace_text", ""),
                    "line": kwargs.get("line", 1),
                    "column": kwargs.get("column", 1),
                }
        except Exception as e:
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        pass


class ImageEditorTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="image_editor",
            description="Image editing operations: open, crop, resize, rotate, flip, apply filters, annotate, compress, convert, export",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["open", "crop", "resize", "rotate", "flip",
                                 "filter", "annotate", "compress", "convert",
                                 "export", "undo", "redo", "info", "thumbnail",
                                 "watermark", "adjust"],
                        "description": "Image editor action to perform",
                    },
                    "image_id": {"type": "string", "description": "Image ID"},
                    "file_path": {"type": "string", "description": "Image file path"},
                    "x": {"type": "integer", "description": "Crop start X"},
                    "y": {"type": "integer", "description": "Crop start Y"},
                    "width": {"type": "integer", "description": "Width for crop/resize"},
                    "height": {"type": "integer", "description": "Height for crop/resize"},
                    "angle": {"type": "integer", "description": "Rotation angle in degrees"},
                    "flip_direction": {"type": "string", "enum": ["horizontal", "vertical"], "description": "Flip direction"},
                    "filter_name": {"type": "string", "enum": ["grayscale", "sepia", "blur", "sharpen", "brightness", "contrast", "invert", "emboss"], "description": "Filter name"},
                    "filter_value": {"type": "number", "description": "Filter intensity (0-1)"},
                    "annotation_text": {"type": "string", "description": "Annotation text"},
                    "annotation_color": {"type": "string", "description": "Annotation color"},
                    "quality": {"type": "integer", "description": "Compression quality (1-100)"},
                    "output_format": {"type": "string", "enum": ["png", "jpg", "webp", "bmp", "gif"], "description": "Output format"},
                    "watermark_text": {"type": "string", "description": "Watermark text"},
                    "brightness": {"type": "number", "description": "Brightness adjustment (-1 to 1)"},
                    "contrast": {"type": "number", "description": "Contrast adjustment (-1 to 1)"},
                    "saturation": {"type": "number", "description": "Saturation adjustment (-1 to 1)"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "info")
        try:
            if action in ("annotate", "filter", "adjust", "watermark"):
                from app.core.llm.dispatcher import ModelDispatcher
                from app.core.llm.gateway import llm_gateway
                from app.services.ai_workspace_service import AIWorkspaceService
                svc = AIWorkspaceService(ModelDispatcher(gateway=llm_gateway))
                return await svc.ai_image_assist(action=action, params=kwargs)
            else:
                return {
                    "action": "workspace_command",
                    "app": "image_editor",
                    "command": action,
                    "image_id": kwargs.get("image_id", ""),
                    "file_path": kwargs.get("file_path", ""),
                    "x": kwargs.get("x", 0),
                    "y": kwargs.get("y", 0),
                    "width": kwargs.get("width", 0),
                    "height": kwargs.get("height", 0),
                    "angle": kwargs.get("angle", 0),
                    "flip_direction": kwargs.get("flip_direction", "horizontal"),
                    "filter_name": kwargs.get("filter_name", "grayscale"),
                    "filter_value": kwargs.get("filter_value", 0.5),
                    "quality": kwargs.get("quality", 85),
                    "output_format": kwargs.get("output_format", "png"),
                    "watermark_text": kwargs.get("watermark_text", ""),
                    "brightness": kwargs.get("brightness", 0),
                    "contrast": kwargs.get("contrast", 0),
                    "saturation": kwargs.get("saturation", 0),
                }
        except Exception as e:
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        pass


class VideoEditorTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="video_editor",
            description=(
                "Hyperframes-based video composition editor. Create HTML compositions "
                "with video clips, images, text overlays, audio tracks, and GSAP animations. "
                "Render to MP4/WebM/MOV. Also supports FFmpeg operations (trim, split, merge)."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "create_composition", "add_video", "add_image", "add_text",
                            "add_audio", "add_composition", "remove_element", "update_element",
                            "add_zoom_keyframe", "list_elements", "generate_html", "render",
                            "preview", "lint", "list_compositions", "delete_composition",
                            "get_composition",
                            "trim", "split", "merge", "add_effect", "add_subtitle",
                            "audio_extract", "thumbnail", "info", "convert", "speed",
                            "add_text_overlay", "analyze",
                        ],
                        "description": "Video editor action to perform",
                    },
                    "composition_id": {"type": "string", "description": "Composition ID"},
                    "title": {"type": "string", "description": "Composition title"},
                    "resolution": {
                        "type": "string",
                        "enum": ["landscape", "portrait"],
                        "description": "Canvas resolution",
                    },
                    "total_duration": {"type": "number", "description": "Total duration in seconds"},
                    "element_id": {"type": "string", "description": "Timeline element ID"},
                    "element_name": {"type": "string", "description": "Element display name"},
                    "src": {"type": "string", "description": "Source file path or URL"},
                    "start_time": {"type": "number", "description": "Start time in seconds"},
                    "duration": {"type": "number", "description": "Duration in seconds"},
                    "end_time": {"type": "number", "description": "End time in seconds"},
                    "z_index": {"type": "integer", "description": "Layer order"},
                    "x": {"type": "number", "description": "X position"},
                    "y": {"type": "number", "description": "Y position"},
                    "scale": {"type": "number", "description": "Scale factor"},
                    "opacity": {"type": "number", "description": "Opacity 0-1"},
                    "content": {"type": "string", "description": "Text content"},
                    "color": {"type": "string", "description": "Text color"},
                    "font_size": {"type": "integer", "description": "Font size in pixels"},
                    "font_weight": {"type": "integer", "description": "Font weight"},
                    "font_family": {"type": "string", "description": "Font family"},
                    "volume": {"type": "number", "description": "Audio volume 0-1"},
                    "media_start_time": {"type": "number", "description": "Media offset in seconds"},
                    "has_audio": {"type": "boolean", "description": "Video has audio track"},
                    "updates": {"type": "object", "description": "Properties to update on element"},
                    "zoom_scale": {"type": "number", "description": "Zoom scale factor"},
                    "focus_x": {"type": "number", "description": "Zoom focus X"},
                    "focus_y": {"type": "number", "description": "Zoom focus Y"},
                    "fps": {"type": "integer", "enum": [24, 30, 60], "description": "Render FPS"},
                    "quality": {
                        "type": "string",
                        "enum": ["draft", "standard", "high", "low", "medium"],
                        "description": "Quality preset",
                    },
                    "format": {"type": "string", "enum": ["mp4", "webm", "mov"], "description": "Output format"},
                    "output_path": {"type": "string", "description": "Custom output path"},
                    "file_path": {"type": "string", "description": "Video file path (FFmpeg actions)"},
                    "file_paths": {"type": "array", "items": {"type": "string"}, "description": "Multiple file paths"},
                    "split_time": {"type": "number", "description": "Split point in seconds"},
                    "effect_name": {
                        "type": "string",
                        "enum": ["fade_in", "fade_out", "blur", "grayscale", "sepia", "vignette", "noise"],
                        "description": "Effect name",
                    },
                    "subtitle_text": {"type": "string", "description": "Subtitle text"},
                    "speed_factor": {"type": "number", "description": "Speed factor"},
                    "export_format": {
                        "type": "string",
                        "enum": ["mp4", "webm", "avi", "gif", "mov"],
                        "description": "Export format",
                    },
                    "text_content": {"type": "string", "description": "Text overlay content"},
                    "text_position": {
                        "type": "string",
                        "enum": ["top", "center", "bottom"],
                        "description": "Text position",
                    },
                    "custom_styles": {"type": "string", "description": "Custom CSS styles"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    def _parse_time(self, time_val: Any) -> float:
        if isinstance(time_val, (int, float)):
            return float(time_val)
        if not time_val:
            return 0.0
        try:
            return float(time_val)
        except ValueError:
            parts = str(time_val).split(":")
            if len(parts) == 3:
                return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
            if len(parts) == 2:
                return float(parts[0]) * 60 + float(parts[1])
            return 0.0

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "info")
        try:
            composition_actions = {
                "create_composition", "add_video", "add_image", "add_text",
                "add_audio", "add_composition", "remove_element", "update_element",
                "add_zoom_keyframe", "list_elements", "generate_html", "render",
                "preview", "lint", "list_compositions", "delete_composition",
                "get_composition",
            }

            if action in composition_actions:
                return await self._composition_action(action, kwargs)

            from app.services.video_service import video_service

            if action == "analyze":
                from app.core.llm.dispatcher import ModelDispatcher
                from app.core.llm.gateway import llm_gateway
                from app.services.ai_workspace_service import AIWorkspaceService
                svc = AIWorkspaceService(ModelDispatcher(gateway=llm_gateway))
                return await svc.ai_video_analyze(kwargs)
            elif action == "add_subtitle":
                from app.core.llm.dispatcher import ModelDispatcher
                from app.core.llm.gateway import llm_gateway
                from app.services.ai_workspace_service import AIWorkspaceService
                svc = AIWorkspaceService(ModelDispatcher(gateway=llm_gateway))
                return await svc.ai_generate_subtitles(
                    kwargs.get("subtitle_text", ""), "zh"
                )
            elif action == "trim":
                return await video_service.trim(
                    kwargs.get("file_path", ""),
                    self._parse_time(kwargs.get("start_time", 0)),
                    self._parse_time(kwargs.get("end_time", 0)),
                )
            elif action == "merge":
                return await video_service.merge(kwargs.get("file_paths", []))
            elif action == "split":
                return await video_service.split(
                    kwargs.get("file_path", ""),
                    self._parse_time(kwargs.get("split_time", 0)),
                )
            elif action == "speed":
                return await video_service.change_speed(
                    kwargs.get("file_path", ""),
                    kwargs.get("speed_factor", 1.0),
                )
            elif action == "add_effect":
                return await video_service.apply_effect(
                    kwargs.get("file_path", ""),
                    kwargs.get("effect_name", "grayscale"),
                )
            elif action in ("add_text", "add_text_overlay"):
                return await video_service.add_text_overlay(
                    kwargs.get("file_path", ""),
                    kwargs.get("text_content", ""),
                    kwargs.get("text_position", "bottom"),
                )
            elif action == "audio_extract":
                return await video_service.extract_audio(kwargs.get("file_path", ""))
            elif action == "thumbnail":
                return await video_service.generate_thumbnail(
                    kwargs.get("file_path", ""),
                    self._parse_time(kwargs.get("start_time", 1)),
                )
            elif action == "info":
                return await video_service.get_info(kwargs.get("file_path", ""))
            elif action == "convert":
                return await video_service.convert(
                    kwargs.get("file_path", ""),
                    kwargs.get("export_format", "mp4"),
                    kwargs.get("quality", "medium"),
                )
            else:
                return {
                    "action": "workspace_command",
                    "app": "video_editor",
                    "command": action,
                    "composition_id": kwargs.get("composition_id", ""),
                    "file_path": kwargs.get("file_path", ""),
                }
        except Exception as e:
            return {"error": str(e)}

    async def _composition_action(self, action: str, kwargs: dict) -> Any:
        from app.services.video_editor_service import (
            StageZoomKeyframe,
            TimelineElement,
            video_editor_service,
        )

        svc = video_editor_service

        if action == "create_composition":
            comp = await svc.create_composition(
                title=kwargs.get("title", "Untitled"),
                resolution=kwargs.get("resolution", "landscape"),
                total_duration=kwargs.get("total_duration", 10.0),
            )
            return {"success": True, "composition": comp.to_dict()}

        elif action in ("add_video", "add_image", "add_text", "add_audio", "add_composition"):
            composition_id = kwargs.get("composition_id", "")
            if not composition_id:
                return {"error": "composition_id is required"}
            el = TimelineElement(
                type=action.replace("add_", ""),
                name=kwargs.get("element_name", action.replace("add_", "")),
                start_time=float(kwargs.get("start_time", 0)),
                duration=float(kwargs.get("duration", 5)),
                z_index=int(kwargs.get("z_index", 0)),
                x=float(kwargs.get("x", 0)),
                y=float(kwargs.get("y", 0)),
                scale=float(kwargs.get("scale", 1)),
                opacity=float(kwargs.get("opacity", 1)),
                src=kwargs.get("src", ""),
                content=kwargs.get("content", ""),
                color=kwargs.get("color", "white"),
                font_size=int(kwargs.get("font_size", 48)),
                font_weight=int(kwargs.get("font_weight", 700)),
                font_family=kwargs.get("font_family", "Inter"),
                volume=float(kwargs.get("volume", 1)),
                media_start_time=float(kwargs.get("media_start_time", 0)),
                has_audio=bool(kwargs.get("has_audio", False)),
                composition_id=kwargs.get("composition_src", ""),
                variable_values=kwargs.get("variable_values", {}),
            )
            comp = await svc.add_element(composition_id, el)
            if not comp:
                return {"error": f"Composition not found: {composition_id}"}
            return {"success": True, "element_id": el.id, "composition": comp.to_dict()}

        elif action == "remove_element":
            composition_id = kwargs.get("composition_id", "")
            element_id = kwargs.get("element_id", "")
            if not composition_id or not element_id:
                return {"error": "composition_id and element_id are required"}
            comp = await svc.remove_element(composition_id, element_id)
            if not comp:
                return {"error": f"Composition not found: {composition_id}"}
            return {"success": True, "composition": comp.to_dict()}

        elif action == "update_element":
            composition_id = kwargs.get("composition_id", "")
            element_id = kwargs.get("element_id", "")
            updates = kwargs.get("updates", {})
            if not composition_id or not element_id:
                return {"error": "composition_id and element_id are required"}
            comp = await svc.update_element(composition_id, element_id, updates)
            if not comp:
                return {"error": f"Composition not found: {composition_id}"}
            return {"success": True, "composition": comp.to_dict()}

        elif action == "add_zoom_keyframe":
            composition_id = kwargs.get("composition_id", "")
            if not composition_id:
                return {"error": "composition_id is required"}
            zk = StageZoomKeyframe(
                time=float(kwargs.get("zoom_time", kwargs.get("start_time", 0))),
                scale=float(kwargs.get("zoom_scale", 1)),
                focus_x=float(kwargs.get("focus_x", 960)),
                focus_y=float(kwargs.get("focus_y", 540)),
            )
            comp = await svc.add_zoom_keyframe(composition_id, zk)
            if not comp:
                return {"error": f"Composition not found: {composition_id}"}
            return {"success": True, "keyframe_id": zk.id, "composition": comp.to_dict()}

        elif action == "list_elements":
            composition_id = kwargs.get("composition_id", "")
            if not composition_id:
                return {"error": "composition_id is required"}
            comp = await svc.get_composition(composition_id)
            if not comp:
                return {"error": f"Composition not found: {composition_id}"}
            return {"success": True, "elements": [e.to_dict() for e in comp.elements]}

        elif action == "generate_html":
            composition_id = kwargs.get("composition_id", "")
            if not composition_id:
                return {"error": "composition_id is required"}
            return await svc.generate_html(composition_id)

        elif action == "render":
            composition_id = kwargs.get("composition_id", "")
            if not composition_id:
                return {"error": "composition_id is required"}
            return await svc.render_composition(
                composition_id=composition_id,
                fps=int(kwargs.get("fps", 30)),
                quality=kwargs.get("quality", "standard"),
                format=kwargs.get("format", "mp4"),
                output_path=kwargs.get("output_path"),
            )

        elif action == "preview":
            composition_id = kwargs.get("composition_id", "")
            if not composition_id:
                return {"error": "composition_id is required"}
            return await svc.preview_composition(composition_id)

        elif action == "lint":
            composition_id = kwargs.get("composition_id", "")
            if not composition_id:
                return {"error": "composition_id is required"}
            return await svc.lint_composition(composition_id)

        elif action == "list_compositions":
            comps = await svc.list_compositions()
            return {"success": True, "compositions": [c.to_dict() for c in comps]}

        elif action == "delete_composition":
            composition_id = kwargs.get("composition_id", "")
            if not composition_id:
                return {"error": "composition_id is required"}
            deleted = await svc.delete_composition(composition_id)
            return {"success": deleted}

        elif action == "get_composition":
            composition_id = kwargs.get("composition_id", "")
            if not composition_id:
                return {"error": "composition_id is required"}
            comp = await svc.get_composition(composition_id)
            if not comp:
                return {"error": f"Composition not found: {composition_id}"}
            return {"success": True, "composition": comp.to_dict()}

        return {"error": f"Unknown composition action: {action}"}

    async def _on_hibernate(self) -> None:
        pass


class CalculatorTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="calculator",
            description="Calculator operations: evaluate expressions, unit/currency conversion, formulas, history, percentage, base conversion, solve equations",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["evaluate", "convert_unit", "convert_currency",
                                 "formula", "history", "percentage", "base_convert",
                                 "solve", "graph", "statistics", "clear", "save"],
                        "description": "Calculator action to perform",
                    },
                    "expression": {"type": "string", "description": "Mathematical expression to evaluate"},
                    "from_unit": {"type": "string", "description": "Source unit for conversion"},
                    "to_unit": {"type": "string", "description": "Target unit for conversion"},
                    "value": {"type": "number", "description": "Numeric value"},
                    "from_currency": {"type": "string", "description": "Source currency code (e.g., USD)"},
                    "to_currency": {"type": "string", "description": "Target currency code (e.g., CNY)"},
                    "from_base": {"type": "integer", "description": "Source base (2-36)"},
                    "to_base": {"type": "integer", "description": "Target base (2-36)"},
                    "formula_name": {"type": "string", "description": "Formula name (e.g., quadratic, pythagorean)"},
                    "formula_params": {"type": "object", "description": "Formula parameters"},
                    "data": {"type": "array", "items": {"type": "number"}, "description": "Data array for statistics"},
                    "total": {"type": "number", "description": "Total for percentage calculation"},
                    "part": {"type": "number", "description": "Part for percentage calculation"},
                    "equation": {"type": "string", "description": "Equation to solve"},
                    "variable": {"type": "string", "description": "Variable to solve for"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "evaluate")
        try:
            if action == "evaluate":
                expr = kwargs.get("expression", "0")
                allowed_chars = set("0123456789+-*/.()%^ ")
                sanitized = "".join(c for c in expr if c in allowed_chars or c.isalpha())
                sanitized = sanitized.replace("^", "**")
                result = eval(sanitized, {"__builtins__": {}}, {})
                return {"result": result, "expression": expr}
            elif action == "convert_unit":
                from app.core.llm.dispatcher import ModelDispatcher
                from app.core.llm.gateway import llm_gateway
                from app.services.ai_workspace_service import AIWorkspaceService
                svc = AIWorkspaceService(ModelDispatcher(gateway=llm_gateway))
                return await svc.ai_calculator_assist(action="convert_unit", params=kwargs)
            elif action == "convert_currency":
                return {
                    "action": "workspace_command",
                    "app": "calculator",
                    "command": "convert_currency",
                    "value": kwargs.get("value", 0),
                    "from_currency": kwargs.get("from_currency", "USD"),
                    "to_currency": kwargs.get("to_currency", "CNY"),
                }
            elif action == "base_convert":
                value = kwargs.get("value", 0)
                from_base = kwargs.get("from_base", 10)
                to_base = kwargs.get("to_base", 2)
                if isinstance(value, (int, float)):
                    decimal_val = int(value)
                else:
                    decimal_val = int(str(value), from_base)
                return {"result": format(decimal_val, f"0{to_base}x" if to_base == 16 else "d"), "decimal": decimal_val}
            elif action == "percentage":
                total = kwargs.get("total", 100)
                part = kwargs.get("part", 0)
                return {"percentage": (part / total * 100) if total != 0 else 0, "part": part, "total": total}
            elif action == "statistics":
                data = kwargs.get("data", [])
                if not data:
                    return {"error": "No data provided"}
                n = len(data)
                mean = sum(data) / n
                variance = sum((x - mean) ** 2 for x in data) / n
                return {
                    "count": n, "sum": sum(data), "mean": mean,
                    "min": min(data), "max": max(data),
                    "variance": variance, "std_dev": variance ** 0.5,
                    "median": sorted(data)[n // 2],
                }
            elif action in ("solve", "formula", "graph"):
                from app.core.llm.dispatcher import ModelDispatcher
                from app.core.llm.gateway import llm_gateway
                from app.services.ai_workspace_service import AIWorkspaceService
                svc = AIWorkspaceService(ModelDispatcher(gateway=llm_gateway))
                return await svc.ai_calculator_assist(action=action, params=kwargs)
            else:
                return {
                    "action": "workspace_command",
                    "app": "calculator",
                    "command": action,
                }
        except Exception as e:
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        pass


class ContactsTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="contacts",
            description="Contacts management: list, search, add, edit, delete, group, import, export, merge, favorite, tag contacts",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["list", "search", "add", "edit", "delete",
                                 "group", "import", "export", "merge",
                                 "favorite", "tag", "detail", "add_to_group",
                                 "remove_from_group"],
                        "description": "Contacts action to perform",
                    },
                    "contact_id": {"type": "string", "description": "Contact ID"},
                    "name": {"type": "string", "description": "Contact name"},
                    "email": {"type": "string", "description": "Contact email"},
                    "phone": {"type": "string", "description": "Contact phone number"},
                    "company": {"type": "string", "description": "Company name"},
                    "title": {"type": "string", "description": "Job title"},
                    "address": {"type": "string", "description": "Contact address"},
                    "notes": {"type": "string", "description": "Contact notes"},
                    "query": {"type": "string", "description": "Search query"},
                    "group_name": {"type": "string", "description": "Group name"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags"},
                    "contact_ids": {"type": "array", "items": {"type": "string"}, "description": "Contact IDs for merge/batch"},
                    "export_format": {"type": "string", "enum": ["csv", "vcf", "json"], "description": "Export format"},
                    "import_path": {"type": "string", "description": "Import file path"},
                    "avatar_url": {"type": "string", "description": "Avatar URL"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "list")
        try:
            if action in ("merge", "add_to_group", "remove_from_group"):
                from app.core.llm.dispatcher import ModelDispatcher
                from app.core.llm.gateway import llm_gateway
                from app.services.ai_workspace_service import AIWorkspaceService
                svc = AIWorkspaceService(ModelDispatcher(gateway=llm_gateway))
                return await svc.ai_contacts_assist(action=action, params=kwargs)
            else:
                return {
                    "action": "workspace_command",
                    "app": "contacts",
                    "command": action,
                    "contact_id": kwargs.get("contact_id", ""),
                    "name": kwargs.get("name", ""),
                    "email": kwargs.get("email", ""),
                    "phone": kwargs.get("phone", ""),
                    "company": kwargs.get("company", ""),
                    "title": kwargs.get("title", ""),
                    "address": kwargs.get("address", ""),
                    "notes": kwargs.get("notes", ""),
                    "query": kwargs.get("query", ""),
                    "group_name": kwargs.get("group_name", ""),
                    "tags": kwargs.get("tags", []),
                    "contact_ids": kwargs.get("contact_ids", []),
                    "export_format": kwargs.get("export_format", "csv"),
                    "import_path": kwargs.get("import_path", ""),
                }
        except Exception as e:
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        pass


class WeatherTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="weather",
            description="Weather operations: search city, current weather, forecast, air quality, alerts, hourly, UV index, sunrise/sunset",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["search_city", "current", "forecast", "air_quality",
                                 "alert", "hourly", "uv_index", "sunrise",
                                 "moon_phase", "compare", "history", "radar"],
                        "description": "Weather action to perform",
                    },
                    "city": {"type": "string", "description": "City name"},
                    "latitude": {"type": "number", "description": "Latitude"},
                    "longitude": {"type": "number", "description": "Longitude"},
                    "forecast_days": {"type": "integer", "description": "Number of forecast days (1-16)"},
                    "language": {"type": "string", "description": "Language code (zh, en)"},
                    "compare_cities": {"type": "array", "items": {"type": "string"}, "description": "City names to compare"},
                    "date": {"type": "string", "description": "Date for history (YYYY-MM-DD)"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "current")
        try:
            from app.services.weather_service import weather_service
            if action == "search_city":
                results = await weather_service.search_city(
                    kwargs.get("city", ""), 5, kwargs.get("language", "zh")
                )
                return {"results": results}
            elif action == "current":
                lat = kwargs.get("latitude", 39.9042)
                lon = kwargs.get("longitude", 116.4074)
                return await weather_service.get_current_weather(lat, lon)
            elif action == "forecast":
                lat = kwargs.get("latitude", 39.9042)
                lon = kwargs.get("longitude", 116.4074)
                return await weather_service.get_forecast(
                    lat, lon, kwargs.get("forecast_days", 7)
                )
            elif action == "air_quality":
                lat = kwargs.get("latitude", 39.9042)
                lon = kwargs.get("longitude", 116.4074)
                return await weather_service.get_air_quality(lat, lon)
            elif action in ("alert", "hourly", "uv_index", "sunrise", "moon_phase", "compare", "history", "radar"):
                from app.core.llm.dispatcher import ModelDispatcher
                from app.core.llm.gateway import llm_gateway
                from app.services.ai_workspace_service import AIWorkspaceService
                svc = AIWorkspaceService(ModelDispatcher(gateway=llm_gateway))
                return await svc.ai_weather_assist(action=action, params=kwargs)
            return {"error": f"Unknown action: {action}"}
        except Exception as e:
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        pass


class FocusTimerTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="focus_timer",
            description="Focus timer operations: start/pause/stop focus sessions, track stats, configure settings, manage breaks, view history and streaks",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["start", "pause", "stop", "stats", "settings",
                                 "break", "history", "preset", "daily_report",
                                 "streak", "goal", "reminder"],
                        "description": "Focus timer action to perform",
                    },
                    "duration_minutes": {"type": "integer", "description": "Focus duration in minutes"},
                    "task_name": {"type": "string", "description": "Task name for focus session"},
                    "break_minutes": {"type": "integer", "description": "Break duration in minutes"},
                    "preset_name": {"type": "string", "description": "Preset name (pomodoro, deep_work, short_break)"},
                    "daily_goal_minutes": {"type": "integer", "description": "Daily focus goal in minutes"},
                    "date": {"type": "string", "description": "Date for history (YYYY-MM-DD)"},
                    "auto_start_break": {"type": "boolean", "description": "Auto start break after focus"},
                    "sound_enabled": {"type": "boolean", "description": "Enable notification sound"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "stats")
        try:
            if action in ("daily_report", "preset", "goal", "streak"):
                from app.core.llm.dispatcher import ModelDispatcher
                from app.core.llm.gateway import llm_gateway
                from app.services.ai_workspace_service import AIWorkspaceService
                svc = AIWorkspaceService(ModelDispatcher(gateway=llm_gateway))
                return await svc.ai_focus_assist(action=action, params=kwargs)
            else:
                return {
                    "action": "workspace_command",
                    "app": "focus_timer",
                    "command": action,
                    "duration_minutes": kwargs.get("duration_minutes", 25),
                    "task_name": kwargs.get("task_name", ""),
                    "break_minutes": kwargs.get("break_minutes", 5),
                    "preset_name": kwargs.get("preset_name", "pomodoro"),
                    "daily_goal_minutes": kwargs.get("daily_goal_minutes", 120),
                    "date": kwargs.get("date", ""),
                    "auto_start_break": kwargs.get("auto_start_break", True),
                    "sound_enabled": kwargs.get("sound_enabled", True),
                }
        except Exception as e:
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        pass


class MusicTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="music",
            description="Music player operations: play/pause, next/prev, manage playlists, search, volume control, lyrics, favorites, queue",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["play", "pause", "next", "prev", "playlist",
                                 "search", "volume", "lyrics", "favorite",
                                 "queue", "shuffle", "repeat", "create_playlist",
                                 "add_to_playlist", "remove_from_playlist", "info"],
                        "description": "Music action to perform",
                    },
                    "song_id": {"type": "string", "description": "Song ID"},
                    "song_name": {"type": "string", "description": "Song name"},
                    "artist": {"type": "string", "description": "Artist name"},
                    "playlist_id": {"type": "string", "description": "Playlist ID"},
                    "playlist_name": {"type": "string", "description": "Playlist name"},
                    "volume_level": {"type": "integer", "description": "Volume level (0-100)"},
                    "query": {"type": "string", "description": "Search query"},
                    "repeat_mode": {"type": "string", "enum": ["off", "one", "all"], "description": "Repeat mode"},
                    "position": {"type": "integer", "description": "Queue position"},
                    "album": {"type": "string", "description": "Album name"},
                    "genre": {"type": "string", "description": "Genre"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "info")
        try:
            if action in ("lyrics", "search", "create_playlist"):
                from app.core.llm.dispatcher import ModelDispatcher
                from app.core.llm.gateway import llm_gateway
                from app.services.ai_workspace_service import AIWorkspaceService
                svc = AIWorkspaceService(ModelDispatcher(gateway=llm_gateway))
                return await svc.ai_music_assist(action=action, params=kwargs)
            else:
                return {
                    "action": "workspace_command",
                    "app": "music",
                    "command": action,
                    "song_id": kwargs.get("song_id", ""),
                    "song_name": kwargs.get("song_name", ""),
                    "artist": kwargs.get("artist", ""),
                    "playlist_id": kwargs.get("playlist_id", ""),
                    "playlist_name": kwargs.get("playlist_name", ""),
                    "volume_level": kwargs.get("volume_level", 70),
                    "query": kwargs.get("query", ""),
                    "repeat_mode": kwargs.get("repeat_mode", "off"),
                    "position": kwargs.get("position", 0),
                    "album": kwargs.get("album", ""),
                    "genre": kwargs.get("genre", ""),
                }
        except Exception as e:
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        pass


class ScreenRecorderTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="screen_recorder",
            description="Screen recording operations: start/stop/pause recording, take screenshots, list recordings, trim, convert, analyze, share, configure settings",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["start", "stop", "pause", "resume", "screenshot",
                                 "list_recordings", "trim", "settings", "schedule",
                                 "annotate", "convert", "share", "delete", "analyze",
                                 "generate_thumbnail", "extract_text", "mix_narration",
                                 "generate_narration"],
                        "description": "Screen recorder action to perform",
                    },
                    "recording_id": {"type": "string", "description": "Recording ID"},
                    "start_time": {"type": "string", "description": "Trim start time (seconds)"},
                    "end_time": {"type": "string", "description": "Trim end time (seconds)"},
                    "output_format": {"type": "string", "enum": ["mp4", "webm", "gif", "avi"], "description": "Output format"},
                    "quality": {"type": "string", "enum": ["low", "medium", "high", "original"], "description": "Recording quality"},
                    "fps": {"type": "integer", "description": "Frames per second"},
                    "audio_enabled": {"type": "boolean", "description": "Enable audio recording"},
                    "region": {"type": "string", "description": "Screen region (x,y,width,height)"},
                    "schedule_time": {"type": "string", "description": "Scheduled recording time (ISO format)"},
                    "duration_minutes": {"type": "integer", "description": "Recording duration in minutes"},
                    "annotation_text": {"type": "string", "description": "Annotation text"},
                    "analyze_action": {"type": "string", "description": "AI analysis action: summarize_recording, extract_highlights, suggest_title, generate_chapters, extract_text"},
                    "limit": {"type": "integer", "description": "Number of recordings to list"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "list_recordings")
        try:
            if action == "list_recordings":
                return await self._list_recordings(kwargs.get("limit", 20))
            elif action in ("trim", "convert", "analyze", "generate_thumbnail", "share", "delete", "extract_text"):
                recording_id = kwargs.get("recording_id", "")
                if not recording_id:
                    return {"error": "recording_id is required for this action"}
                return await self._recording_action(recording_id, action, kwargs)
            elif action in ("annotate", "schedule"):
                from app.dependencies import container
                from app.services.ai_workspace_service import AIWorkspaceService
                dispatcher = container.get("model_dispatcher")
                svc = AIWorkspaceService(dispatcher) if dispatcher else None
                if svc:
                    return await svc.ai_recorder_assist(action=action, params=kwargs)
                return {"action": action, "params": kwargs}
            elif action == "generate_narration":
                text = kwargs.get("annotation_text", kwargs.get("text", ""))
                voice = kwargs.get("voice", "en-Carter_man")
                if not text:
                    return {"error": "Text is required for narration generation"}
                from app.services.tts_service import tts_service
                audio_data = await tts_service.generate(text, voice)
                return {"audio_size": len(audio_data), "format": "wav"}
            elif action == "mix_narration":
                recording_id = kwargs.get("recording_id", "")
                if not recording_id:
                    return {"error": "recording_id is required"}
                return await self._recording_action(recording_id, "mix_narration", kwargs)
            else:
                return {
                    "action": "workspace_command",
                    "app": "screen_recorder",
                    "command": action,
                    "recording_id": kwargs.get("recording_id", ""),
                    "quality": kwargs.get("quality", "high"),
                    "fps": kwargs.get("fps", 30),
                    "audio_enabled": kwargs.get("audio_enabled", True),
                    "region": kwargs.get("region", ""),
                }
        except Exception as e:
            return {"error": str(e)}

    async def _list_recordings(self, limit: int = 20) -> dict:
        from sqlalchemy import select

        from app.db.database import async_session
        from app.models.tables import Recording

        async with async_session() as session:
            result = await session.execute(
                select(Recording).order_by(Recording.created_at.desc()).limit(limit)
            )
            recordings = result.scalars().all()
            items = [
                {
                    "id": r.id,
                    "title": r.title,
                    "duration": r.duration,
                    "file_size": r.file_size,
                    "source_type": r.source_type,
                    "status": r.status,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in recordings
            ]
            return {"items": items, "count": len(items)}

    async def _recording_action(self, recording_id: str, action: str, kwargs: dict) -> dict:
        from app.db.database import async_session
        from app.models.tables import Recording
        from app.services.recorder_service import recorder_service

        async with async_session() as session:
            recording = await session.get(Recording, recording_id)
            if not recording:
                return {"error": f"Recording {recording_id} not found"}

            if action == "trim":
                start = float(kwargs.get("start_time", 0))
                end = float(kwargs.get("end_time", recording.duration))
                fmt = kwargs.get("output_format", "mp4")
                return await recorder_service.trim_recording(recording, start, end, fmt)

            elif action == "convert":
                fmt = kwargs.get("output_format", "mp4")
                quality = kwargs.get("quality", "high")
                return await recorder_service.convert_recording(recording, fmt, quality)

            elif action == "analyze":
                analyze_action = kwargs.get("analyze_action", "summarize_recording")
                return await recorder_service.analyze_recording(recording, analyze_action, kwargs)

            elif action == "extract_text":
                return await recorder_service.analyze_recording(recording, "extract_text", kwargs)

            elif action == "generate_thumbnail":
                return await recorder_service.generate_thumbnail(recording)

            elif action == "share":
                expires_hours = kwargs.get("duration_minutes", 1440) // 60
                from app.api.v1.recordings import share_recording
                return await share_recording(recording_id, max(1, expires_hours), db=session)

            elif action == "delete":
                await session.delete(recording)
                await session.commit()
                return {"deleted": True, "id": recording_id}

            elif action == "mix_narration":
                return {"message": "Use POST /api/v1/recordings/{id}/mix-narration with narration file upload"}

            return {"error": f"Unknown action: {action}"}

    async def _on_hibernate(self) -> None:
        pass


class FinanceTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="finance",
            description="Finance and accounting operations: record transactions, categorize, budget, reports, statistics, export",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["record", "list", "categorize", "budget",
                                 "report", "statistics", "export", "import",
                                 "delete", "summary", "trend", "category_list"],
                        "description": "Finance action to perform",
                    },
                    "transaction_id": {"type": "string", "description": "Transaction ID"},
                    "amount": {"type": "number", "description": "Transaction amount"},
                    "type": {"type": "string", "enum": ["income", "expense", "transfer"], "description": "Transaction type"},
                    "category": {"type": "string", "description": "Transaction category"},
                    "description": {"type": "string", "description": "Transaction description"},
                    "date": {"type": "string", "description": "Transaction date (YYYY-MM-DD)"},
                    "account": {"type": "string", "description": "Account name"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags"},
                    "start_date": {"type": "string", "description": "Start date for range query"},
                    "end_date": {"type": "string", "description": "End date for range query"},
                    "budget_amount": {"type": "number", "description": "Budget amount"},
                    "export_format": {"type": "string", "enum": ["csv", "xlsx", "pdf", "json"], "description": "Export format"},
                    "import_path": {"type": "string", "description": "Import file path"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "summary")
        try:
            if action in ("categorize", "budget", "report", "trend", "statistics"):
                from app.core.llm.dispatcher import ModelDispatcher
                from app.core.llm.gateway import llm_gateway
                from app.services.ai_workspace_service import AIWorkspaceService
                svc = AIWorkspaceService(ModelDispatcher(gateway=llm_gateway))
                return await svc.ai_finance_assist(action=action, params=kwargs)
            else:
                return {
                    "action": "workspace_command",
                    "app": "finance",
                    "command": action,
                    "transaction_id": kwargs.get("transaction_id", ""),
                    "amount": kwargs.get("amount", 0),
                    "type": kwargs.get("type", "expense"),
                    "category": kwargs.get("category", ""),
                    "description": kwargs.get("description", ""),
                    "date": kwargs.get("date", ""),
                    "account": kwargs.get("account", ""),
                    "tags": kwargs.get("tags", []),
                    "start_date": kwargs.get("start_date", ""),
                    "end_date": kwargs.get("end_date", ""),
                    "budget_amount": kwargs.get("budget_amount", 0),
                    "export_format": kwargs.get("export_format", "csv"),
                    "import_path": kwargs.get("import_path", ""),
                }
        except Exception as e:
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        pass


def register_workspace_tools():
    from app.core.tool.registry import tool_registry
    from app.core.tools.video_editor_tool import VideoEditorTool as ClipEditorTool
    tools = [
        DocumentTool(),
        PptTool(),
        ExcelTool(),
        NotesTool(),
        MindmapTool(),
        ReaderTool(),
        CodeEditorTool(),
        ImageEditorTool(),
        ClipEditorTool(),
        CalculatorTool(),
        ContactsTool(),
        WeatherTool(),
        FocusTimerTool(),
        MusicTool(),
        ScreenRecorderTool(),
        FinanceTool(),
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
    logger.info(f"Registered {len(registered)} workspace tools: {registered}")
    return registered
