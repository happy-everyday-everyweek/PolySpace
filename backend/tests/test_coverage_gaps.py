import asyncio
import time
import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.config import set_test_mode

set_test_mode(True)


def _unique_username(base: str) -> str:
    return f"{base}_{uuid.uuid4().hex[:8]}"


class TestAuthService:
    @pytest.mark.asyncio
    async def test_password_hash_and_verify(self):
        from app.services.auth_service import _hash_password, _verify_password

        password = "test_password_123"
        hashed = _hash_password(password)

        assert ":" in hashed
        assert _verify_password(password, hashed) is True
        assert _verify_password("wrong_password", hashed) is False

    @pytest.mark.asyncio
    async def test_password_hash_with_salt(self):
        from app.services.auth_service import _hash_password, _verify_password

        password = "test_password"
        salt = "test_salt_123"
        hashed = _hash_password(password, salt)

        assert hashed.startswith(f"{salt}:")
        assert _verify_password(password, hashed) is True

    @pytest.mark.asyncio
    async def test_password_verify_malformed_hash(self):
        from app.services.auth_service import _verify_password

        assert _verify_password("password", "malformed_hash") is False
        assert _verify_password("password", "") is False

    @pytest.mark.asyncio
    async def test_login_disabled_account(self):
        from app.services.auth_service import AuthService, LoginRequest, UserStatus

        service = AuthService()
        from app.services.auth_service import UserCreateRequest

        username = _unique_username("disabled_user")
        req = UserCreateRequest(username=username, password="test123")
        await service.register(req)

        user = await service.get_user(
            next(u.id for u in await service.list_users() if u.username == username)
        )
        user.status = UserStatus.DISABLED

        login_req = LoginRequest(username=username, password="test123")
        with pytest.raises(ValueError, match="disabled"):
            await service.login(login_req)

    @pytest.mark.asyncio
    async def test_validate_token_valid(self):
        from app.services.auth_service import AuthService, UserCreateRequest

        service = AuthService()
        username = _unique_username("token_user")
        req = UserCreateRequest(username=username, password="test123")
        user = await service.register(req)

        validated = await service.validate_token(user.api_token)
        assert validated is not None
        assert validated.username == username

    @pytest.mark.asyncio
    async def test_validate_token_invalid(self):
        from app.services.auth_service import AuthService

        service = AuthService()
        result = await service.validate_token("invalid_token_12345")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_user(self):
        from app.services.auth_service import AuthService, UserCreateRequest, UserUpdateRequest

        service = AuthService()
        username = _unique_username("update_user")
        req = UserCreateRequest(username=username, password="test123")
        user = await service.register(req)

        update_req = UserUpdateRequest(
            display_name="New Name",
            email="new@email.com",
        )
        updated = await service.update_user(user.id, update_req)
        assert updated is not None
        assert updated.display_name == "New Name"
        assert updated.email == "new@email.com"

    @pytest.mark.asyncio
    async def test_update_user_not_found(self):
        from app.services.auth_service import AuthService, UserUpdateRequest

        service = AuthService()
        update_req = UserUpdateRequest(display_name="New Name")
        result = await service.update_user("nonexistent_id", update_req)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_user(self):
        from app.services.auth_service import AuthService, UserCreateRequest

        service = AuthService()
        username = _unique_username("delete_user")
        req = UserCreateRequest(username=username, password="test123")
        user = await service.register(req)

        deleted = await service.delete_user(user.id)
        assert deleted is True

        result = await service.get_user(user.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self):
        from app.services.auth_service import AuthService

        service = AuthService()
        deleted = await service.delete_user("nonexistent_id")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_create_shared_workspace(self):
        from app.services.auth_service import AuthService, UserCreateRequest

        service = AuthService()
        username = _unique_username("ws_owner")
        req = UserCreateRequest(username=username, password="test123")
        owner = await service.register(req)

        ws = await service.create_shared_workspace("Test Workspace", owner.id)
        assert ws.name == "Test Workspace"
        assert ws.owner_id == owner.id
        assert len(ws.members) == 1
        assert ws.members[0]["role"] == "owner"

    @pytest.mark.asyncio
    async def test_create_shared_workspace_with_members(self):
        from app.services.auth_service import AuthService, UserCreateRequest

        service = AuthService()
        owner_req = UserCreateRequest(username=_unique_username("ws_owner2"), password="test123")
        owner = await service.register(owner_req)
        member_req = UserCreateRequest(username=_unique_username("ws_member"), password="test123")
        member = await service.register(member_req)

        ws = await service.create_shared_workspace(
            "Test Workspace 2", owner.id, [owner.id, member.id]
        )
        assert len(ws.members) == 2

    @pytest.mark.asyncio
    async def test_list_shared_workspaces(self):
        from app.services.auth_service import AuthService, UserCreateRequest

        service = AuthService()
        owner_req = UserCreateRequest(username=_unique_username("ws_owner3"), password="test123")
        owner = await service.register(owner_req)

        await service.create_shared_workspace("Workspace 1", owner.id)
        await service.create_shared_workspace("Workspace 2", owner.id)

        workspaces = await service.list_shared_workspaces(owner.id)
        assert len(workspaces) >= 2

    @pytest.mark.asyncio
    async def test_add_workspace_member(self):
        from app.services.auth_service import AuthService, UserCreateRequest

        service = AuthService()
        owner_req = UserCreateRequest(username=_unique_username("ws_owner4"), password="test123")
        owner = await service.register(owner_req)
        member_req = UserCreateRequest(username=_unique_username("ws_member2"), password="test123")
        member = await service.register(member_req)

        ws = await service.create_shared_workspace("Test Workspace 3", owner.id)
        added = await service.add_workspace_member(ws.id, member.id)
        assert added is True

        updated_ws = next(
            w for w in service._shared_workspaces.values() if w.id == ws.id
        )
        assert len(updated_ws.members) == 2

    @pytest.mark.asyncio
    async def test_add_workspace_member_already_exists(self):
        from app.services.auth_service import AuthService, UserCreateRequest

        service = AuthService()
        owner_req = UserCreateRequest(username=_unique_username("ws_owner5"), password="test123")
        owner = await service.register(owner_req)

        ws = await service.create_shared_workspace("Test Workspace 4", owner.id)
        added = await service.add_workspace_member(ws.id, owner.id)
        assert added is False

    @pytest.mark.asyncio
    async def test_remove_workspace_member(self):
        from app.services.auth_service import AuthService, UserCreateRequest

        service = AuthService()
        owner_req = UserCreateRequest(username=_unique_username("ws_owner6"), password="test123")
        owner = await service.register(owner_req)
        member_req = UserCreateRequest(username=_unique_username("ws_member3"), password="test123")
        member = await service.register(member_req)

        ws = await service.create_shared_workspace(
            "Test Workspace 5", owner.id, [owner.id, member.id]
        )
        removed = await service.remove_workspace_member(ws.id, member.id)
        assert removed is True

    @pytest.mark.asyncio
    async def test_remove_workspace_member_owner_protected(self):
        from app.services.auth_service import AuthService, UserCreateRequest

        service = AuthService()
        owner_req = UserCreateRequest(username=_unique_username("ws_owner7"), password="test123")
        owner = await service.register(owner_req)

        ws = await service.create_shared_workspace("Test Workspace 6", owner.id)
        await service.remove_workspace_member(ws.id, owner.id)

        updated_ws = next(
            w for w in service._shared_workspaces.values() if w.id == ws.id
        )
        assert len(updated_ws.members) == 1
        assert updated_ws.members[0]["user_id"] == owner.id


