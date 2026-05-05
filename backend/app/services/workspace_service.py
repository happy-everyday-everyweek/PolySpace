from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class WorkspaceDocument:
    doc_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    doc_type: str = "note"
    content: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkspaceRecommendation:
    title: str
    description: str
    action_type: str = "tool"
    action_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkspaceEncouragement:
    message: str
    category: str = "general"
    context_aware: bool = False
    related_tool: str = ""
    tone: str = "warm"


WORKSPACE_CONTEXT_MAP: dict[str, dict[str, Any]] = {
    "document": {
        "label": "文档编辑",
        "actions": ["撰写", "编辑", "润色", "整理思路"],
        "encouragement_angles": ["写作进度", "内容质量", "思路清晰度"],
    },
    "video": {
        "label": "视频编辑",
        "actions": ["剪辑", "调色", "添加字幕", "编排片段"],
        "encouragement_angles": ["创作进度", "视觉效果", "叙事节奏"],
    },
    "ppt": {
        "label": "演示文稿",
        "actions": ["设计幻灯片", "排版", "添加内容", "准备演讲"],
        "encouragement_angles": ["设计美感", "内容逻辑", "演示准备"],
    },
    "excel": {
        "label": "电子表格",
        "actions": ["数据分析", "公式计算", "图表制作", "数据清洗"],
        "encouragement_angles": ["数据洞察", "分析深度", "效率提升"],
    },
    "calendar": {
        "label": "日程管理",
        "actions": ["安排日程", "解决冲突", "设置提醒", "规划时间"],
        "encouragement_angles": ["时间管理", "规划能力", "效率提升"],
    },
    "knowledge": {
        "label": "知识库",
        "actions": ["搜索知识", "整理文档", "提取信息", "构建知识体系"],
        "encouragement_angles": ["知识积累", "信息整合", "学习深度"],
    },
    "todo": {
        "label": "待办事项",
        "actions": ["管理任务", "排列优先级", "分解任务", "追踪进度"],
        "encouragement_angles": ["任务推进", "执行效率", "目标达成"],
    },
    "memo": {
        "label": "备忘录",
        "actions": ["记录想法", "整理笔记", "提取要点", "分类归档"],
        "encouragement_angles": ["记录习惯", "思维整理", "灵感捕捉"],
    },
    "email": {
        "label": "邮件处理",
        "actions": ["撰写邮件", "回复消息", "分类整理", "提取任务"],
        "encouragement_angles": ["沟通效率", "信息处理", "响应及时"],
    },
    "kanban": {
        "label": "看板管理",
        "actions": ["追踪进度", "分配任务", "识别瓶颈", "优化流程"],
        "encouragement_angles": ["项目管理", "流程优化", "团队协作"],
    },
    "recorder": {
        "label": "屏幕录制",
        "actions": ["录制屏幕", "制作教程", "捕获操作", "保存记录"],
        "encouragement_angles": ["内容创作", "知识分享", "记录留存"],
    },
}

FALLBACK_ENCOURAGEMENTS: list[WorkspaceEncouragement] = [
    WorkspaceEncouragement("你正在稳步前进，每一步都算数！", "progress", False, "", "warm"),
    WorkspaceEncouragement("保持专注，你离目标越来越近了。", "focus", False, "", "calm"),
    WorkspaceEncouragement("工作节奏不错，记得适时休息。", "wellness", False, "", "caring"),
    WorkspaceEncouragement("你的努力正在积累，继续加油！", "motivation", False, "", "energetic"),
    WorkspaceEncouragement("认真工作的你最有魅力。", "praise", False, "", "warm"),
    WorkspaceEncouragement("每完成一个小任务，都是一次进步。", "progress", False, "", "encouraging"),
    WorkspaceEncouragement("保持这份投入感，成果会说话的。", "motivation", False, "", "confident"),
    WorkspaceEncouragement("今天的状态很棒，好好利用它！", "praise", False, "", "energetic"),
]


