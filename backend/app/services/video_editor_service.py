from __future__ import annotations

import asyncio
import json
import os
import shutil
import uuid
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import aiosqlite

FILTER_PRESETS: dict[str, dict[str, Any]] = {
    "none": {"label": "无", "css": ""},
    "grayscale": {"label": "黑白", "css": "filter: grayscale(100%);"},
    "sepia": {"label": "复古", "css": "filter: sepia(80%);"},
    "warm": {"label": "暖色", "css": "filter: sepia(30%) saturate(140%) brightness(105%);"},
    "cool": {"label": "冷色", "css": "filter: saturate(80%) brightness(105%) hue-rotate(10deg);"},
    "vintage": {"label": "怀旧", "css": "filter: sepia(40%) contrast(90%) brightness(95%) saturate(80%);"},
    "cinematic": {"label": "电影", "css": "filter: contrast(110%) saturate(85%) brightness(95%);"},
    "vivid": {"label": "鲜艳", "css": "filter: saturate(160%) contrast(110%);"},
    "fade": {"label": "褪色", "css": "filter: contrast(85%) brightness(110%) saturate(70%);"},
    "noir": {"label": "黑色电影", "css": "filter: grayscale(100%) contrast(130%) brightness(90%);"},
    "teal_orange": {"label": "青橙", "css": "filter: contrast(115%) saturate(120%) hue-rotate(-10deg);"},
    "dreamy": {"label": "梦幻", "css": "filter: brightness(110%) contrast(90%) saturate(120%) blur(0.5px);"},
    "high_contrast": {"label": "高对比", "css": "filter: contrast(150%) brightness(95%);"},
    "low_contrast": {"label": "低对比", "css": "filter: contrast(70%) brightness(105%);"},
    "portrait": {"label": "人像", "css": "filter: brightness(105%) contrast(95%) saturate(90%);"},
    "landscape_filter": {"label": "风景", "css": "filter: saturate(130%) contrast(105%) brightness(105%);"},
}

TRANSITION_PRESETS: dict[str, dict[str, Any]] = {
    "cut": {"label": "硬切", "type": "cut"},
    "fade": {"label": "淡入淡出", "type": "fade", "duration": 0.5},
    "dissolve": {"label": "溶解", "type": "dissolve", "duration": 0.5},
    "wipe_left": {"label": "左擦除", "type": "wipe", "direction": "left", "duration": 0.5},
    "wipe_right": {"label": "右擦除", "type": "wipe", "direction": "right", "duration": 0.5},
    "slide_left": {"label": "左滑", "type": "slide", "direction": "left", "duration": 0.5},
    "slide_right": {"label": "右滑", "type": "slide", "direction": "right", "duration": 0.5},
    "zoom_in": {"label": "放大", "type": "zoom", "direction": "in", "duration": 0.5},
    "zoom_out": {"label": "缩小", "type": "zoom", "direction": "out", "duration": 0.5},
    "blur": {"label": "模糊过渡", "type": "blur", "duration": 0.5},
}


@dataclass
class Keyframe:
    id: str = ""
    time: float = 0.0
    property_name: str = ""
    value: Any = None
    ease: str = "linear"

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "id": self.id,
            "time": self.time,
            "property": self.property_name,
            "value": self.value,
        }
        if self.ease != "linear":
            d["ease"] = self.ease
        return d


@dataclass
class TimelineElement:
    id: str = ""
    type: str = "video"
    name: str = ""
    start_time: float = 0.0
    duration: float = 5.0
    z_index: int = 0
    x: float = 0.0
    y: float = 0.0
    scale: float = 1.0
    opacity: float = 1.0
    rotation: float = 0.0
    src: str = ""
    content: str = ""
    color: str = "white"
    font_size: int = 48
    font_weight: int = 700
    font_family: str = "Inter"
    text_shadow: bool = True
    text_outline: bool = False
    text_outline_color: str = "#000000"
    text_outline_width: int = 2
    text_highlight: bool = False
    text_highlight_color: str = "yellow"
    text_highlight_padding: int = 4
    text_highlight_radius: int = 4
    volume: float = 1.0
    media_start_time: float = 0.0
    source_duration: float = 0.0
    has_audio: bool = False
    is_aroll: bool = False
    composition_id: str = ""
    source_width: int = 0
    source_height: int = 0
    variable_values: dict[str, Any] = field(default_factory=dict)
    keyframes: list[dict[str, Any]] = field(default_factory=list)
    filter_preset: str = ""
    filter_custom: str = ""
    transition_in: str = ""
    transition_out: str = ""
    transition_duration: float = 0.5
    speed: float = 1.0
    blur: float = 0.0
    brightness: float = 100.0
    contrast: float = 100.0
    saturation: float = 100.0
    hue_rotate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "startTime": self.start_time,
            "duration": self.duration,
            "zIndex": self.z_index,
        }
        if self.x != 0:
            d["x"] = self.x
        if self.y != 0:
            d["y"] = self.y
        if self.scale != 1:
            d["scale"] = self.scale
        if self.opacity != 1:
            d["opacity"] = self.opacity
        if self.rotation != 0:
            d["rotation"] = self.rotation
        if self.speed != 1:
            d["speed"] = self.speed
        if self.blur > 0:
            d["blur"] = self.blur
        if self.brightness != 100:
            d["brightness"] = self.brightness
        if self.contrast != 100:
            d["contrast"] = self.contrast
        if self.saturation != 100:
            d["saturation"] = self.saturation
        if self.hue_rotate != 0:
            d["hueRotate"] = self.hue_rotate
        if self.filter_preset:
            d["filterPreset"] = self.filter_preset
        if self.filter_custom:
            d["filterCustom"] = self.filter_custom
        if self.transition_in:
            d["transitionIn"] = self.transition_in
        if self.transition_out:
            d["transitionOut"] = self.transition_out
        if self.transition_duration != 0.5:
            d["transitionDuration"] = self.transition_duration

        if self.type in ("video", "image", "audio"):
            d["src"] = self.src
            if self.media_start_time > 0:
                d["mediaStartTime"] = self.media_start_time
            if self.source_duration > 0:
                d["sourceDuration"] = self.source_duration
            if self.volume != 1:
                d["volume"] = self.volume
            if self.type == "video" and self.has_audio:
                d["hasAudio"] = True
            if self.is_aroll:
                d["isAroll"] = True
            if self.source_width > 0:
                d["sourceWidth"] = self.source_width
            if self.source_height > 0:
                d["sourceHeight"] = self.source_height
        elif self.type == "text":
            d["content"] = self.content or self.name
            d["color"] = self.color
            d["fontSize"] = self.font_size
            d["fontWeight"] = self.font_weight
            d["fontFamily"] = self.font_family
            d["textShadow"] = self.text_shadow
            d["textOutline"] = self.text_outline
            if self.text_outline:
                d["textOutlineColor"] = self.text_outline_color
                d["textOutlineWidth"] = self.text_outline_width
            d["textHighlight"] = self.text_highlight
            if self.text_highlight:
                d["textHighlightColor"] = self.text_highlight_color
                d["textHighlightPadding"] = self.text_highlight_padding
                d["textHighlightRadius"] = self.text_highlight_radius
        elif self.type == "composition":
            d["src"] = self.src
            d["compositionId"] = self.composition_id
            if self.source_duration > 0:
                d["sourceDuration"] = self.source_duration
            if self.source_width > 0:
                d["sourceWidth"] = self.source_width
            if self.source_height > 0:
                d["sourceHeight"] = self.source_height
            if self.variable_values:
                d["variableValues"] = self.variable_values

        if self.keyframes:
            d["keyframes"] = self.keyframes

        return d

    def get_filter_css(self) -> str:
        parts = []
        if self.blur > 0:
            parts.append(f"blur({self.blur}px)")
        if self.brightness != 100:
            parts.append(f"brightness({self.brightness}%)")
        if self.contrast != 100:
            parts.append(f"contrast({self.contrast}%)")
        if self.saturation != 100:
            parts.append(f"saturate({self.saturation}%)")
        if self.hue_rotate != 0:
            parts.append(f"hue-rotate({self.hue_rotate}deg)")
        if self.filter_preset and self.filter_preset in FILTER_PRESETS:
            preset_css = FILTER_PRESETS[self.filter_preset].get("css", "")
            if preset_css and not parts:
                return preset_css
        if self.filter_custom:
            parts.append(self.filter_custom)
        if not parts:
            return ""
        return f"filter: {' '.join(parts)};"


