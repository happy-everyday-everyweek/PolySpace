import asyncio
import json
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

import yaml

from app.core.audit.models import AuditCategory, AuditLevel
from app.core.audit.service import audit_service


class RiskLevel(str, Enum):
    LOW = "low_risk"
    MEDIUM = "medium_risk"
    HIGH = "high_risk"


class PolicyAction(str, Enum):
    ALLOW = "allow"
    NOTIFY = "notify"
    CONFIRM = "confirm"
    BLOCK = "block"


@dataclass
class Policy:
    name: str
    level: RiskLevel
    patterns: list[str]
    action: PolicyAction
    message: str
    _compiled_patterns: list[re.Pattern] = field(default_factory=list, repr=False, init=False)

    def __post_init__(self):
        self._compiled_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.patterns
        ]


class PolicyEngine:
    def __init__(self, policies_path: Optional[str] = None):
        self._policies: list[Policy] = []
        if policies_path:
            self.load_policies(policies_path)

    def load_policies(self, path: str) -> None:
        file_path = Path(path)
        if not file_path.exists():
            return
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data or "policies" not in data:
            return
        for p in data["policies"]:
            policy = Policy(
                name=p["name"],
                level=RiskLevel(p["level"]),
                patterns=p["patterns"],
                action=PolicyAction(p["action"]),
                message=p.get("message", ""),
            )
            self._policies.append(policy)

    def _match_policy(self, action: str) -> Optional[Policy]:
        for policy in self._policies:
            for compiled in policy._compiled_patterns:
                if compiled.search(action):
                    return policy
        return None

    def evaluate(self, action: str) -> tuple[PolicyAction, Optional[str]]:
        matched_policy = self._match_policy(action)

        if matched_policy:
            self._schedule_audit(action, matched_policy)
            return matched_policy.action, matched_policy.message

        self._schedule_audit(action, None)
        return PolicyAction.ALLOW, None

    async def evaluate_with_audit(
        self, action: str, *, actor_type: str = "agent", actor_id: str = ""
    ) -> tuple[PolicyAction, Optional[str]]:
        matched_policy = self._match_policy(action)

        if matched_policy:
            level = AuditLevel.WARN
            category = AuditCategory.POLICY_EVALUATE
            if matched_policy.action == PolicyAction.BLOCK:
                level = AuditLevel.ERROR
                category = AuditCategory.POLICY_BLOCK
            elif matched_policy.action == PolicyAction.CONFIRM:
                category = AuditCategory.POLICY_CONFIRM

            await audit_service.record(
                category=category,
                action=f"policy_evaluate:{matched_policy.name}",
                level=level,
                actor_type=actor_type,
                actor_id=actor_id,
                resource_type="policy",
                resource_id=matched_policy.name,
                status=matched_policy.action.value,
                detail=json.dumps({
                    "action": action,
                    "policy_name": matched_policy.name,
                    "risk_level": matched_policy.level.value,
                    "policy_action": matched_policy.action.value,
                    "message": matched_policy.message,
                }, ensure_ascii=False),
            )
            return matched_policy.action, matched_policy.message

        await audit_service.record(
            category=AuditCategory.POLICY_EVALUATE,
            action="policy_evaluate:allow",
            level=AuditLevel.INFO,
            actor_type=actor_type,
            actor_id=actor_id,
            status="allow",
            detail=json.dumps({"action": action, "result": "no_policy_matched"}, ensure_ascii=False),
        )
        return PolicyAction.ALLOW, None

    def _schedule_audit(self, action: str, policy: Optional[Policy]) -> None:
        try:
            loop = asyncio.get_running_loop()
            if policy:
                level = AuditLevel.WARN
                category = AuditCategory.POLICY_EVALUATE
                if policy.action == PolicyAction.BLOCK:
                    level = AuditLevel.ERROR
                    category = AuditCategory.POLICY_BLOCK
                elif policy.action == PolicyAction.CONFIRM:
                    category = AuditCategory.POLICY_CONFIRM
                task = loop.create_task(audit_service.record(
                    category=category,
                    action=f"policy_evaluate:{policy.name}",
                    level=level,
                    status=policy.action.value,
                    detail=json.dumps({
                        "action": action,
                        "policy_name": policy.name,
                        "risk_level": policy.level.value,
                        "policy_action": policy.action.value,
                    }, ensure_ascii=False),
                ))
                task.add_done_callback(self._handle_task_exception)
            else:
                task = loop.create_task(audit_service.record(
                    category=AuditCategory.POLICY_EVALUATE,
                    action="policy_evaluate:allow",
                    level=AuditLevel.INFO,
                    status="allow",
                    detail=json.dumps({"action": action, "result": "no_policy_matched"}, ensure_ascii=False),
                ))
                task.add_done_callback(self._handle_task_exception)
        except RuntimeError:
            pass

    @staticmethod
    def _handle_task_exception(task: asyncio.Task) -> None:
        if task.cancelled():
            return
        exc = task.exception()
        if exc:
            import logging
            logging.getLogger(__name__).error("Audit task failed: %s", exc)

    def is_high_risk(self, action: str) -> bool:
        action_result, _ = self.evaluate(action)
        return action_result in (PolicyAction.CONFIRM, PolicyAction.BLOCK)

    def add_policy(self, policy: Policy) -> None:
        self._policies.append(policy)

    def remove_policy(self, name: str) -> None:
        self._policies = [p for p in self._policies if p.name != name]

    def list_policies(self) -> list[dict]:
        return [
            {
                "name": p.name,
                "level": p.level.value,
                "patterns": p.patterns,
                "action": p.action.value,
                "message": p.message,
            }
            for p in self._policies
        ]
