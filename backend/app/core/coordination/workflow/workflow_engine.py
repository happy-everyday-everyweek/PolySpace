import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WorkflowStep:
    name: str
    action: str
    params: dict = field(default_factory=dict)
    status: str = "pending"
    result: Any = None
    retry_count: int = 0
    max_retries: int = 3

    def to_dict(self) -> dict:
        return {"name": self.name, "action": self.action, "status": self.status, "result": str(self.result)[:200] if self.result else None}


@dataclass
class Workflow:
    id: str
    name: str
    description: str
    steps: list[WorkflowStep] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_step: int = 0
    created_at: float = field(default_factory=time.time)
    completed_at: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "steps": [s.to_dict() for s in self.steps],
            "status": self.status.value,
            "current_step": self.current_step,
            "progress": f"{self.current_step}/{len(self.steps)}",
        }


BUILTIN_TEMPLATES = {
    "email_processing": [
        {"name": "fetch_emails", "action": "email_fetch_new"},
        {"name": "classify", "action": "email_classify"},
        {"name": "draft_replies", "action": "email_draft_replies"},
        {"name": "remind_user", "action": "notify_user"},
    ],
    "meeting_workflow": [
        {"name": "prepare", "action": "meeting_prepare_materials"},
        {"name": "remind", "action": "meeting_send_reminder"},
        {"name": "record", "action": "meeting_start_recording"},
        {"name": "extract_todos", "action": "meeting_extract_action_items"},
        {"name": "followup", "action": "meeting_send_followup"},
    ],
    "document_workflow": [
        {"name": "outline", "action": "doc_generate_outline"},
        {"name": "draft", "action": "doc_write_draft"},
        {"name": "review", "action": "doc_review_content"},
        {"name": "revise", "action": "doc_apply_revisions"},
        {"name": "finalize", "action": "doc_finalize"},
    ],
    "data_analysis": [
        {"name": "fetch_data", "action": "data_fetch"},
        {"name": "clean", "action": "data_clean"},
        {"name": "analyze", "action": "data_analyze"},
        {"name": "visualize", "action": "data_visualize"},
        {"name": "report", "action": "data_generate_report"},
    ],
    "project_management": [
        {"name": "gather_requirements", "action": "pm_gather_requirements"},
        {"name": "break_down", "action": "pm_break_down_tasks"},
        {"name": "assign", "action": "pm_assign_tasks"},
        {"name": "track", "action": "pm_track_progress"},
        {"name": "retrospect", "action": "pm_retrospect"},
    ],
}


class WorkflowEngine:
    def __init__(self):
        self._workflows: dict[str, Workflow] = {}
        self._templates = dict(BUILTIN_TEMPLATES)
        self._max_workflows = 50

    def create_from_template(self, template_name: str, params: Optional[dict] = None) -> Optional[Workflow]:
        template = self._templates.get(template_name)
        if not template:
            return None
        steps = [WorkflowStep(name=s["name"], action=s["action"], params=params or {}) for s in template]
        wf_id = f"wf_{template_name}_{int(time.time())}"
        workflow = Workflow(id=wf_id, name=template_name, description=f"Auto-created from template: {template_name}", steps=steps)
        self._workflows[wf_id] = workflow
        if len(self._workflows) > self._max_workflows:
            oldest = min(self._workflows, key=lambda k: self._workflows[k].created_at)
            del self._workflows[oldest]
        return workflow

    async def execute(self, workflow_id: str) -> Optional[dict]:
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            return None
        workflow.status = WorkflowStatus.RUNNING
        for i, step in enumerate(workflow.steps):
            workflow.current_step = i
            step.status = "running"
            try:
                step.result = await self._execute_step(step)
                step.status = "completed"
            except Exception as e:
                logger.error(f"Workflow step {step.name} failed: {e}")
                if step.retry_count < step.max_retries:
                    step.retry_count += 1
                    step.status = "retrying"
                    try:
                        step.result = await self._execute_step(step)
                        step.status = "completed"
                    except Exception:
                        step.status = "failed"
                        workflow.status = WorkflowStatus.FAILED
                        return workflow.to_dict()
                else:
                    step.status = "failed"
                    workflow.status = WorkflowStatus.FAILED
                    return workflow.to_dict()
        workflow.status = WorkflowStatus.COMPLETED
        workflow.completed_at = time.time()
        workflow.current_step = len(workflow.steps)
        return workflow.to_dict()

    async def _execute_step(self, step: WorkflowStep) -> Any:
        return {"action": step.action, "status": "simulated", "params": step.params}

    def pause(self, workflow_id: str) -> bool:
        wf = self._workflows.get(workflow_id)
        if wf and wf.status == WorkflowStatus.RUNNING:
            wf.status = WorkflowStatus.PAUSED
            return True
        return False

    def resume(self, workflow_id: str) -> bool:
        wf = self._workflows.get(workflow_id)
        if wf and wf.status == WorkflowStatus.PAUSED:
            wf.status = WorkflowStatus.RUNNING
            return True
        return False

    def get_workflow(self, workflow_id: str) -> Optional[dict]:
        wf = self._workflows.get(workflow_id)
        return wf.to_dict() if wf else None

    def list_workflows(self, status: Optional[str] = None) -> list[dict]:
        results = []
        for wf in self._workflows.values():
            if status and wf.status.value != status:
                continue
            results.append(wf.to_dict())
        return results

    def list_templates(self) -> list[dict]:
        return [{"name": k, "steps": len(v)} for k, v in self._templates.items()]


_engine: Optional[WorkflowEngine] = None


def get_workflow_engine() -> WorkflowEngine:
    global _engine
    if _engine is None:
        _engine = WorkflowEngine()
    return _engine