class TestSafeEvaluatorExtended:
    def setup_method(self):
        from app.core.tool.workspace_tools import safe_eval
        self.safe_eval = safe_eval

    def test_bool_op_and(self):
        assert self.safe_eval("True and True") == True
        assert self.safe_eval("True and False") == False
        assert self.safe_eval("False and False") == False
        assert self.safe_eval("1 and 0") == 0

    def test_bool_op_or(self):
        assert self.safe_eval("True or False") == True
        assert self.safe_eval("False or False") == False
        assert self.safe_eval("False or True") == True
        assert self.safe_eval("0 or 1") == 1

    def test_chained_comparisons(self):
        assert self.safe_eval("1 < 2 < 3") == True
        assert self.safe_eval("1 < 2 > 0") == True
        assert self.safe_eval("3 > 2 > 1") == True
        assert self.safe_eval("1 > 2 > 3") == False

    def test_floor_division_not_supported(self):
        with pytest.raises(ValueError, match="Unsupported binary operator"):
            self.safe_eval("7 // 3")

    def test_bitwise_xor_converts_to_power(self):
        result = self.safe_eval("5 ^ 3")
        assert result == 125

    def test_complex_expression(self):
        assert self.safe_eval("2 + 3 * 4 - 1") == 13
        assert self.safe_eval("(2 + 3) * (4 - 1)") == 15

    def test_scientific_notation(self):
        assert self.safe_eval("1e3") == 1000.0
        assert self.safe_eval("2.5e2") == 250.0

    def test_negative_numbers(self):
        assert self.safe_eval("-5 + 3") == -2
        assert self.safe_eval("5 * -3") == -15

    def test_division_by_zero(self):
        with pytest.raises(ZeroDivisionError):
            self.safe_eval("1 / 0")

    def test_modulo_operation(self):
        assert self.safe_eval("10 % 3") == 1
        assert self.safe_eval("15 % 5") == 0

    def test_large_numbers(self):
        assert self.safe_eval("1000000 * 1000000") == 1000000000000