@dataclass
class StageZoomKeyframe:
    id: str = ""
    time: float = 0.0
    scale: float = 1.0
    focus_x: float = 960.0
    focus_y: float = 540.0
    ease: str = ""

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "id": self.id,
            "time": self.time,
            "zoom": {"scale": self.scale, "focusX": self.focus_x, "focusY": self.focus_y},
        }
        if self.ease:
            d["ease"] = self.ease
        return d


@dataclass
class AssetItem:
    id: str = ""
    name: str = ""
    type: str = "sticker"
    category: str = ""
    src: str = ""
    thumbnail: str = ""
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    pack_id: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "category": self.category,
            "src": self.src,
            "thumbnail": self.thumbnail,
            "tags": self.tags,
            "metadata": self.metadata,
            "packId": self.pack_id,
            "createdAt": self.created_at,
        }


@dataclass
class AssetPack:
    pack_id: str = ""
    name: str = ""
    version: str = "1.0"
    author: str = ""
    description: str = ""
    items: list[AssetItem] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "packId": self.pack_id,
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "itemCount": len(self.items),
            "items": [i.to_dict() for i in self.items],
            "createdAt": self.created_at,
        }


@dataclass
class VideoComposition:
    composition_id: str = ""
    title: str = ""
    resolution: str = "landscape"
    total_duration: float = 10.0
    elements: list[TimelineElement] = field(default_factory=list)
    zoom_keyframes: list[StageZoomKeyframe] = field(default_factory=list)
    custom_styles: str = ""
    status: str = "draft"
    output_file: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "compositionId": self.composition_id,
            "title": self.title,
            "resolution": self.resolution,
            "totalDuration": self.total_duration,
            "elements": [e.to_dict() for e in self.elements],
            "zoomKeyframes": [z.to_dict() for z in self.zoom_keyframes],
            "customStyles": self.custom_styles,
            "status": self.status,
            "outputFile": self.output_file,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }


GSAP_CDN = "https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js"

CANVAS_DIMENSIONS = {
    "landscape": {"width": 1920, "height": 1080},
    "portrait": {"width": 1080, "height": 1920},
    "square": {"width": 1080, "height": 1080},
}

BASE_STYLES = """* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #000; overflow: hidden; }
video, img { display: block; }"""

ZOOM_CONTAINER_STYLES = "position: absolute; top: 0; left: 0; width: 100%; height: 100%; transform-origin: 0 0;"

FONT_WEIGHTS: dict[str, str] = {
    "Inter": "400;500;600;700;800;900",
    "Noto Sans SC": "400;500;700;900",
    "Noto Serif SC": "400;700;900",
    "Roboto": "400;500;700;900",
    "Montserrat": "400;500;600;700;800;900",
    "Poppins": "400;500;600;700;800;900",
    "Bebas Neue": "400",
    "Oswald": "400;500;600;700",
    "Anton": "400",
    "Playfair Display": "400;500;600;700;800;900",
    "Lora": "400;500;600;700",
    "Pacifico": "400",
    "Permanent Marker": "400",
    "Fira Code": "400;500;600;700",
}


def _generate_google_fonts_url(font_families: list[str]) -> str | None:
    families = [
        f"family={f.replace(' ', '+')}:wght@{FONT_WEIGHTS[f]}"
        for f in font_families
        if f in FONT_WEIGHTS
    ]
    if not families:
        return None
    return f"https://fonts.googleapis.com/css2?{'&'.join(families)}&display=swap"


def _sort_elements(elements: list[TimelineElement]) -> list[TimelineElement]:
    return sorted(elements, key=lambda e: (e.z_index, e.start_time))


