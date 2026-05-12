import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from app.core.safety.policies import PolicyEngine, Policy, PolicyAction, RiskLevel


class TestPolicyEngineAsync:
    @pytest.mark.asyncio
    async def test_evaluate_with_audit_block_action(self):
        engine = PolicyEngine()
        policy = Policy(
            name="test_block",
            level=RiskLevel.HIGH,
            patterns=[r"rm\s+-rf"],
            action=PolicyAction.BLOCK,
            message="Dangerous command blocked",
        )
        engine.add_policy(policy)

        with patch("app.core.safety.policies.audit_service") as mock_audit:
            mock_audit.record = AsyncMock()
            action, msg = await engine.evaluate_with_audit("rm -rf /")
            assert action == PolicyAction.BLOCK
            assert "Dangerous" in msg
            mock_audit.record.assert_called_once()

    @pytest.mark.asyncio
    async def test_evaluate_with_audit_confirm_action(self):
        engine = PolicyEngine()
        policy = Policy(
            name="test_confirm",
            level=RiskLevel.MEDIUM,
            patterns=[r"delete"],
            action=PolicyAction.CONFIRM,
            message="Please confirm deletion",
        )
        engine.add_policy(policy)

        with patch("app.core.safety.policies.audit_service") as mock_audit:
            mock_audit.record = AsyncMock()
            action, msg = await engine.evaluate_with_audit("delete all files")
            assert action == PolicyAction.CONFIRM
            mock_audit.record.assert_called_once()

    @pytest.mark.asyncio
    async def test_evaluate_with_audit_notify_action(self):
        engine = PolicyEngine()
        policy = Policy(
            name="test_notify",
            level=RiskLevel.LOW,
            patterns=[r"sudo"],
            action=PolicyAction.NOTIFY,
            message="Sudo usage logged",
        )
        engine.add_policy(policy)

        with patch("app.core.safety.policies.audit_service") as mock_audit:
            mock_audit.record = AsyncMock()
            action, msg = await engine.evaluate_with_audit("sudo apt update")
            assert action == PolicyAction.NOTIFY
            mock_audit.record.assert_called_once()

    @pytest.mark.asyncio
    async def test_evaluate_with_audit_allow_no_match(self):
        engine = PolicyEngine()
        policy = Policy(
            name="test_block",
            level=RiskLevel.HIGH,
            patterns=[r"rm\s+-rf"],
            action=PolicyAction.BLOCK,
            message="Blocked",
        )
        engine.add_policy(policy)

        with patch("app.core.safety.policies.audit_service") as mock_audit:
            mock_audit.record = AsyncMock()
            action, msg = await engine.evaluate_with_audit("ls -la")
            assert action == PolicyAction.ALLOW
            assert msg is None
            mock_audit.record.assert_called_once()

    @pytest.mark.asyncio
    async def test_evaluate_with_audit_custom_actor(self):
        engine = PolicyEngine()
        policy = Policy(
            name="test_policy",
            level=RiskLevel.MEDIUM,
            patterns=[r"test"],
            action=PolicyAction.NOTIFY,
            message="Test action",
        )
        engine.add_policy(policy)

        with patch("app.core.safety.policies.audit_service") as mock_audit:
            mock_audit.record = AsyncMock()
            await engine.evaluate_with_audit("test action", actor_type="user", actor_id="user123")
            call_kwargs = mock_audit.record.call_args
            assert call_kwargs is not None


class TestPolicyEnginePatterns:
    def test_case_insensitive_pattern(self):
        engine = PolicyEngine()
        policy = Policy(
            name="case_test",
            level=RiskLevel.HIGH,
            patterns=[r"DANGER"],
            action=PolicyAction.BLOCK,
            message="Danger detected",
        )
        engine.add_policy(policy)

        action1, _ = engine.evaluate("dangerous command")
        action2, _ = engine.evaluate("DANGEROUS COMMAND")
        action3, _ = engine.evaluate("Dangerous Command")

        assert action1 == PolicyAction.BLOCK
        assert action2 == PolicyAction.BLOCK
        assert action3 == PolicyAction.BLOCK

    def test_multiple_patterns_match(self):
        engine = PolicyEngine()
        policy = Policy(
            name="multi_pattern",
            level=RiskLevel.HIGH,
            patterns=[r"rm\s+-rf", r"format", r"drop\s+table"],
            action=PolicyAction.BLOCK,
            message="Destructive action blocked",
        )
        engine.add_policy(policy)

        action1, _ = engine.evaluate("rm -rf /")
        action2, _ = engine.evaluate("format c:")
        action3, _ = engine.evaluate("drop table users")

        assert action1 == PolicyAction.BLOCK
        assert action2 == PolicyAction.BLOCK
        assert action3 == PolicyAction.BLOCK

    def test_first_matching_policy_returns(self):
        engine = PolicyEngine()
        policy1 = Policy(
            name="first",
            level=RiskLevel.LOW,
            patterns=[r"test"],
            action=PolicyAction.NOTIFY,
            message="First policy",
        )
        policy2 = Policy(
            name="second",
            level=RiskLevel.HIGH,
            patterns=[r"test"],
            action=PolicyAction.BLOCK,
            message="Second policy",
        )
        engine.add_policy(policy1)
        engine.add_policy(policy2)

        action, msg = engine.evaluate("test action")
        assert action == PolicyAction.NOTIFY
        assert msg == "First policy"

    def test_policy_engine_from_yaml_path(self):
        import tempfile
        import yaml

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                "policies": [
                    {
                        "name": "yaml_policy",
                        "level": "high_risk",
                        "patterns": [r"danger"],
                        "action": "block",
                        "message": "Dangerous action"
                    }
                ]
            }, f)
            temp_path = f.name

        engine = PolicyEngine(policies_path=temp_path)
        action, msg = engine.evaluate("dangerous action")
        assert action == PolicyAction.BLOCK
        assert msg == "Dangerous action"


class TestPolicyEngineEdgeCases:
    def test_empty_pattern_list(self):
        policy = Policy(
            name="empty_patterns",
            level=RiskLevel.LOW,
            patterns=[],
            action=PolicyAction.ALLOW,
            message="",
        )
        assert len(policy._compiled_patterns) == 0

    def test_special_regex_characters(self):
        policy = Policy(
            name="special_chars",
            level=RiskLevel.HIGH,
            patterns=[r"file\[1\]\.txt"],
            action=PolicyAction.BLOCK,
            message="Special chars blocked",
        )
        assert len(policy._compiled_patterns) == 1

    def test_unicode_pattern(self):
        policy = Policy(
            name="unicode_pattern",
            level=RiskLevel.MEDIUM,
            patterns=[r"密码"],
            action=PolicyAction.NOTIFY,
            message="Password keyword",
        )
        assert len(policy._compiled_patterns) == 1

    def test_remove_nonexistent_policy(self):
        engine = PolicyEngine()
        initial_count = len(engine.list_policies())
        engine.remove_policy("nonexistent_policy")
        assert len(engine.list_policies()) == initial_count