class TestContextAggregatorExtended:
    @pytest.mark.asyncio
    async def test_event_expiration(self):
        from app.core.coordination.context.aggregator import (
            ContextAggregator,
            ContextEvent,
            ContextSource,
        )

        aggregator = ContextAggregator()
        event = ContextEvent(
            source=ContextSource.CHAT,
            data={"message": "test"},
            ttl=0.1,
        )
        await aggregator.ingest(event)

        time.sleep(0.2)

        context = await aggregator.get_current_context()
        assert context["event_count"] == 0

    @pytest.mark.asyncio
    async def test_event_hash_deduplication(self):
        from app.core.coordination.context.aggregator import (
            ContextAggregator,
            ContextEvent,
            ContextSource,
        )

        aggregator = ContextAggregator()
        event1 = ContextEvent(
            source=ContextSource.CHAT,
            data={"message": "test", "app": "test_app"},
        )
        event2 = ContextEvent(
            source=ContextSource.CHAT,
            data={"message": "test", "app": "test_app"},
        )

        await aggregator.ingest(event1)
        await aggregator.ingest(event2)

        context = await aggregator.get_current_context()
        assert context["event_count"] == 1

    @pytest.mark.asyncio
    async def test_subscriber_callback(self):
        from app.core.coordination.context.aggregator import (
            ContextAggregator,
            ContextEvent,
            ContextSource,
        )

        aggregator = ContextAggregator()
        received_events = []

        async def callback(event):
            received_events.append(event)

        aggregator.subscribe(callback)
        event = ContextEvent(source=ContextSource.CHAT, data={"test": "data"})
        await aggregator.ingest(event)

        assert len(received_events) == 1
        assert received_events[0].source == ContextSource.CHAT

    @pytest.mark.asyncio
    async def test_sync_subscriber(self):
        from app.core.coordination.context.aggregator import (
            ContextAggregator,
            ContextEvent,
            ContextSource,
        )

        aggregator = ContextAggregator()
        received_events = []

        def sync_callback(event):
            received_events.append(event)

        aggregator.subscribe(sync_callback)
        event = ContextEvent(source=ContextSource.SCREEN, data={"test": "sync"})
        await aggregator.ingest(event)

        assert len(received_events) == 1

    @pytest.mark.asyncio
    async def test_unsubscribe(self):
        from app.core.coordination.context.aggregator import (
            ContextAggregator,
            ContextEvent,
            ContextSource,
        )

        aggregator = ContextAggregator()
        received_events = []

        def callback(event):
            received_events.append(event)

        aggregator.subscribe(callback)
        aggregator.unsubscribe(callback)
        event = ContextEvent(source=ContextSource.CHAT, data={"test": "data"})
        await aggregator.ingest(event)

        assert len(received_events) == 0

    @pytest.mark.asyncio
    async def test_search_context(self):
        from app.core.coordination.context.aggregator import (
            ContextAggregator,
            ContextEvent,
            ContextSource,
        )

        aggregator = ContextAggregator()
        await aggregator.ingest(
            ContextEvent(source=ContextSource.CHAT, data={"message": "hello world"})
        )
        await aggregator.ingest(
            ContextEvent(source=ContextSource.EMAIL, data={"subject": "test email"})
        )

        results = await aggregator.search_context("hello")
        assert len(results) == 1
        assert "hello" in results[0]["data"]["message"]

    @pytest.mark.asyncio
    async def test_build_activity_summary(self):
        from app.core.coordination.context.aggregator import ContextAggregator

        aggregator = ContextAggregator()
        events = [
            {"source": "chat", "data": {"app": "vscode", "action": "edit"}},
            {"source": "chat", "data": {"app": "vscode", "action": "edit"}},
            {"source": "screen", "data": {"app": "browser"}},
        ]

        summary = aggregator.build_activity_summary(events)
        assert summary is not None
        assert summary["primary_source"] == "chat"
        assert summary["primary_activity"] in ("edit", "vscode")
        assert "vscode" in summary["key_entities"]

    @pytest.mark.asyncio
    async def test_build_activity_summary_empty(self):
        from app.core.coordination.context.aggregator import ContextAggregator

        aggregator = ContextAggregator()
        summary = aggregator.build_activity_summary([])
        assert summary is None

    @pytest.mark.asyncio
    async def test_get_incremental_events(self):
        from app.core.coordination.context.aggregator import (
            ContextAggregator,
            ContextEvent,
            ContextSource,
        )

        aggregator = ContextAggregator()
        await aggregator.ingest(
            ContextEvent(source=ContextSource.CHAT, data={"msg": "first", "app": "app1"})
        )
        await aggregator.ingest(
            ContextEvent(source=ContextSource.CHAT, data={"msg": "second", "app": "app2"})
        )

        events = aggregator.get_incremental_events()
        assert len(events) == 2

        await aggregator.ingest(
            ContextEvent(source=ContextSource.CHAT, data={"msg": "third", "app": "app3"})
        )
        new_events = aggregator.get_incremental_events()
        assert len(new_events) == 1

    @pytest.mark.asyncio
    async def test_get_events_since(self):
        from app.core.coordination.context.aggregator import (
            ContextAggregator,
            ContextEvent,
            ContextSource,
        )

        aggregator = ContextAggregator()
        now = time.time()
        await aggregator.ingest(
            ContextEvent(source=ContextSource.CHAT, data={"msg": "old", "app": "old_app"}, timestamp=now - 10)
        )
        await aggregator.ingest(
            ContextEvent(source=ContextSource.CHAT, data={"msg": "new", "app": "new_app"}, timestamp=now - 1)
        )

        events = aggregator.get_events_since(now - 5)
        assert len(events) == 1
        assert events[0]["data"]["msg"] == "new"

    @pytest.mark.asyncio
    async def test_get_source_events(self):
        from app.core.coordination.context.aggregator import (
            ContextAggregator,
            ContextEvent,
            ContextSource,
        )

        aggregator = ContextAggregator()
        await aggregator.ingest(
            ContextEvent(source=ContextSource.CHAT, data={"msg": "chat1", "app": "app1"})
        )
        await aggregator.ingest(
            ContextEvent(source=ContextSource.SCREEN, data={"msg": "screen1", "app": "app2"})
        )
        await aggregator.ingest(
            ContextEvent(source=ContextSource.CHAT, data={"msg": "chat2", "app": "app3"})
        )

        chat_events = aggregator.get_source_events(ContextSource.CHAT)
        assert len(chat_events) == 2

    @pytest.mark.asyncio
    async def test_get_context_for_llm(self):
        from app.core.coordination.context.aggregator import (
            ContextAggregator,
            ContextEvent,
            ContextSource,
        )

        aggregator = ContextAggregator()
        await aggregator.ingest(
            ContextEvent(source=ContextSource.CHAT, data={"message": "test message"})
        )

        llm_context = await aggregator.get_context_for_llm()
        assert "chat" in llm_context.lower()
        assert "Active sources" in llm_context

    @pytest.mark.asyncio
    async def test_ingest_batch(self):
        from app.core.coordination.context.aggregator import (
            ContextAggregator,
            ContextEvent,
            ContextSource,
        )

        aggregator = ContextAggregator()
        events = [
            ContextEvent(source=ContextSource.CHAT, data={"msg": "1"}),
            ContextEvent(source=ContextSource.SCREEN, data={"msg": "2"}),
            ContextEvent(source=ContextSource.EMAIL, data={"msg": "3"}),
        ]
        await aggregator.ingest_batch(events)

        context = await aggregator.get_current_context()
        assert context["event_count"] == 3