def _generate_element_html(el: TimelineElement) -> str:
    base_attrs = [
        f'id="{el.id}"',
        f'data-start="{el.start_time}"',
        f'data-end="{el.start_time + el.duration}"',
        f'data-layer="{el.z_index}"',
        f'data-name="{el.name}"',
    ]
    if el.x != 0:
        base_attrs.append(f'data-x="{el.x}"')
    if el.y != 0:
        base_attrs.append(f'data-y="{el.y}"')
    if el.scale != 1:
        base_attrs.append(f'data-scale="{el.scale}"')
    if el.opacity != 1:
        base_attrs.append(f'data-opacity="{el.opacity}"')
    if el.rotation != 0:
        base_attrs.append(f'data-rotation="{el.rotation}"')
    if el.speed != 1:
        base_attrs.append(f'data-speed="{el.speed}"')
    if el.keyframes:
        kf_json = json.dumps(el.keyframes).replace("'", "&#39;")
        base_attrs.append(f"data-keyframes='{kf_json}'")
    if el.transition_in:
        base_attrs.append(f'data-transition-in="{el.transition_in}"')
    if el.transition_out:
        base_attrs.append(f'data-transition-out="{el.transition_out}"')
    if el.transition_duration != 0.5:
        base_attrs.append(f'data-transition-duration="{el.transition_duration}"')

    if el.type == "text":
        text_attrs = base_attrs + ['data-type="text"']
        if el.color:
            text_attrs.append(f'data-color="{el.color}"')
        if el.font_size:
            text_attrs.append(f'data-font-size="{el.font_size}"')
        if el.font_weight:
            text_attrs.append(f'data-font-weight="{el.font_weight}"')
        if el.font_family:
            text_attrs.append(f'data-font-family="{el.font_family}"')
        if not el.text_shadow:
            text_attrs.append('data-text-shadow="false"')
        if el.text_outline:
            text_attrs.append('data-text-outline="true"')
            text_attrs.append(f'data-text-outline-color="{el.text_outline_color}"')
            text_attrs.append(f'data-text-outline-width="{el.text_outline_width}"')
        if el.text_highlight:
            text_attrs.append('data-text-highlight="true"')
            text_attrs.append(f'data-text-highlight-color="{el.text_highlight_color}"')
            text_attrs.append(f'data-text-highlight-padding="{el.text_highlight_padding}"')
            text_attrs.append(f'data-text-highlight-radius="{el.text_highlight_radius}"')
        content = el.content or el.name
        return f'<div {" ".join(text_attrs)}><div>{content}</div></div>'

    if el.type == "composition":
        comp_attrs = base_attrs + [
            'data-type="composition"',
            f'data-composition-id="{el.composition_id}"',
        ]
        if el.source_duration > 0:
            comp_attrs.append(f'data-source-duration="{el.source_duration}"')
        if el.source_width > 0:
            comp_attrs.append(f'data-source-width="{el.source_width}"')
        if el.source_height > 0:
            comp_attrs.append(f'data-source-height="{el.source_height}"')
        if el.variable_values:
            var_json = json.dumps(el.variable_values).replace("'", "&#39;")
            comp_attrs.append(f"data-variable-values='{var_json}'")
        iframe_src = el.src.split("?")[0]
        if el.variable_values:
            params = "&".join(f"{k}={v}" for k, v in el.variable_values.items())
            iframe_src = f"{iframe_src}?{params}"
        return (
            f'<div {" ".join(comp_attrs)} style="width: 100%; height: 100%;">'
            f'<iframe src="{iframe_src}" sandbox="allow-scripts allow-same-origin" '
            f"style=\"width: 100%; height: 100%; border: none; pointer-events: none;\"></iframe>"
            f'<div class="composition-click-overlay" style="position: absolute; inset: 0; cursor: pointer;"></div>'
            f"</div>"
        )

    if el.type in ("video", "image", "audio"):
        if el.media_start_time > 0:
            base_attrs.append(f'data-media-start="{el.media_start_time}"')
        if el.source_duration > 0:
            base_attrs.append(f'data-source-duration="{el.source_duration}"')
        if el.is_aroll:
            base_attrs.append('data-aroll="true"')
        if el.volume != 1:
            base_attrs.append(f'data-volume="{el.volume}"')
        if el.type == "video" and el.has_audio:
            base_attrs.append('data-has-audio="true"')
        if el.filter_preset:
            base_attrs.append(f'data-filter-preset="{el.filter_preset}"')

    attrs = " ".join(base_attrs)
    if el.type == "video":
        return f'<video {attrs} src="{el.src}" playsinline></video>'
    elif el.type == "image":
        return f'<img {attrs} src="{el.src}" alt="{el.name}" />'
    elif el.type == "audio":
        return f'<audio {attrs} src="{el.src}"></audio>'
    return ""


def _generate_element_styles(el: TimelineElement) -> str:
    base = "position: absolute;"
    filter_css = el.get_filter_css()
    filter_style = f" {filter_css}" if filter_css else ""
    rotation_style = f" transform: rotate({el.rotation}deg);" if el.rotation != 0 else ""

    if el.type == "text":
        font_family = el.font_family or "Inter"
        font_size = el.font_size or 48
        font_weight = el.font_weight or 700
        color = el.color or "white"
        shadow = "text-shadow: 2px 2px 4px rgba(0,0,0,0.8);" if el.text_shadow else ""
        outline = ""
        if el.text_outline:
            ow = el.text_outline_width or 2
            oc = el.text_outline_color or "#000000"
            outline = f"-webkit-text-stroke: {ow}px {oc}; paint-order: stroke fill;"
        highlight = ""
        if el.text_highlight:
            pad = el.text_highlight_padding or 4
            highlight = (
                f"background-color: {el.text_highlight_color or 'yellow'}; "
                f"padding: {pad}px {int(pad * 1.5)}px; "
                f"border-radius: {el.text_highlight_radius or 4}px; "
                f"box-decoration-break: clone; -webkit-box-decoration-break: clone;"
            )
        return (
            f"    #{el.id} {{ {base} width: 100%; height: 100%; display: flex; "
            f"align-items: center; justify-content: center; pointer-events: none;{filter_style} }}\n"
            f"    #{el.id} > div {{ font-family: '{font_family}', sans-serif; "
            f"font-size: {font_size}px; font-weight: {font_weight}; color: {color}; "
            f"{shadow} {outline} {highlight} pointer-events: auto; cursor: grab; "
            f"white-space: pre-wrap; text-align: center; }}"
        )
    elif el.type == "video":
        return (
            f"    #{el.id} {{ {base} width: 100%; height: 100%; "
            f"object-fit: contain; transform-origin: center center;{filter_style}{rotation_style} }}"
        )
    elif el.type == "image":
        return (
            f"    #{el.id} {{ {base} max-width: 100%; max-height: 100%; "
            f"transform-origin: center center;{filter_style}{rotation_style} }}"
        )
    elif el.type == "audio":
        return f"    #{el.id} {{ {base} }}"
    elif el.type == "composition":
        return f"    #{el.id} {{ {base} width: 100%; height: 100%; position: absolute; }}"
    return ""


