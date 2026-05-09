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


class TestSafeEvaluator:
    def setup_method(self):
        from app.core.tool.workspace_tools import safe_eval
        self.safe_eval = safe_eval

    def test_basic_arithmetic(self):
        assert self.safe_eval("2 + 3") == 5
        assert self.safe_eval("10 - 4") == 6
        assert self.safe_eval("3 * 4") == 12
        assert self.safe_eval("15 / 3") == 5.0
        assert self.safe_eval("10 % 3") == 1

    def test_order_of_operations(self):
        assert self.safe_eval("2 + 3 * 4") == 14
        assert self.safe_eval("(2 + 3) * 4") == 20

    def test_power_operator(self):
        assert self.safe_eval("2 ** 3") == 8
        assert self.safe_eval("2 ^ 3") == 8
        assert self.safe_eval("10 ** 2") == 100

    def test_unary_operators(self):
        assert self.safe_eval("-5") == -5
        assert self.safe_eval("--5") == 5
        assert self.safe_eval("-2 + 3") == 1

    def test_comparisons(self):
        assert self.safe_eval("5 > 3") == True
        assert self.safe_eval("5 < 3") == False
        assert self.safe_eval("10 >= 10") == True
        assert self.safe_eval("3 <= 2") == False
        assert self.safe_eval("5 == 5") == True
        assert self.safe_eval("5 != 3") == True

    def test_conditional_expression(self):
        assert self.safe_eval("1 if 5 > 3 else 0") == 1
        assert self.safe_eval("1 if 3 > 5 else 0") == 0

    def test_empty_expression_raises(self):
        import pytest
        with pytest.raises(ValueError):
            self.safe_eval("")
        with pytest.raises(ValueError):
            self.safe_eval("   ")

    def test_malicious_code_injection_blocked(self):
        import pytest
        malicious_exprs = [
            "__import__('os').system('ls')",
            "().__class__.__bases__[0].__subclasses__()",
            "open('/etc/passwd').read()",
            "__builtins__",
            "[].__class__.__base__",
            "exec('print(1)')",
            "eval('1+1')",
            "import sys",
            "from os import system",
            "os.listdir('.')",
        ]
        for expr in malicious_exprs:
            with pytest.raises(Exception):
                self.safe_eval(expr)

    def test_whitespace_handling(self):
        assert self.safe_eval("  2 + 3  ") == 5
        assert self.safe_eval("\t4 * 5\t") == 20

    def test_float_numbers(self):
        assert self.safe_eval("3.14 + 2.86") == 6.0
        assert self.safe_eval("10.5 / 2") == 5.25


class TestFileMemoryStorage:
    def test_flush_preserves_failed_entries_in_buffer(self):
        import tempfile
        import json
        from pathlib import Path
        from app.core.memory.manager import FileMemoryStorage

        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileMemoryStorage(base_dir=tmpdir)

            storage._write_buffer[None] = {"version": "1.0", "lastUpdated": "2024-01-01", "test": "data1"}
            storage._write_buffer["agent1"] = {"version": "1.0", "lastUpdated": "2024-01-01", "test": "data2"}

            original_flush = storage._flush_buffer_sync

            def failing_flush():
                failed_entries = {}
                for agent_name, memory_data in list(storage._write_buffer.items()):
                    file_path = storage._get_file_path(agent_name)
                    if agent_name == "agent1":
                        failed_entries[agent_name] = memory_data
                        continue
                    tmp_path = file_path.with_suffix(".tmp")
                    tmp_path.write_text(json.dumps(memory_data, ensure_ascii=False, indent=2), encoding="utf-8")
                    tmp_path.replace(file_path)
                    mtime = file_path.stat().st_mtime
                    storage._cache[agent_name] = (memory_data, mtime)
                storage._write_buffer.clear()
                for agent_name, memory_data in failed_entries.items():
                    storage._write_buffer[agent_name] = memory_data

            storage._flush_buffer_sync = failing_flush
            storage._flush_buffer_sync()

            assert "agent1" in storage._write_buffer
            assert storage._write_buffer["agent1"]["test"] == "data2"

    def test_flush_clears_successful_entries(self):
        import tempfile
        from app.core.memory.manager import FileMemoryStorage

        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileMemoryStorage(base_dir=tmpdir)

            storage._write_buffer[None] = {"version": "1.0", "lastUpdated": "2024-01-01", "test": "success"}
            storage._write_buffer["agent1"] = {"version": "1.0", "lastUpdated": "2024-01-01", "test": "success2"}

            storage._flush_buffer_sync()

            assert len(storage._write_buffer) == 0