class TestExceptionsExtended:
    def test_tool_error(self):
        from app.core.exceptions import ToolError

        err = ToolError("Tool failed", tool_name="test_tool")
        assert err.code == "TOOL_ERROR"
        assert err.status_code == 500
        assert err.tool_name == "test_tool"

    def test_llm_rate_limit_error(self):
        from app.core.exceptions import LLMRateLimitError

        err = LLMRateLimitError(provider="openai", model="gpt-4")
        assert err.code == "LLM_RATE_LIMIT"
        assert err.status_code == 429

    def test_llm_timeout_error(self):
        from app.core.exceptions import LLMTimeoutError

        err = LLMTimeoutError(provider="anthropic", model="claude-3")
        assert err.code == "LLM_TIMEOUT"
        assert err.status_code == 504

    def test_memory_error(self):
        from app.core.exceptions import MemoryError as PolyMemoryError

        err = PolyMemoryError("Memory allocation failed")
        assert err.code == "MEMORY_ERROR"
        assert err.status_code == 500

    def test_safety_violation_error(self):
        from app.core.exceptions import SafetyViolationError

        err = SafetyViolationError("Dangerous action", policy="block_shell")
        assert err.code == "SAFETY_VIOLATION"
        assert err.status_code == 403
        assert err.policy == "block_shell"

    def test_validation_error(self):
        from app.core.exceptions import ValidationError

        err = ValidationError("Invalid input", detail={"field": "username"})
        assert err.code == "VALIDATION_ERROR"
        assert err.status_code == 422
        assert err.detail == {"field": "username"}

    def test_not_found_error(self):
        from app.core.exceptions import NotFoundError

        err = NotFoundError(resource="user")
        assert err.code == "NOT_FOUND"
        assert err.status_code == 404
        assert err.resource == "user"

    def test_format_error_response(self):
        from app.core.exceptions import PolySpaceError, _format_error_response

        err = PolySpaceError("Test error", code="TEST_CODE", detail={"key": "value"})
        response = _format_error_response(err)

        assert response["error"]["code"] == "TEST_CODE"
        assert response["error"]["message"] == "Test error"
        assert response["error"]["detail"] == {"key": "value"}

    def test_format_error_response_no_detail(self):
        from app.core.exceptions import PolySpaceError, _format_error_response

        err = PolySpaceError("Simple error", code="SIMPLE")
        response = _format_error_response(err)

        assert "detail" not in response["error"]


