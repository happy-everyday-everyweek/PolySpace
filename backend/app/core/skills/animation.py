import logging
import uuid
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

_ANIMATION_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  body {{ margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; height: 100vh;
    overflow: hidden; font-family: system-ui, -apple-system, sans-serif;
    background-color: {bg_color}; }}
  .container {{ position: relative; width: {width}px; height: {height}px; display: flex; justify-content: center; align-items: center; }}
  svg {{ width: 100%; height: 100%; overflow: visible; }}
  .controls {{ position: absolute; bottom: 20px; display: flex; gap: 10px; z-index: 10; }}
  button {{ padding: 8px 16px; background: white; border: 1px solid #333; border-radius: 4px; cursor: pointer; font-size: 13px; }}
  #status {{ position: absolute; bottom: 60px; font-size: 13px; background: rgba(255,255,255,0.9); padding: 4px 12px; border-radius: 4px; display: none; }}
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
</head>
<body>
<div class="container">
  {svg_content}
</div>
<div id="status">Exporting...</div>
<div class="controls">
  <button onclick="playAnimation()">Replay</button>
  <button onclick="exportGIF()">Export GIF</button>
</div>
<script>
  let tl;
  function initAnimation() {{
    const scene = document.querySelector("#scene") || document.querySelector("svg");
    const paths = Array.from(document.querySelectorAll("path"));
    const groups = Array.from(document.querySelectorAll("g"));
    const elements = paths.length > 0 ? paths : groups;
    const hull = elements[0];
    const parts = elements.slice(1);
    gsap.set([scene, ...elements], {{ transformOrigin: "50% 50%" }});
    {init_logic}
    tl = gsap.timeline({{ paused: true }});
    {timeline_logic}
  }}
  function playAnimation() {{ if (tl) tl.kill(); initAnimation(); tl.play(); }}
  async function exportGIF() {{
    document.getElementById('status').style.display = 'block';
    document.getElementById('status').textContent = 'Recording... (this may take a moment)';
    const canvas = document.createElement('canvas');
    canvas.width = {width}; canvas.height = {height};
    const ctx = canvas.getContext('2d');
    const data = {{ frames: [] }};
    const svgEl = document.querySelector('svg');
    const totalFrames = Math.round({duration} * 30);
    for (let i = 0; i <= totalFrames; i++) {{
      tl.progress(i / totalFrames);
      await new Promise(r => requestAnimationFrame(r));
      const svgData = new XMLSerializer().serializeToString(svgEl);
      const img = new Image();
      const blob = new Blob([svgData], {{ type: 'image/svg+xml;charset=utf-8' }});
      const url = URL.createObjectURL(blob);
      await new Promise((resolve) => {{ img.onload = resolve; img.src = url; }});
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      URL.revokeObjectURL(url);
      data.frames.push(canvas.toDataURL('image/png'));
    }}
    document.getElementById('status').textContent = 'Frames captured! Sending to server...';
    try {{
      const resp = await fetch('/api/v1/ai/coordination/skills/animation/export', {{
        method: 'POST', headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ frames: data.frames.length, title: '{title}', format: 'gif' }})
      }});
      const result = await resp.json();
      document.getElementById('status').textContent = result.message || 'Export initiated';
    }} catch(e) {{
      document.getElementById('status').textContent = 'Export: ' + e.message;
    }}
    setTimeout(() => {{ document.getElementById('status').style.display = 'none'; }}, 3000);
  }}
  initAnimation(); tl.play();