def _generate_gsap_script(
    elements: list[TimelineElement],
    total_duration: float,
    resolution: str = "landscape",
) -> str:
    sorted_els = _sort_elements(elements)
    has_media = any(e.type in ("video", "audio") for e in sorted_els)

    lines = ["    const tl = gsap.timeline({ paused: true });"]

    for el in sorted_els:
        if el.type in ("audio", "composition"):
            continue
        x_val = el.x
        y_val = el.y
        scale_val = el.scale if el.type in ("video", "image", "audio") else 1
        rotation_val = el.rotation if el.rotation != 0 else None
        set_props: dict[str, Any] = {}
        if x_val != 0 or y_val != 0:
            set_props["x"] = x_val
            set_props["y"] = y_val
        if scale_val != 1:
            set_props["scale"] = scale_val
        if rotation_val is not None:
            set_props["rotation"] = rotation_val
        if set_props:
            props_str = ", ".join(f"{k}: {v}" for k, v in set_props.items())
            lines.append(f"    tl.set('#{el.id}', {{ {props_str} }}, 0);")

    for el in sorted_els:
        start = el.start_time
        end = el.start_time + el.duration
        element_opacity = el.opacity
        lines.append(f"    tl.set('#{el.id}', {{ visibility: 'hidden' }}, 0);")
        if element_opacity != 1:
            lines.append(f"    tl.set('#{el.id}', {{ visibility: 'visible', opacity: {element_opacity} }}, {start});")
        else:
            lines.append(f"    tl.set('#{el.id}', {{ visibility: 'visible' }}, {start});")
        lines.append(f"    tl.set('#{el.id}', {{ visibility: 'hidden' }}, {end});")

        if el.transition_in and el.transition_in != "cut":
            td = el.transition_duration
            if el.transition_in == "fade":
                lines.append(
                    f"    tl.fromTo('#{el.id}', {{ opacity: 0 }}, "
                    f"{{ opacity: {element_opacity}, duration: {td} }}, {start});"
                )
            elif el.transition_in == "dissolve":
                lines.append(
                    f"    tl.fromTo('#{el.id}', {{ opacity: 0, scale: 1.05 }}, "
                    f"{{ opacity: {element_opacity}, scale: 1, duration: {td} }}, {start});"
                )

        if el.keyframes:
            for kf in el.keyframes:
                kf_time = kf.get("time", 0)
                kf_prop = kf.get("property", "")
                kf_val = kf.get("value")
                kf_ease = kf.get("ease", "none")
                if kf_prop and kf_val is not None:
                    ease_str = (
                        f", ease: '{kf_ease}'" if kf_ease != "none" else ""
                    )
                    lines.append(
                        f"    tl.to('#{el.id}', "
                        f"{{ {kf_prop}: {kf_val}, duration: 0.01{ease_str} }}, "
                        f"{kf_time});"
                    )

    if has_media:
        lines.append("""
    tl.eventCallback("onUpdate", function() {
      const time = tl.time();
      document.querySelectorAll("video[data-start], audio[data-start]").forEach(function(media) {
        const start = parseFloat(media.dataset.start);
        const end = parseFloat(media.dataset.end) || Infinity;
        const speed = parseFloat(media.dataset.speed) || 1;
        const mediaTime = (time - start) * speed;
        if (time >= start && time < end) {
          if (Math.abs(media.currentTime - mediaTime) > 0.1) {
            media.currentTime = mediaTime;
          }
          if (media.paused && !tl.paused()) {
            media.play().catch(function() {});
          }
        } else if (!media.paused) {
          media.pause();
        }
      });
    });""")

    return "\n".join(lines)


def generate_composition_html(composition: VideoComposition) -> str:
    dims = CANVAS_DIMENSIONS.get(composition.resolution, CANVAS_DIMENSIONS["landscape"])
    width, height = dims["width"], dims["height"]

    sorted_elements = _sort_elements(composition.elements)

    used_fonts: set[str] = set()
    for el in sorted_elements:
        if el.type == "text" and el.font_family:
            used_fonts.add(el.font_family)
    used_fonts.add("Inter")
    google_fonts_url = _generate_google_fonts_url(list(used_fonts))

    google_fonts_link = ""
    if google_fonts_url:
        google_fonts_link = (
            f'  <link data-hf-fonts="true" rel="preconnect" href="https://fonts.googleapis.com">\n'
            f'  <link data-hf-fonts="true" rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
            f'  <link data-hf-fonts="true" href="{google_fonts_url}" rel="stylesheet">'
        )

    element_styles = "\n".join(_generate_element_styles(el) for el in sorted_elements)
    stage_css = (
        f"#stage {{ position: relative; width: {width}px; height: {height}px; "
        f"overflow: hidden; background: #fff; }}"
    )
    zoom_css = f"#stage-zoom-container {{ {ZOOM_CONTAINER_STYLES} }}"
    core_css = f"{BASE_STYLES}\n{stage_css}\n{zoom_css}\n{element_styles}"

    custom_css = composition.custom_styles.strip() if composition.custom_styles else ""

    elements_html = "\n      ".join(_generate_element_html(el) for el in sorted_elements)

    zoom_kf_attr = ""
    if composition.zoom_keyframes:
        zoom_json = json.dumps([z.to_dict() for z in composition.zoom_keyframes]).replace("'", "&#39;")
        zoom_kf_attr = f" data-zoom-keyframes='{zoom_json}'"

    custom_styles_attr = ""
    if composition.custom_styles:
        cs_json = json.dumps(composition.custom_styles).replace("'", "&#39;")
        custom_styles_attr = f" data-custom-styles='{cs_json}'"

    gsap_script = _generate_gsap_script(
        sorted_elements, composition.total_duration, composition.resolution,
    )

    custom_style_tag = ""
    if custom_css:
        custom_style_tag = "  <style data-hf-custom=\"true\">\n    " + custom_css + "\n  </style>"

    html_attrs = (
        f'data-composition-id="{composition.composition_id}" '
        f'data-composition-duration="{composition.total_duration}" '
        f'data-resolution="{composition.resolution}"{custom_styles_attr}'
    )

    return f"""<!DOCTYPE html>
<html {html_attrs}>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  {google_fonts_link}
  <script src="{GSAP_CDN}"></script>
  <style data-hf-core="true">
    {core_css}
  </style>
{custom_style_tag}
</head>
<body>
  <div id="stage">
    <div id="stage-zoom-container"{zoom_kf_attr}>
      {elements_html}
    </div>
  </div>
  <script>
{gsap_script}
  </script>
</body>
</html>"""