class TestPolicyEngineExtended:
    def setup_method(self):
        from app.core.safety.policies import PolicyEngine
        self.engine = PolicyEngine()

    def test_load_policies_file_not_exists(self):
        from app.core.safety.policies import PolicyEngine

        engine = PolicyEngine(policies_path="/nonexistent/path/policies.yaml")
        assert len(engine.list_policies()) == 0

    def test_load_policies_invalid_yaml(self, tmp_path):
        from app.core.safety.policies import PolicyEngine
        import yaml

        invalid_yaml = tmp_path / "invalid.yaml"
        invalid_yaml.write_text("not: valid: yaml: :")

        with pytest.raises(yaml.scanner.ScannerError):
            engine = PolicyEngine(policies_path=str(invalid_yaml))

    def test_load_policies_empty_file(self, tmp_path):
        from app.core.safety.policies import PolicyEngine

        empty_yaml = tmp_path / "empty.yaml"
        empty_yaml.write_text("")

        engine = PolicyEngine(policies_path=str(empty_yaml))
        assert len(engine.list_policies()) == 0

    def test_load_policies_valid(self, tmp_path):
        from app.core.safety.policies import PolicyEngine

        valid_yaml = tmp_path / "policies.yaml"
        valid_yaml.write_text("""
policies:
  - name: test_policy
    level: high_risk
    patterns:
      - "dangerous"
    action: block
    message: "Blocked dangerous action"
""")
        engine = PolicyEngine(policies_path=str(valid_yaml))
        policies = engine.list_policies()
        assert len(policies) == 1
        assert policies[0]["name"] == "test_policy"

    @pytest.mark.asyncio
    async def test_evaluate_with_audit_allow(self):
        from app.core.safety.policies import PolicyEngine

        engine = PolicyEngine()
        action, msg = await engine.evaluate_with_audit("safe action", actor_type="user", actor_id="test_user")
        assert action.value == "allow"
        assert msg is None

    @pytest.mark.asyncio
    async def test_evaluate_with_audit_block(self):
        from app.core.safety.policies import Policy, PolicyAction, PolicyEngine, RiskLevel

        engine = PolicyEngine()
        policy = Policy(
            name="test_block",
            level=RiskLevel.HIGH,
            patterns=[r"rm\s+-rf"],
            action=PolicyAction.BLOCK,
            message="Dangerous command",
        )
        engine.add_policy(policy)

        action, msg = await engine.evaluate_with_audit("rm -rf /", actor_type="agent", actor_id="test_agent")
        assert action == PolicyAction.BLOCK
        assert msg == "Dangerous command"