</script>
</body>
</html>"""


@dataclass
class AnimationStyle:
    name: str = "standard"
    duration: float = 1.2
    ease: str = "back.out(2)"
    stagger: float = 0.012
    rotation: float = 0
    scale_from: float = 0.1
    scale_to: float = 1.0
    overshoot: float = 2.0


PRESET_STYLES = {
    "standard": AnimationStyle(name="standard", duration=1.2, ease="back.out(2)", stagger=0.012),
    "power": AnimationStyle(name="power", duration=0.7, ease="back.out(5)", stagger=0.008, rotation=-360, overshoot=5.0),
    "elegant": AnimationStyle(name="elegant", duration=1.5, ease="power4.out", stagger=0.02),
    "bounce": AnimationStyle(name="bounce", duration=1.0, ease="elastic.out(1, 0.5)", stagger=0.015),
    "fast": AnimationStyle(name="fast", duration=0.4, ease="power2.out", stagger=0.005),
    "slow_reveal": AnimationStyle(name="slow_reveal", duration=2.0, ease="power3.inOut", stagger=0.03, scale_from=0.01),
}


@dataclass
class AnimationProject:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "Untitled Animation"
    svg_content: str = ""
    style: str = "standard"
    width: int = 600
    height: int = 600
    bg_color: str = "#f4f4f5"
    duration: float = 3.0
    created_at: float = field(default_factory=lambda: __import__("time").time())


class SkillEngine:
    def __init__(self, output_dir: str | Path | None = None):
        if output_dir is None:
            from app.config import settings
            output_dir = Path(settings.DATA_DIR) / "animations"
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._projects: dict[str, AnimationProject] = {}

    def create_animation(
        self,
        svg_content: str,
        title: str = "Animation",
        style: str = "standard",
        width: int = 600,
        height: int = 600,
        bg_color: str = "#f4f4f5",
        duration: float = 3.0,
    ) -> AnimationProject:
        project = AnimationProject(
            title=title,
            svg_content=svg_content,
            style=style,
            width=width,
            height=height,
            bg_color=bg_color,
            duration=duration,
        )
        self._projects[project.id] = project
        return project

    def render_to_html(self, project_id: str) -> str | None:
        project = self._projects.get(project_id)
        if not project:
            return None

        style = PRESET_STYLES.get(project.style, PRESET_STYLES["standard"])
        init_logic = self._build_init_logic(style)
        timeline_logic = self._build_timeline_logic(project, style)

        html = _ANIMATION_TEMPLATE.format(
            title=project.title,
            bg_color=project.bg_color,
            width=project.width,
            height=project.height,
            svg_content=project.svg_content,
            init_logic=init_logic,
            timeline_logic=timeline_logic,
            duration=project.duration,
        )

        output_path = self._output_dir / f"{project.id}.html"
        output_path.write_text(html, encoding="utf-8")
        return str(output_path)

    def _build_init_logic(self, style: AnimationStyle) -> str:
        return f"""
    const hull = paths[0]; const parts = paths.slice(1);
    gsap.set(hull, {{ opacity: 0, scale: {style.scale_from} }});
    parts.forEach(part => {{
      const angle = Math.random() * Math.PI * 2;
      const distance = 8000 + Math.random() * 10000;
      gsap.set(part, {{ opacity: 0, x: Math.cos(angle) * distance, y: Math.sin(angle) * distance, scaleX: 0.05, scaleY: 4, rotation: 90 }});
    }});"""

    def _build_timeline_logic(self, project: AnimationProject, style: AnimationStyle) -> str:
        return f"""
    tl.fromTo(scene, {{ rotation: {style.rotation}, scale: {style.scale_from} }}, {{ rotation: 0, scale: {style.scale_to}, duration: {project.duration}, ease: "power4.out" }}, 0);
    tl.to(hull, {{ opacity: 1, scale: 1, duration: {style.duration * 1.2}, ease: "elastic.out(1, 0.5)" }}, 0.2);
    tl.to(parts, {{ opacity: 1, x: 0, y: 0, scaleX: 1, scaleY: 1, rotation: 0, duration: {style.duration}, stagger: {{ each: {style.stagger}, from: "random" }}, ease: "{style.ease}" }}, 0.5);"""

    def list_styles(self) -> list[dict]:
        return [
            {"name": s.name, "duration": s.duration, "ease": s.ease, "stagger": s.stagger, "rotation": s.rotation}
            for s in PRESET_STYLES.values()
        ]

    def get_project(self, project_id: str) -> dict | None:
        project = self._projects.get(project_id)
        if not project:
            return None
        return {
            "id": project.id, "title": project.title, "style": project.style,
            "width": project.width, "height": project.height, "duration": project.duration,
        }

    def list_projects(self) -> list[dict]:
        return [
            {"id": p.id, "title": p.title, "style": p.style, "duration": p.duration}
            for p in self._projects.values()
        ]


_skill_engine: SkillEngine | None = None


def get_skill_engine() -> SkillEngine:
    global _skill_engine
    if _skill_engine is None:
        _skill_engine = SkillEngine()
    return _skill_engine