class HyperframesCLI:
    def __init__(self, project_dir: str | None = None) -> None:
        self._hyperframes_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "hyperframes-0.4.42",
        )
        self._node_path = shutil.which("node") or shutil.which("node.exe")
        self._npx_path = shutil.which("npx") or shutil.which("npx.cmd")
        self._project_dir = project_dir or os.path.join(
            os.getcwd(), "data", "clip_editor", "hyperframes_projects",
        )

    @property
    def available(self) -> bool:
        return self._node_path is not None and os.path.isdir(self._hyperframes_dir)

    async def render(
        self,
        project_dir: str,
        output_path: str | None = None,
        fps: int = 30,
        quality: str = "standard",
        format: str = "mp4",
    ) -> dict[str, Any]:
        if not self.available:
            return {"error": "Node.js 或 hyperframes 未安装"}

        out = output_path or os.path.join(
            self._project_dir, f"render_{uuid.uuid4().hex[:8]}.{format}",
        )

        try:
            cmd = [
                self._npx_path, "hyperframes", "render",
                "--fps", str(fps),
                "--quality", quality,
                "--format", format,
                "--output", out,
            ]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=project_dir,
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=600.0)
            if process.returncode == 0:
                return {"success": True, "output_file": out, "output": stdout.decode(errors="replace")}
            return {"error": f"渲染失败: {stderr.decode(errors='replace')}"}
        except asyncio.TimeoutError:
            return {"error": "渲染超时 (10分钟限制)"}
        except Exception as e:
            return {"error": str(e)}

    async def preview(self, project_dir: str, port: int = 3210) -> dict[str, Any]:
        if not self.available:
            return {"error": "Node.js 或 hyperframes 未安装"}

        try:
            cmd = [self._npx_path, "hyperframes", "preview", "--port", str(port)]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=project_dir,
            )
            await asyncio.sleep(3)
            return {"success": True, "url": f"http://localhost:{port}", "pid": process.pid}
        except Exception as e:
            return {"error": str(e)}

    async def lint(self, project_dir: str) -> dict[str, Any]:
        if not self.available:
            return {"error": "Node.js 或 hyperframes 未安装"}

        try:
            cmd = [self._npx_path, "hyperframes", "lint"]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=project_dir,
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)
            output = stdout.decode(errors="replace") + stderr.decode(errors="replace")
            if process.returncode == 0:
                return {"success": True, "output": output}
            return {"success": False, "output": output, "errors": output}
        except Exception as e:
            return {"error": str(e)}