class TestRuntimeMonitorExtended:
    def setup_method(self):
        from app.core.safety.monitor import ResourceBudget, RuntimeMonitor
        self.budget = ResourceBudget(
            max_tokens_per_request=50000,
            max_requests_per_minute=30,
            max_tool_calls_per_minute=10,
            max_concurrent_tools=3,
        )
        self.monitor = RuntimeMonitor(budget=self.budget)

    def test_resource_budget_defaults(self):
        from app.core.safety.monitor import ResourceBudget

        budget = ResourceBudget()
        assert budget.max_tokens_per_request == 100000
        assert budget.max_requests_per_minute == 60
        assert budget.max_tool_calls_per_minute == 30
        assert budget.max_concurrent_tools == 5

    def test_rate_limit_exceeded(self):
        for i in range(15):
            self.monitor.record_tool_call(f"tool_{i}")

        assert not self.monitor.check_rate_limit()

    def test_verify_determinism_match(self):
        result = self.monitor.verify_determinism("expected output", "expected output")
        assert result is True

    def test_verify_determinism_with_whitespace(self):
        result = self.monitor.verify_determinism("  expected  ", "expected")
        assert result is True

    def test_verify_determinism_mismatch(self):
        result = self.monitor.verify_determinism("expected", "actual")
        assert result is False

    def test_stats_cache_expiry(self):
        from app.core.safety.monitor import RuntimeMonitor

        monitor = RuntimeMonitor()
        monitor.record_tool_call("tool1")

        stats1 = monitor.get_stats()

        time.sleep(0.1)
        monitor.record_tool_call("tool2")

        stats2 = monitor.get_stats()
        assert stats2["total_calls"] == 2

    def test_tool_call_record_timestamp(self):
        from app.core.safety.monitor import ToolCallRecord

        record = ToolCallRecord(tool_name="test_tool")
        assert record.tool_name == "test_tool"
        assert record.timestamp is not None

    def test_stats_values(self):
        self.monitor.record_tool_call("tool_a")
        self.monitor.record_tool_call("tool_b")
        self.monitor.record_tool_call("tool_a")

        stats = self.monitor.get_stats()
        assert stats["total_calls"] == 3
        assert "calls_last_minute" in stats
        assert "jitter_detected" in stats
        assert "rate_limit_ok" in stats