class WorkspaceService:
    def __init__(self, data_dir: str | None = None) -> None:
        if data_dir is None:
            data_dir = os.path.join(os.getcwd(), "data", "workspace")
        self._data_dir = data_dir
        self._documents: dict[str, WorkspaceDocument] = {}
        os.makedirs(data_dir, exist_ok=True)

    async def create_document(self, title: str, doc_type: str = "note", content: str = "", **metadata: Any) -> WorkspaceDocument:
        doc = WorkspaceDocument(title=title, doc_type=doc_type, content=content, metadata=metadata)
        self._documents[doc.doc_id] = doc
        return doc

    async def get_document(self, doc_id: str) -> WorkspaceDocument | None:
        return self._documents.get(doc_id)

    async def update_document(self, doc_id: str, **updates: Any) -> WorkspaceDocument | None:
        doc = self._documents.get(doc_id)
        if not doc:
            return None
        for key, value in updates.items():
            if hasattr(doc, key):
                setattr(doc, key, value)
        doc.updated_at = datetime.now().isoformat()
        return doc

    async def delete_document(self, doc_id: str) -> bool:
        if doc_id in self._documents:
            del self._documents[doc_id]
            return True
        return False

    async def list_documents(self, doc_type: str | None = None) -> list[WorkspaceDocument]:
        docs = list(self._documents.values())
        if doc_type:
            docs = [d for d in docs if d.doc_type == doc_type]
        return sorted(docs, key=lambda d: d.updated_at, reverse=True)

    async def open_document(self, doc_id: str) -> dict[str, Any]:
        doc = await self.get_document(doc_id)
        if not doc:
            return {"error": f"Document not found: {doc_id}"}
        return {
            "doc_id": doc.doc_id,
            "title": doc.title,
            "doc_type": doc.doc_type,
            "content": doc.content,
            "metadata": doc.metadata,
        }

    async def open_presentation(self, doc_id: str) -> dict[str, Any]:
        return await self.open_document(doc_id)

    async def open_spreadsheet(self, doc_id: str) -> dict[str, Any]:
        return await self.open_document(doc_id)

    async def get_recommendations(self, mode: str = "normal") -> list[WorkspaceRecommendation]:
        recommendations = []
        if mode == "normal":
            recommendations = [
                WorkspaceRecommendation(
                    title="Create new document",
                    description="Start writing a new document",
                    action_type="create",
                    action_data={"doc_type": "note"},
                ),
                WorkspaceRecommendation(
                    title="Open knowledge base",
                    description="Search your knowledge base",
                    action_type="navigate",
                    action_data={"target": "knowledge"},
                ),
            ]
        elif mode == "edit":
            recommendations = [
                WorkspaceRecommendation(
                    title="AI assist",
                    description="Let AI help you write",
                    action_type="tool",
                    action_data={"tool": "ai_assist"},
                ),
                WorkspaceRecommendation(
                    title="Format document",
                    description="Auto-format your document",
                    action_type="tool",
                    action_data={"tool": "format"},
                ),
            ]
        return recommendations

    async def get_encouragement(self) -> WorkspaceEncouragement:
        import random
        return random.choice(FALLBACK_ENCOURAGEMENTS)

    async def get_smart_encouragement(
        self,
        active_tool: str = "",
        work_context: str = "",
        emotion_state: str = "",
        recent_actions: list[str] | None = None,
        work_duration_minutes: int = 0,
        completed_tasks_count: int = 0,
    ) -> WorkspaceEncouragement:
        tool_info = WORKSPACE_CONTEXT_MAP.get(active_tool, {})
        tool_label = tool_info.get("label", "")
        tool_actions = tool_info.get("actions", [])
        encouragement_angles = tool_info.get("encouragement_angles", [])

        context_parts = []
        now = datetime.now()
        hour = now.hour
        if 5 <= hour < 12:
            time_of_day = "早上"
        elif 12 <= hour < 14:
            time_of_day = "中午"
        elif 14 <= hour < 18:
            time_of_day = "下午"
        elif 18 <= hour < 22:
            time_of_day = "晚上"
        else:
            time_of_day = "深夜"

        context_parts.append(f"当前时间: {time_of_day}")

        if tool_label:
            context_parts.append(f"用户正在使用: {tool_label}")
        if tool_actions:
            context_parts.append(f"可能在进行: {', '.join(tool_actions[:3])}")
        if encouragement_angles:
            context_parts.append(f"鼓励角度: {', '.join(encouragement_angles[:2])}")
        if work_context:
            context_parts.append(f"工作内容: {work_context}")
        if emotion_state:
            context_parts.append(f"用户情绪: {emotion_state}")
        if recent_actions:
            context_parts.append(f"近期操作: {', '.join(recent_actions[-3:])}")
        if work_duration_minutes > 0:
            context_parts.append(f"已工作时长: {work_duration_minutes}分钟")
        if completed_tasks_count > 0:
            context_parts.append(f"已完成任务: {completed_tasks_count}个")

        context_str = "。".join(context_parts)

        try:
            from app.core.llm.dispatcher import ModelDispatcher, TaskCategory
            from app.core.llm.gateway import llm_gateway

            dispatcher = ModelDispatcher(gateway=llm_gateway)
            messages = [
                {
                    "role": "system",
                    "content": (
                        "你是一个温暖而智能的工作伙伴，负责给用户发送鼓励话语。规则:\n"
                        "1. 必须结合用户当前的工作场景来生成鼓励，让用户感受到你真的了解TA在做什么\n"
                        "2. 语气要自然亲切，像朋友一样，不要说教\n"
                        "3. 如果是深夜，提醒注意休息；如果是早上，给予美好开始祝福\n"
                        "4. 如果用户工作了较长时间，肯定TA的专注和投入\n"
                        "5. 如果用户完成了任务，给予真诚的祝贺\n"
                        "6. 不要使用任何表情符号\n"
                        "7. 控制在1-2句话以内，简洁有力\n"
                        "8. 返回JSON: {message: 鼓励话语, category: progress|focus|wellness|motivation|praise|achievement, tone: warm|calm|caring|energetic|encouraging|confident}"
                    ),
                },
                {"role": "user", "content": context_str},
            ]
            response = await dispatcher.dispatch(TaskCategory.INTENT, messages=messages)
            content = response.choices[0].message.content
            import json
            data = json.loads(content)
            return WorkspaceEncouragement(
                message=data.get("message", ""),
                category=data.get("category", "general"),
                context_aware=True,
                related_tool=active_tool,
                tone=data.get("tone", "warm"),
            )
        except Exception:
            import random
            fallback = random.choice(FALLBACK_ENCOURAGEMENTS)
            if tool_label:
                angle = random.choice(encouragement_angles) if encouragement_angles else "投入"
                fallback = WorkspaceEncouragement(
                    message=f"在{tool_label}中{angle}的你，真的很棒！",
                    category="progress",
                    context_aware=True,
                    related_tool=active_tool,
                    tone="warm",
                )
            return fallback

    async def get_status(self) -> dict[str, Any]:
        return {
            "documents_count": len(self._documents),
            "recent_documents": [
                {"doc_id": d.doc_id, "title": d.title, "doc_type": d.doc_type}
                for d in (await self.list_documents())[:5]
            ],
        }


workspace_service = WorkspaceService()