class ClipEditorService:
    def __init__(self, data_dir: str | None = None) -> None:
        if data_dir is None:
            data_dir = os.path.join(os.getcwd(), "data", "clip_editor")
        self._data_dir = data_dir
        self._projects_dir = os.path.join(data_dir, "projects")
        self._assets_dir = os.path.join(data_dir, "assets")
        self._compositions: dict[str, VideoComposition] = {}
        self._asset_packs: dict[str, AssetPack] = {}
        self._cli = HyperframesCLI()
        self._db_path = os.path.join(data_dir, "clip_editor.db")
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(self._projects_dir, exist_ok=True)
        os.makedirs(self._assets_dir, exist_ok=True)
        os.makedirs(os.path.join(self._assets_dir, "stickers"), exist_ok=True)
        os.makedirs(os.path.join(self._assets_dir, "music"), exist_ok=True)
        os.makedirs(os.path.join(self._assets_dir, "effects"), exist_ok=True)
        os.makedirs(os.path.join(self._assets_dir, "transitions"), exist_ok=True)
        os.makedirs(os.path.join(self._assets_dir, "fonts"), exist_ok=True)

    @property
    def hyperframes_available(self) -> bool:
        return self._cli.available

    def _composition_project_dir(self, composition_id: str) -> str:
        return os.path.join(self._projects_dir, composition_id)

    async def create_composition(
        self,
        title: str,
        resolution: str = "landscape",
        total_duration: float = 10.0,
    ) -> VideoComposition:
        comp_id = f"comp-{uuid.uuid4().hex[:12]}"
        comp = VideoComposition(
            composition_id=comp_id,
            title=title,
            resolution=resolution,
            total_duration=total_duration,
        )
        self._compositions[comp_id] = comp
        await self._save_composition(comp)
        return comp

    async def get_composition(self, composition_id: str) -> VideoComposition | None:
        if composition_id in self._compositions:
            return self._compositions[composition_id]
        return await self._load_composition(composition_id)

    async def list_compositions(self) -> list[VideoComposition]:
        return sorted(self._compositions.values(), key=lambda c: c.updated_at, reverse=True)

    async def delete_composition(self, composition_id: str) -> bool:
        if composition_id in self._compositions:
            del self._compositions[composition_id]
        try:
            async with aiosqlite.connect(self._db_path) as db:
                await db.execute(
                    "DELETE FROM compositions WHERE composition_id = ?",
                    (composition_id,),
                )
                await db.commit()
        except Exception:
            pass
        project_dir = self._composition_project_dir(composition_id)
        if os.path.isdir(project_dir):
            shutil.rmtree(project_dir, ignore_errors=True)
        return True

    async def add_element(
        self, composition_id: str, element: TimelineElement,
    ) -> VideoComposition | None:
        comp = await self.get_composition(composition_id)
        if not comp:
            return None
        if not element.id:
            element.id = f"el-{uuid.uuid4().hex[:8]}"
        comp.elements.append(element)
        comp.updated_at = datetime.now().isoformat()
        await self._save_composition(comp)
        return comp

    async def remove_element(
        self, composition_id: str, element_id: str,
    ) -> VideoComposition | None:
        comp = await self.get_composition(composition_id)
        if not comp:
            return None
        comp.elements = [e for e in comp.elements if e.id != element_id]
        comp.updated_at = datetime.now().isoformat()
        await self._save_composition(comp)
        return comp

    async def update_element(
        self,
        composition_id: str,
        element_id: str,
        updates: dict[str, Any],
    ) -> VideoComposition | None:
        comp = await self.get_composition(composition_id)
        if not comp:
            return None
        _key_map = {
            "startTime": "start_time", "zIndex": "z_index",
            "fontSize": "font_size", "fontWeight": "font_weight",
            "fontFamily": "font_family", "textShadow": "text_shadow",
            "textOutline": "text_outline", "textHighlight": "text_highlight",
            "mediaStartTime": "media_start_time", "sourceDuration": "source_duration",
            "hasAudio": "has_audio", "isAroll": "is_aroll",
            "compositionId": "composition_id", "sourceWidth": "source_width",
            "sourceHeight": "source_height", "variableValues": "variable_values",
            "filterPreset": "filter_preset", "filterCustom": "filter_custom",
            "transitionIn": "transition_in", "transitionOut": "transition_out",
            "transitionDuration": "transition_duration", "hueRotate": "hue_rotate",
        }
        for el in comp.elements:
            if el.id == element_id:
                for key, value in updates.items():
                    attr = _key_map.get(key, key)
                    if hasattr(el, attr):
                        setattr(el, attr, value)
                break
        comp.updated_at = datetime.now().isoformat()
        await self._save_composition(comp)
        return comp

    async def add_keyframe(
        self,
        composition_id: str,
        element_id: str,
        keyframe: Keyframe,
    ) -> VideoComposition | None:
        comp = await self.get_composition(composition_id)
        if not comp:
            return None
        for el in comp.elements:
            if el.id == element_id:
                if not keyframe.id:
                    keyframe.id = f"kf-{uuid.uuid4().hex[:8]}"
                el.keyframes.append(keyframe.to_dict())
                break
        comp.updated_at = datetime.now().isoformat()
        await self._save_composition(comp)
        return comp

    async def remove_keyframe(
        self,
        composition_id: str,
        element_id: str,
        keyframe_id: str,
    ) -> VideoComposition | None:
        comp = await self.get_composition(composition_id)
        if not comp:
            return None
        for el in comp.elements:
            if el.id == element_id:
                el.keyframes = [kf for kf in el.keyframes if kf.get("id") != keyframe_id]
                break
        comp.updated_at = datetime.now().isoformat()
        await self._save_composition(comp)
        return comp

    async def add_zoom_keyframe(
        self, composition_id: str, keyframe: StageZoomKeyframe,
    ) -> VideoComposition | None:
        comp = await self.get_composition(composition_id)
        if not comp:
            return None
        if not keyframe.id:
            keyframe.id = f"zk-{uuid.uuid4().hex[:8]}"
        comp.zoom_keyframes.append(keyframe)
        comp.updated_at = datetime.now().isoformat()
        await self._save_composition(comp)
        return comp

    async def apply_filter(
        self,
        composition_id: str,
        element_id: str,
        filter_preset: str,
        adjustments: dict[str, Any] | None = None,
    ) -> VideoComposition | None:
        comp = await self.get_composition(composition_id)
        if not comp:
            return None
        for el in comp.elements:
            if el.id == element_id:
                if filter_preset in FILTER_PRESETS:
                    el.filter_preset = filter_preset
                if adjustments:
                    for k, v in adjustments.items():
                        if hasattr(el, k):
                            setattr(el, k, v)
                break
        comp.updated_at = datetime.now().isoformat()
        await self._save_composition(comp)
        return comp

    async def ai_color_grade(
        self,
        composition_id: str,
        element_id: str,
        style: str = "cinematic",
        reference_image: str | None = None,
    ) -> dict[str, Any]:
        comp = await self.get_composition(composition_id)
        if not comp:
            return {"error": f"合成未找到: {composition_id}"}

        target_el = None
        for el in comp.elements:
            if el.id == element_id:
                target_el = el
                break
        if not target_el:
            return {"error": f"元素未找到: {element_id}"}

        style_presets: dict[str, dict[str, Any]] = {
            "cinematic": {"contrast": 110, "saturation": 85, "brightness": 95},
            "vintage": {"contrast": 90, "saturation": 70, "brightness": 95, "sepia": True},
            "vivid": {"contrast": 115, "saturation": 150, "brightness": 105},
            "noir": {"contrast": 130, "saturation": 0, "brightness": 90},
            "warm": {"contrast": 105, "saturation": 120, "brightness": 105, "hue_rotate": -5},
            "cool": {"contrast": 105, "saturation": 90, "brightness": 105, "hue_rotate": 10},
            "dreamy": {"contrast": 90, "saturation": 110, "brightness": 110, "blur": 0.5},
            "portrait": {"contrast": 95, "saturation": 90, "brightness": 105},
            "landscape_grade": {"contrast": 110, "saturation": 130, "brightness": 105},
        }

        preset = style_presets.get(style, style_presets["cinematic"])
        for k, v in preset.items():
            if k == "sepia" and v:
                target_el.filter_preset = "sepia"
            elif hasattr(target_el, k):
                setattr(target_el, k, v)

        comp.updated_at = datetime.now().isoformat()
        await self._save_composition(comp)

        return {
            "success": True,
            "style": style,
            "adjustments": preset,
            "element_id": element_id,
        }

    async def import_asset_pack(self, zip_path: str) -> dict[str, Any]:
        if not os.path.isfile(zip_path):
            return {"error": f"文件不存在: {zip_path}"}
        if not zipfile.is_zipfile(zip_path):
            return {"error": "不是有效的ZIP文件"}

        pack_id = f"pack-{uuid.uuid4().hex[:8]}"
        pack_dir = os.path.join(self._assets_dir, pack_id)
        os.makedirs(pack_dir, exist_ok=True)

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(pack_dir)

            manifest_path = os.path.join(pack_dir, "manifest.json")
            if not os.path.isfile(manifest_path):
                shutil.rmtree(pack_dir, ignore_errors=True)
                return {"error": "ZIP根目录缺少 manifest.json 声明文件"}

            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            pack_name = manifest.get("name", "未命名素材包")
            pack_version = manifest.get("version", "1.0")
            pack_author = manifest.get("author", "")
            pack_description = manifest.get("description", "")
            items_data = manifest.get("items", [])

            if not items_data:
                shutil.rmtree(pack_dir, ignore_errors=True)
                return {"error": "manifest.json 中没有素材项"}

            items: list[AssetItem] = []
            for item_data in items_data:
                item_id = f"asset-{uuid.uuid4().hex[:8]}"
                item_src = item_data.get("src", "")
                abs_src = os.path.join(pack_dir, item_src) if item_src else ""
                if item_src and not os.path.isfile(abs_src):
                    continue

                item = AssetItem(
                    id=item_id,
                    name=item_data.get("name", "未命名"),
                    type=item_data.get("type", "sticker"),
                    category=item_data.get("category", ""),
                    src=abs_src,
                    thumbnail=item_data.get("thumbnail", ""),
                    tags=item_data.get("tags", []),
                    metadata=item_data.get("metadata", {}),
                    pack_id=pack_id,
                )
                items.append(item)

            pack = AssetPack(
                pack_id=pack_id,
                name=pack_name,
                version=pack_version,
                author=pack_author,
                description=pack_description,
                items=items,
            )
            self._asset_packs[pack_id] = pack
            await self._save_asset_pack(pack)

            return {
                "success": True,
                "pack_id": pack_id,
                "name": pack_name,
                "item_count": len(items),
            }
        except json.JSONDecodeError:
            shutil.rmtree(pack_dir, ignore_errors=True)
            return {"error": "manifest.json 格式错误"}
        except Exception as e:
            shutil.rmtree(pack_dir, ignore_errors=True)
            return {"error": str(e)}

    async def list_asset_packs(self) -> list[AssetPack]:
        return list(self._asset_packs.values())

    async def list_assets(
        self,
        asset_type: str | None = None,
        category: str | None = None,
    ) -> list[AssetItem]:
        items: list[AssetItem] = []
        for pack in self._asset_packs.values():
            for item in pack.items:
                if asset_type and item.type != asset_type:
                    continue
                if category and item.category != category:
                    continue
                items.append(item)
        return items

    async def delete_asset_pack(self, pack_id: str) -> bool:
        if pack_id in self._asset_packs:
            del self._asset_packs[pack_id]
        pack_dir = os.path.join(self._assets_dir, pack_id)
        if os.path.isdir(pack_dir):
            shutil.rmtree(pack_dir, ignore_errors=True)
        return True

    def get_filter_presets(self) -> dict[str, dict[str, Any]]:
        return FILTER_PRESETS

    def get_transition_presets(self) -> dict[str, dict[str, Any]]:
        return TRANSITION_PRESETS

    async def generate_html(self, composition_id: str) -> dict[str, Any]:
        comp = await self.get_composition(composition_id)
        if not comp:
            return {"error": f"合成未找到: {composition_id}"}

        html = generate_composition_html(comp)

        project_dir = self._composition_project_dir(composition_id)
        os.makedirs(project_dir, exist_ok=True)
        html_path = os.path.join(project_dir, "index.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

        return {
            "success": True,
            "html": html,
            "html_path": html_path,
            "project_dir": project_dir,
        }

    async def render_composition(
        self,
        composition_id: str,
        fps: int = 30,
        quality: str = "standard",
        format: str = "mp4",
        output_path: str | None = None,
    ) -> dict[str, Any]:
        comp = await self.get_composition(composition_id)
        if not comp:
            return {"error": f"合成未找到: {composition_id}"}

        gen_result = await self.generate_html(composition_id)
        if not gen_result.get("success"):
            return gen_result

        project_dir = gen_result["project_dir"]

        if not self._cli.available:
            return await self._render_via_ffmpeg(
                comp, project_dir, fps, quality, format, output_path,
            )

        out = output_path or os.path.join(
            self._data_dir, f"render_{uuid.uuid4().hex[:8]}.{format}",
        )
        result = await self._cli.render(project_dir, out, fps=fps, quality=quality, format=format)

        if result.get("success"):
            comp.status = "rendered"
            comp.output_file = result["output_file"]
            comp.updated_at = datetime.now().isoformat()
            await self._save_composition(comp)

        return result

    async def _render_via_ffmpeg(
        self,
        comp: VideoComposition,
        project_dir: str,
        fps: int,
        quality: str,
        format: str,
        output_path: str | None = None,
    ) -> dict[str, Any]:
        from app.services.video_service import video_service

        video_elements = [e for e in comp.elements if e.type == "video"]
        if not video_elements:
            return {"error": "没有视频元素可渲染，且 hyperframes CLI 不可用"}

        if len(video_elements) == 1:
            el = video_elements[0]
            if el.media_start_time > 0 or el.duration < el.source_duration:
                return await video_service.trim(
                    el.src, el.media_start_time, el.media_start_time + el.duration,
                )
            return {"success": True, "output_file": el.src}

        file_list = []
        for el in sorted(video_elements, key=lambda e: e.start_time):
            if el.src not in file_list:
                file_list.append(el.src)

        if len(file_list) >= 2:
            return await video_service.merge(file_list)

        return {"error": "无法在无 hyperframes 的情况下渲染此合成"}

    async def preview_composition(
        self, composition_id: str, port: int = 3210,
    ) -> dict[str, Any]:
        gen_result = await self.generate_html(composition_id)
        if not gen_result.get("success"):
            return gen_result
        return await self._cli.preview(gen_result["project_dir"], port)

    async def lint_composition(self, composition_id: str) -> dict[str, Any]:
        gen_result = await self.generate_html(composition_id)
        if not gen_result.get("success"):
            return gen_result
        return await self._cli.lint(gen_result["project_dir"])

    async def _save_composition(self, comp: VideoComposition) -> None:
        try:
            async with aiosqlite.connect(self._db_path) as db:
                await db.execute(
                    """INSERT OR REPLACE INTO compositions
                       (composition_id, title, resolution, total_duration, elements,
                        zoom_keyframes, custom_styles, status, output_file,
                        created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        comp.composition_id,
                        comp.title,
                        comp.resolution,
                        comp.total_duration,
                        json.dumps([e.to_dict() for e in comp.elements]),
                        json.dumps([z.to_dict() for z in comp.zoom_keyframes]),
                        comp.custom_styles,
                        comp.status,
                        comp.output_file,
                        comp.created_at,
                        comp.updated_at,
                    ),
                )
                await db.commit()
        except Exception:
            pass

    async def _load_composition(self, composition_id: str) -> VideoComposition | None:
        try:
            async with aiosqlite.connect(self._db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM compositions WHERE composition_id = ?",
                    (composition_id,),
                ) as cursor:
                    row = await cursor.fetchone()
                    if row is None:
                        return None

                    elements = _parse_elements(json.loads(row["elements"]))
                    zoom_kfs = _parse_zoom_keyframes(json.loads(row["zoom_keyframes"]))

                    comp = VideoComposition(
                        composition_id=row["composition_id"],
                        title=row["title"],
                        resolution=row["resolution"],
                        total_duration=row["total_duration"],
                        elements=elements,
                        zoom_keyframes=zoom_kfs,
                        custom_styles=row["custom_styles"],
                        status=row["status"],
                        output_file=row["output_file"],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                    )
                    self._compositions[composition_id] = comp
                    return comp
        except Exception:
            return None

    async def _save_asset_pack(self, pack: AssetPack) -> None:
        try:
            async with aiosqlite.connect(self._db_path) as db:
                await db.execute(
                    """INSERT OR REPLACE INTO asset_packs
                       (pack_id, name, version, author, description,
                        items, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        pack.pack_id,
                        pack.name,
                        pack.version,
                        pack.author,
                        pack.description,
                        json.dumps([i.to_dict() for i in pack.items]),
                        pack.created_at,
                    ),
                )
                await db.commit()
        except Exception:
            pass


def _parse_elements(elements_data: list[dict]) -> list[TimelineElement]:
    elements = []
    for ed in elements_data:
        el = TimelineElement()
        el.id = ed.get("id", "")
        el.type = ed.get("type", "video")
        el.name = ed.get("name", "")
        el.start_time = ed.get("startTime", 0)
        el.duration = ed.get("duration", 5)
        el.z_index = ed.get("zIndex", 0)
        el.x = ed.get("x", 0)
        el.y = ed.get("y", 0)
        el.scale = ed.get("scale", 1)
        el.opacity = ed.get("opacity", 1)
        el.rotation = ed.get("rotation", 0)
        el.src = ed.get("src", "")
        el.content = ed.get("content", "")
        el.color = ed.get("color", "white")
        el.font_size = ed.get("fontSize", 48)
        el.font_weight = ed.get("fontWeight", 700)
        el.font_family = ed.get("fontFamily", "Inter")
        el.text_shadow = ed.get("textShadow", True)
        el.text_outline = ed.get("textOutline", False)
        el.text_outline_color = ed.get("textOutlineColor", "#000000")
        el.text_outline_width = ed.get("textOutlineWidth", 2)
        el.text_highlight = ed.get("textHighlight", False)
        el.text_highlight_color = ed.get("textHighlightColor", "yellow")
        el.text_highlight_padding = ed.get("textHighlightPadding", 4)
        el.text_highlight_radius = ed.get("textHighlightRadius", 4)
        el.volume = ed.get("volume", 1)
        el.media_start_time = ed.get("mediaStartTime", 0)
        el.source_duration = ed.get("sourceDuration", 0)
        el.has_audio = ed.get("hasAudio", False)
        el.is_aroll = ed.get("isAroll", False)
        el.composition_id = ed.get("compositionId", "")
        el.source_width = ed.get("sourceWidth", 0)
        el.source_height = ed.get("sourceHeight", 0)
        el.variable_values = ed.get("variableValues", {})
        el.keyframes = ed.get("keyframes", [])
        el.filter_preset = ed.get("filterPreset", "")
        el.filter_custom = ed.get("filterCustom", "")
        el.transition_in = ed.get("transitionIn", "")
        el.transition_out = ed.get("transitionOut", "")
        el.transition_duration = ed.get("transitionDuration", 0.5)
        el.speed = ed.get("speed", 1)
        el.blur = ed.get("blur", 0)
        el.brightness = ed.get("brightness", 100)
        el.contrast = ed.get("contrast", 100)
        el.saturation = ed.get("saturation", 100)
        el.hue_rotate = ed.get("hueRotate", 0)
        elements.append(el)
    return elements


def _parse_zoom_keyframes(data: list[dict]) -> list[StageZoomKeyframe]:
    kfs = []
    for zd in data:
        zoom = zd.get("zoom", {})
        zk = StageZoomKeyframe(
            id=zd.get("id", ""),
            time=zd.get("time", 0),
            scale=zoom.get("scale", 1),
            focus_x=zoom.get("focusX", 960),
            focus_y=zoom.get("focusY", 540),
            ease=zd.get("ease", ""),
        )
        kfs.append(zk)
    return kfs


clip_editor_service = ClipEditorService()

video_editor_service = clip_editor_service