class TestShellToolExtended:
    @pytest.mark.asyncio
    async def test_sanitize_command_empty(self):
        from app.core.tools.shell_tool import ShellTool

        tool = ShellTool()
        is_valid, error = tool._sanitize_command("")
        assert is_valid is False
        assert "empty" in error.lower()

    @pytest.mark.asyncio
    async def test_sanitize_command_too_long(self):
        from app.core.tools.shell_tool import ShellTool

        tool = ShellTool()
        long_cmd = "ls " + "a" * 5000
        is_valid, error = tool._sanitize_command(long_cmd)
        assert is_valid is False
        assert "long" in error.lower()

    @pytest.mark.asyncio
    async def test_sanitize_command_disallowed(self):
        from app.core.tools.shell_tool import ShellTool

        tool = ShellTool()
        is_valid, error = tool._sanitize_command("format c:")
        assert is_valid is False
        assert "not allowed" in error.lower()

    @pytest.mark.asyncio
    async def test_validate_working_dir_path_traversal(self):
        from app.core.tools.shell_tool import ShellTool

        tool = ShellTool()
        is_valid, error = tool._validate_working_dir("../../../etc")
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_working_dir_absolute_path(self):
        from app.core.tools.shell_tool import ShellTool

        tool = ShellTool()
        is_valid, error = tool._validate_working_dir("/etc/passwd")
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_timeout_validation(self):
        from app.core.tools.shell_tool import ShellTool

        tool = ShellTool()
        result = await tool._on_call(command="ls", timeout=0.5)
        assert "error" in result

        result = await tool._on_call(command="ls", timeout=500)
        assert "error" in result


class TestCLIProviderExtended:
    @pytest.mark.asyncio
    async def test_validate_command_action_not_allowed(self):
        from app.core.capability.providers.cli import CLIProvider

        provider = CLIProvider()
        is_valid, error = provider._validate_command("git", "invalid_action", [])
        assert is_valid is False
        assert "not allowed" in error.lower()

    @pytest.mark.asyncio
    async def test_validate_command_argument_too_long(self):
        from app.core.capability.providers.cli import CLIProvider

        provider = CLIProvider()
        long_arg = "a" * 2000
        is_valid, error = provider._validate_command("git", "status", [long_arg])
        assert is_valid is False
        assert "too long" in error.lower()

    @pytest.mark.asyncio
    async def test_validate_command_null_in_args(self):
        from app.core.capability.providers.cli import CLIProvider

        provider = CLIProvider()
        is_valid, error = provider._validate_command("git", "status\0", [])
        assert is_valid is False
        assert "Null" in error

    @pytest.mark.asyncio
    async def test_sniffer_scan_path(self):
        from app.core.capability.providers.cli import CLISniffer

        sniffer = CLISniffer()
        found = sniffer.scan_path()
        assert isinstance(found, list)

    @pytest.mark.asyncio
    async def test_get_capability_not_found(self):
        from app.core.capability.providers.cli import CLIProvider

        provider = CLIProvider()
        cap = provider.get_capability("cli_nonexistent")
        assert cap is None
