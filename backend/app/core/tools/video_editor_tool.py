from __future__ import annotations

import logging
from typing import Any

from app.core.tool.base import BaseTool

logger = logging.getLogger(__name__)


class VideoEditorTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="clip_editor",
            description=(
                "基于 Hyperframes 的视频剪辑器。支持合成编辑、时间轴元素管理、"
                "关键帧动画、滤镜预设、AI调色、转场效果、素材库导入。"
                "同时支持 FFmpeg 基础操作（裁剪/分割/合并/变速等）。"
            ),
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "create_composition", "add_video", "add_image", "add_text",
                            "add_audio", "add_composition", "remove_element", "update_element",
                            "add_keyframe", "remove_keyframe", "add_zoom_keyframe",
                            "list_elements", "generate_html", "render", "preview", "lint",
                            "list_compositions", "delete_composition", "get_composition",
                            "apply_filter", "ai_color_grade",
                            "import_asset_pack", "list_assets", "list_asset_packs",
                            "delete_asset_pack",
                            "get_filter_presets", "get_transition_presets",
                            "trim", "split", "merge", "add_effect", "add_subtitle",
                            "audio_extract", "thumbnail", "info", "convert", "speed",
                            "add_text_overlay", "analyze",
                        ],
                        "description": "剪辑器操作类型",
                    },
                    "composition_id": {"type": "string", "description": "合成ID"},
                    "title": {"type": "string", "description": "合成标题"},
                    "resolution": {
                        "type": "string",
                        "enum": ["landscape", "portrait", "square"],
                        "description": "画布分辨率: landscape=1920x1080, portrait=1080x1920, square=1080x1080",
                    },
                    "total_duration": {"type": "number", "description": "总时长（秒）"},
                    "element_id": {"type": "string", "description": "时间轴元素ID"},
                    "element_name": {"type": "string", "description": "元素名称"},
                    "src": {"type": "string", "description": "源文件路径或URL"},
                    "start_time": {"type": "number", "description": "起始时间（秒）"},
                    "duration": {"type": "number", "description": "时长（秒）"},
                    "end_time": {"type": "number", "description": "结束时间（秒）"},
                    "z_index": {"type": "integer", "description": "图层顺序"},
                    "x": {"type": "number", "description": "X坐标"},
                    "y": {"type": "number", "description": "Y坐标"},
                    "scale": {"type": "number", "description": "缩放比例"},
                    "opacity": {"type": "number", "description": "透明度 0-1"},
                    "rotation": {"type": "number", "description": "旋转角度（度）"},
                    "content": {"type": "string", "description": "文本内容"},
                    "color": {"type": "string", "description": "文本颜色"},
                    "font_size": {"type": "integer", "description": "字号（像素）"},
                    "font_weight": {"type": "integer", "description": "字重"},
                    "font_family": {"type": "string", "description": "字体"},
                    "volume": {"type": "number", "description": "音量 0-1"},
                    "media_start_time": {"type": "number", "description": "媒体偏移（秒）"},
                    "has_audio": {"type": "boolean", "description": "是否含音频"},
                    "updates": {"type": "object", "description": "元素更新属性"},
                    "keyframe_id": {"type": "string", "description": "关键帧ID"},
                    "property_name": {"type": "string", "description": "关键帧属性名"},
                    "value": {"type": "string", "description": "关键帧属性值"},
                    "ease": {
                        "type": "string",
                        "enum": ["linear", "easeIn", "easeOut", "easeInOut", "back", "elastic"],
                        "description": "缓动函数",
                    },
                    "zoom_scale": {"type": "number", "description": "缩放倍数"},
                    "focus_x": {"type": "number", "description": "缩放焦点X"},
                    "focus_y": {"type": "number", "description": "缩放焦点Y"},
                    "filter_preset": {
                        "type": "string",
                        "enum": [
                            "none", "grayscale", "sepia", "warm", "cool", "vintage",
                            "cinematic", "vivid", "fade", "noir", "teal_orange",
                            "dreamy", "high_contrast", "low_contrast", "portrait",
                            "landscape_filter",
                        ],
                        "description": "滤镜预设",
                    },
                    "adjustments": {
                        "type": "object",
                        "description": "滤镜微调参数: brightness/contrast/saturation/blur/hue_rotate",
                    },
                    "style": {
                        "type": "string",
                        "enum": [
                            "cinematic", "vintage", "vivid", "noir", "warm", "cool",
                            "dreamy", "portrait", "landscape_grade",
                        ],
                        "description": "AI调色风格",
                    },
                    "transition_in": {
                        "type": "string",
                        "enum": [
                            "cut", "fade", "dissolve", "wipe_left", "wipe_right",
                            "slide_left", "slide_right", "zoom_in", "zoom_out", "blur",
                        ],
                        "description": "入场转场",
                    },
                    "transition_out": {
                        "type": "string",
                        "enum": [
                            "cut", "fade", "dissolve", "wipe_left", "wipe_right",
                            "slide_left", "slide_right", "zoom_in", "zoom_out", "blur",
                        ],
                        "description": "出场转场",
                    },
                    "transition_duration": {"type": "number", "description": "转场时长（秒）"},
                    "zip_path": {"type": "string", "description": "素材包ZIP路径"},
                    "asset_type": {
                        "type": "string",
                        "enum": ["sticker", "music", "effect", "transition", "font", "background"],
                        "description": "素材类型",
                    },
                    "category": {"type": "string", "description": "素材分类"},
                    "fps": {"type": "integer", "enum": [24, 30, 60], "description": "渲染帧率"},
                    "quality": {
                        "type": "string",
                        "enum": ["draft", "standard", "high", "low", "medium"],
                        "description": "渲染质量",
                    },
                    "format": {"type": "string", "enum": ["mp4", "webm", "mov"], "description": "输出格式"},
                    "output_path": {"type": "string", "description": "输出路径"},
                    "file_path": {"type": "string", "description": "文件路径"},
                    "file_paths": {"type": "array", "items": {"type": "string"}, "description": "多文件路径"},
                    "split_time": {"type": "number", "description": "分割点（秒）"},
                    "effect_name": {
                        "type": "string",
                        "enum": ["fade_in", "fade_out", "blur", "grayscale", "sepia", "vignette", "noise"],
                        "description": "特效名称",
                    },
                    "subtitle_text": {"type": "string", "description": "字幕文本"},
                    "speed_factor": {"type": "number", "description": "变速倍率"},
                    "export_format": {
                        "type": "string",
                        "enum": ["mp4", "webm", "avi", "gif", "mov"],
                        "description": "导出格式",
                    },
                    "text_content": {"type": "string", "description": "文字叠加内容"},
                    "text_position": {
                        "type": "string",
                        "enum": ["top", "center", "bottom"],
                        "description": "文字位置",
                    },
                    "custom_styles": {"type": "string", "description": "自定义CSS样式"},
                },
                "required": ["action"],
            },
        )

    async def _on_activate(self) -> None:
        pass

    async def _on_call(self, **kwargs) -> Any:
        action = kwargs.get("action", "")
        try:
            composition_actions = {
                "create_composition", "add_video", "add_image", "add_text",
                "add_audio", "add_composition", "remove_element", "update_element",
                "add_keyframe", "remove_keyframe", "add_zoom_keyframe",
                "list_elements", "generate_html", "render", "preview", "lint",
                "list_compositions", "delete_composition", "get_composition",
                "apply_filter", "ai_color_grade",
                "import_asset_pack", "list_assets", "list_asset_packs",
                "delete_asset_pack", "get_filter_presets", "get_transition_presets",
            }

            if action in composition_actions:
                return await self._composition_action(action, kwargs)

            ffmpeg_actions = {
                "trim", "split", "merge", "add_effect", "add_subtitle",
                "audio_extract", "thumbnail", "info", "convert", "speed",
                "add_text_overlay", "analyze",
            }
            if action in ffmpeg_actions:
                return await self._ffmpeg_action(action, kwargs)

            return {"error": f"未知操作: {action}"}
        except Exception as e:
            logger.exception("ClipEditorTool error for action %s", action)
            return {"error": str(e)}

    async def _on_hibernate(self) -> None:
        pass

    def _get_service(self):
        from app.services.video_editor_service import clip_editor_service
        return clip_editor_service

    async def _composition_action(self, action: str, kwargs: dict) -> Any:
        from app.services.video_editor_service import (
            Keyframe,
            StageZoomKeyframe,
            TimelineElement,
            clip_editor_service,
        )

        svc = clip_editor_service

        if action == "create_composition":
            comp = await svc.create_composition(
                title=kwargs.get("title", "未命名"),
                resolution=kwargs.get("resolution", "landscape"),
                total_duration=kwargs.get("total_duration", 10.0),
            )
            return {"success": True, "composition": comp.to_dict()}

        elif action in ("add_video", "add_image", "add_text", "add_audio", "add_composition"):
            composition_id = kwargs.get("composition_id", "")
            if not composition_id:
                return {"error": "需要 composition_id"}
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
                rotation=float(kwargs.get("rotation", 0)),
                src=kwargs.get("src", ""),
                content=kwargs.get("content", ""),
                color=kwargs.get("color", "white"),
                font_size=int(kwargs.get("font_size", 48)),
                font_weight=int(kwargs.get("font_weight", 700)),
                font_family=kwargs.get("font_family", "Inter"),
                volume=float(kwargs.get("volume", 1)),
                media_start_time=float(kwargs.get("media_start_time", 0)),
                has_audio=bool(kwargs.get("has_audio", False)),
                filter_preset=kwargs.get("filter_preset", ""),
                transition_in=kwargs.get("transition_in", ""),
                transition_out=kwargs.get("transition_out", ""),
                transition_duration=float(kwargs.get("transition_duration", 0.5)),
                speed=float(kwargs.get("speed", 1)),
                brightness=float(kwargs.get("brightness", 100)),
                contrast=float(kwargs.get("contrast", 100)),
                saturation=float(kwargs.get("saturation", 100)),
                hue_rotate=float(kwargs.get("hue_rotate", 0)),
                blur=float(kwargs.get("blur", 0)),
            )
            comp = await svc.add_element(composition_id, el)
            if not comp:
                return {"error": f"合成未找到: {composition_id}"}
            return {"success": True, "element_id": el.id, "composition": comp.to_dict()}

        elif action == "remove_element":
            composition_id = kwargs.get("composition_id", "")
            element_id = kwargs.get("element_id", "")
            if not composition_id or not element_id:
                return {"error": "需要 composition_id 和 element_id"}
            comp = await svc.remove_element(composition_id, element_id)
            if not comp:
                return {"error": f"合成未找到: {composition_id}"}
            return {"success": True, "composition": comp.to_dict()}

        elif action == "update_element":
            composition_id = kwargs.get("composition_id", "")
            element_id = kwargs.get("element_id", "")
            updates = kwargs.get("updates", {})
            if not composition_id or not element_id:
                return {"error": "需要 composition_id 和 element_id"}
            comp = await svc.update_element(composition_id, element_id, updates)
            if not comp:
                return {"error": f"合成未找到: {composition_id}"}
            return {"success": True, "composition": comp.to_dict()}

        elif action == "add_keyframe":
            composition_id = kwargs.get("composition_id", "")
            element_id = kwargs.get("element_id", "")
            if not composition_id or not element_id:
                return {"error": "需要 composition_id 和 element_id"}
            kf = Keyframe(
                time=float(kwargs.get("start_time", 0)),
                property_name=kwargs.get("property_name", ""),
                value=kwargs.get("value"),
                ease=kwargs.get("ease", "linear"),
            )
            comp = await svc.add_keyframe(composition_id, element_id, kf)
            if not comp:
                return {"error": f"合成未找到: {composition_id}"}
            return {"success": True, "keyframe_id": kf.id, "composition": comp.to_dict()}

        elif action == "remove_keyframe":
            composition_id = kwargs.get("composition_id", "")
            element_id = kwargs.get("element_id", "")
            keyframe_id = kwargs.get("keyframe_id", "")
            if not all([composition_id, element_id, keyframe_id]):
                return {"error": "需要 composition_id, element_id 和 keyframe_id"}
            comp = await svc.remove_keyframe(composition_id, element_id, keyframe_id)
            if not comp:
                return {"error": f"合成未找到: {composition_id}"}
            return {"success": True, "composition": comp.to_dict()}

        elif action == "add_zoom_keyframe":
            composition_id = kwargs.get("composition_id", "")
            if not composition_id:
                return {"error": "需要 composition_id"}
            zk = StageZoomKeyframe(
                time=float(kwargs.get("zoom_time", kwargs.get("start_time", 0))),
                scale=float(kwargs.get("zoom_scale", 1)),
                focus_x=float(kwargs.get("focus_x", 960)),
                focus_y=float(kwargs.get("focus_y", 540)),
            )
            comp = await svc.add_zoom_keyframe(composition_id, zk)
            if not comp:
                return {"error": f"合成未找到: {composition_id}"}
            return {"success": True, "keyframe_id": zk.id, "composition": comp.to_dict()}

        elif action == "apply_filter":
            composition_id = kwargs.get("composition_id", "")
            element_id = kwargs.get("element_id", "")
            filter_preset = kwargs.get("filter_preset", "")
            if not composition_id or not element_id:
                return {"error": "需要 composition_id 和 element_id"}
            comp = await svc.apply_filter(
                composition_id, element_id, filter_preset,
                kwargs.get("adjustments"),
            )
            if not comp:
                return {"error": f"合成未找到: {composition_id}"}
            return {"success": True, "composition": comp.to_dict()}

        elif action == "ai_color_grade":
            composition_id = kwargs.get("composition_id", "")
            element_id = kwargs.get("element_id", "")
            if not composition_id or not element_id:
                return {"error": "需要 composition_id 和 element_id"}
            return await svc.ai_color_grade(
                composition_id, element_id,
                style=kwargs.get("style", "cinematic"),
                reference_image=kwargs.get("reference_image"),
            )

        elif action == "import_asset_pack":
            zip_path = kwargs.get("zip_path", "")
            if not zip_path:
                return {"error": "需要 zip_path"}
            return await svc.import_asset_pack(zip_path)

        elif action == "list_assets":
            return {
                "success": True,
                "assets": [
                    a.to_dict() for a in await svc.list_assets(
                        asset_type=kwargs.get("asset_type"),
                        category=kwargs.get("category"),
                    )
                ],
            }

        elif action == "list_asset_packs":
            packs = await svc.list_asset_packs()
            return {"success": True, "packs": [p.to_dict() for p in packs]}

        elif action == "delete_asset_pack":
            pack_id = kwargs.get("pack_id", "")
            if not pack_id:
                return {"error": "需要 pack_id"}
            deleted = await svc.delete_asset_pack(pack_id)
            return {"success": deleted}

        elif action == "get_filter_presets":
            return {"success": True, "presets": svc.get_filter_presets()}

        elif action == "get_transition_presets":
            return {"success": True, "presets": svc.get_transition_presets()}

        elif action == "list_elements":
            composition_id = kwargs.get("composition_id", "")
            if not composition_id:
                return {"error": "需要 composition_id"}
            comp = await svc.get_composition(composition_id)
            if not comp:
                return {"error": f"合成未找到: {composition_id}"}
            return {"success": True, "elements": [e.to_dict() for e in comp.elements]}

        elif action == "generate_html":
            composition_id = kwargs.get("composition_id", "")
            if not composition_id:
                return {"error": "需要 composition_id"}
            return await svc.generate_html(composition_id)

        elif action == "render":
            composition_id = kwargs.get("composition_id", "")
            if not composition_id:
                return {"error": "需要 composition_id"}
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
                return {"error": "需要 composition_id"}
            return await svc.preview_composition(composition_id)

        elif action == "lint":
            composition_id = kwargs.get("composition_id", "")
            if not composition_id:
                return {"error": "需要 composition_id"}
            return await svc.lint_composition(composition_id)

        elif action == "list_compositions":
            comps = await svc.list_compositions()
            return {"success": True, "compositions": [c.to_dict() for c in comps]}

        elif action == "delete_composition":
            composition_id = kwargs.get("composition_id", "")
            if not composition_id:
                return {"error": "需要 composition_id"}
            deleted = await svc.delete_composition(composition_id)
            return {"success": deleted}

        elif action == "get_composition":
            composition_id = kwargs.get("composition_id", "")
            if not composition_id:
                return {"error": "需要 composition_id"}
            comp = await svc.get_composition(composition_id)
            if not comp:
                return {"error": f"合成未找到: {composition_id}"}
            return {"success": True, "composition": comp.to_dict()}

        return {"error": f"未知合成操作: {action}"}

    async def _ffmpeg_action(self, action: str, kwargs: dict) -> Any:
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
            return await svc.ai_generate_subtitles(kwargs.get("subtitle_text", ""), "zh")
        elif action == "trim":
            return await video_service.trim(
                kwargs.get("file_path", ""),
                float(kwargs.get("start_time", 0)),
                float(kwargs.get("end_time", 0)),
            )
        elif action == "merge":
            return await video_service.merge(kwargs.get("file_paths", []))
        elif action == "split":
            return await video_service.split(
                kwargs.get("file_path", ""),
                float(kwargs.get("split_time", 0)),
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
                float(kwargs.get("start_time", 1)),
            )
        elif action == "info":
            return await video_service.get_info(kwargs.get("file_path", ""))
        elif action == "convert":
            return await video_service.convert(
                kwargs.get("file_path", ""),
                kwargs.get("export_format", "mp4"),
                kwargs.get("quality", "medium"),
            )
        return {"error": f"未知 FFmpeg 操作: {action}"}
