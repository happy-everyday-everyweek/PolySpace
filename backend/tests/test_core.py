from app.config import set_test_mode
from app.core.exceptions import LLMError, PolySpaceError, ServiceUnavailableError
from app.core.safety.monitor import RuntimeMonitor
from app.core.safety.policies import Policy, PolicyAction, PolicyEngine, RiskLevel

set_test_mode(True)


class TestPolicyEngine:
    def setup_method(self):
        self.engine = PolicyEngine()

    def test_no_policies_allows_everything(self):
        action, msg = self.engine.evaluate("any action")
        assert action == PolicyAction.ALLOW
        assert msg is None

    def test_block_policy(self):
        policy = Policy(
            name="test_block",
            level=RiskLevel.HIGH,
            patterns=[r"rm\s+-rf"],
            action=PolicyAction.BLOCK,
            message="Dangerous command",
        )
        self.engine.add_policy(policy)
        action, msg = self.engine.evaluate("rm -rf /")
        assert action == PolicyAction.BLOCK
        assert msg == "Dangerous command"

    def test_notify_policy(self):
        policy = Policy(
            name="test_notify",
            level=RiskLevel.MEDIUM,
            patterns=[r"sudo"],
            action=PolicyAction.NOTIFY,
            message="Sudo usage detected",
        )
        self.engine.add_policy(policy)
        action, msg = self.engine.evaluate("sudo apt install")
        assert action == PolicyAction.NOTIFY
        assert msg == "Sudo usage detected"

    def test_remove_policy(self):
        policy = Policy(
            name="removable",
            level=RiskLevel.LOW,
            patterns=[r"test"],
            action=PolicyAction.NOTIFY,
            message="test",
        )
        self.engine.add_policy(policy)
        assert len(self.engine.list_policies()) == 1
        self.engine.remove_policy("removable")
        assert len(self.engine.list_policies()) == 0

    def test_is_high_risk(self):
        policy = Policy(
            name="high_risk_test",
            level=RiskLevel.HIGH,
            patterns=[r"dangerous"],
            action=PolicyAction.BLOCK,
            message="blocked",
        )
        self.engine.add_policy(policy)
        assert self.engine.is_high_risk("dangerous action")
        assert not self.engine.is_high_risk("safe action")

    def test_compiled_patterns_reused(self):
        policy = Policy(
            name="regex_test",
            level=RiskLevel.MEDIUM,
            patterns=[r"\bdelete\b"],
            action=PolicyAction.CONFIRM,
            message="confirm deletion",
        )
        assert len(policy._compiled_patterns) == 1
        self.engine.add_policy(policy)
        action, _ = self.engine.evaluate("delete all files")
        assert action == PolicyAction.CONFIRM


class TestRuntimeMonitor:
    def setup_method(self):
        self.monitor = RuntimeMonitor()

    def test_record_tool_call(self):
        self.monitor.record_tool_call("test_tool")
        stats = self.monitor.get_stats()
        assert stats["total_calls"] == 1

    def test_rate_limit_ok_under_limit(self):
        for i in range(10):
            self.monitor.record_tool_call(f"tool_{i}")
        assert self.monitor.check_rate_limit()

    def test_jitter_detection(self):
        for i in range(6):
            self.monitor.record_tool_call(f"different_tool_{i}")
        assert self.monitor.detect_jitter()

    def test_no_jitter_same_tool(self):
        for i in range(10):
            self.monitor.record_tool_call("same_tool")
        assert not self.monitor.detect_jitter()

    def test_stats_caching(self):
        self.monitor.record_tool_call("tool1")
        stats1 = self.monitor.get_stats()
        stats2 = self.monitor.get_stats()
        assert stats1 is stats2

    def test_deque_maxlen(self):
        for i in range(1100):
            self.monitor.record_tool_call(f"tool_{i}")
        assert len(self.monitor._tool_call_history) == self.monitor.MAX_HISTORY


class TestExceptions:
    def test_polyspace_error(self):
        err = PolySpaceError("test error", code="TEST_ERROR", status_code=400)
        assert err.message == "test error"
        assert err.code == "TEST_ERROR"
        assert err.status_code == 400

    def test_llm_error(self):
        err = LLMError("model failed", model="gpt-4")
        assert err.code == "LLM_ERROR"
        assert err.status_code == 502
        assert err.model == "gpt-4"

    def test_service_unavailable(self):
        err = ServiceUnavailableError(service="chat_service")
        assert err.code == "SERVICE_UNAVAILABLE"
        assert err.status_code == 503
        assert err.service == "chat_service"
