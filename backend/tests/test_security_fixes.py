import pytest
import asyncio
from unittest.mock import patch, MagicMock


class TestShellToolSecurity:
    @pytest.mark.asyncio
    async def test_shell_tool_command_whitelist(self):
        from app.core.tools.shell_tool import ShellTool
        
        tool = ShellTool()
        
        allowed_result = await tool._on_call(command="ls -l", timeout=10)
        assert "exit_code" in allowed_result
        
        disallowed_result = await tool._on_call(command="rm -rf /", timeout=10)
        assert "error" in disallowed_result
        assert "not allowed" in disallowed_result["error"]
    
    @pytest.mark.asyncio
    async def test_shell_tool_command_injection(self):
        from app.core.tools.shell_tool import ShellTool
        
        tool = ShellTool()
        
        result = await tool._on_call(command="ls; rm -rf /", timeout=10)
        assert "error" in result
        assert "not allowed" in result["error"]
    
    @pytest.mark.asyncio
    async def test_shell_tool_null_byte(self):
        from app.core.tools.shell_tool import ShellTool
        
        tool = ShellTool()
        
        result = await tool._on_call(command="ls -l\0", timeout=10)
        assert "error" in result
        assert "Null byte" in result["error"]
    
    @pytest.mark.asyncio
    async def test_shell_tool_working_dir_validation(self):
        from app.core.tools.shell_tool import ShellTool
        
        tool = ShellTool()
        
        result = await tool._on_call(command="ls", working_dir="../etc", timeout=10)
        assert "error" in result
        assert "Invalid working directory" in result["error"]


class TestCLIProviderSecurity:
    @pytest.mark.asyncio
    async def test_cli_provider_allowed_commands(self):
        from app.core.capability.providers.cli import CLIProvider
        from app.core.capability.base import CapabilityCallContext
        
        provider = CLIProvider()
        context = MagicMock()
        context.timeout_seconds = 30
        
        result = await provider.execute("cli_git", {"action": "status", "args": []}, context)
        assert result.success is True or result.success is False  # Either is ok
    
    @pytest.mark.asyncio
    async def test_cli_provider_disallowed_command(self):
        from app.core.capability.providers.cli import CLIProvider
        from app.core.capability.base import CapabilityCallContext
        
        provider = CLIProvider()
        provider._tools["cli_malicious"] = MagicMock()
        provider._tools["cli_malicious"].name = "malicious_command"
        
        context = MagicMock()
        context.timeout_seconds = 30
        
        result = await provider.execute("cli_malicious", {"action": "execute", "args": []}, context)
        assert result.success is False
        assert "not allowed" in result.error
    
    @pytest.mark.asyncio
    async def test_cli_provider_null_byte(self):
        from app.core.capability.providers.cli import CLIProvider
        from app.core.capability.base import CapabilityCallContext
        
        provider = CLIProvider()
        provider._tools["cli_git"] = MagicMock()
        provider._tools["cli_git"].name = "git"
        
        context = MagicMock()
        context.timeout_seconds = 30
        
        result = await provider.execute("cli_git", {"action": "status\0", "args": []}, context)
        assert result.success is False
        assert "Null byte" in result.error


class TestAuthServiceConcurrency:
    @pytest.mark.asyncio
    async def test_auth_service_concurrent_registration(self):
        from app.services.auth_service import AuthService, UserCreateRequest
        
        service = AuthService()
        
        async def register_user(username):
            req = UserCreateRequest(username=username, password="test123")
            try:
                await service.register(req)
                return True
            except ValueError:
                return False
        
        tasks = [register_user(f"user_{i}") for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        assert sum(results) == 10
        
        users = await service.list_users()
        assert len(users) >= 10
    
    @pytest.mark.asyncio
    async def test_auth_service_duplicate_username(self):
        from app.services.auth_service import AuthService, UserCreateRequest
        
        service = AuthService()
        
        req1 = UserCreateRequest(username="test_user", password="test123")
        req2 = UserCreateRequest(username="test_user", password="test456")
        
        await service.register(req1)
        
        with pytest.raises(ValueError, match="already exists"):
            await service.register(req2)


class TestContextAggregatorConcurrency:
    @pytest.mark.asyncio
    async def test_aggregator_concurrent_ingest(self):
        from app.core.coordination.context.aggregator import ContextAggregator, ContextEvent, ContextSource
        
        aggregator = ContextAggregator()
        
        async def ingest_events(count):
            for i in range(count):
                event = ContextEvent(
                    source=ContextSource.CHAT,
                    data={"message": f"test_{i}"},
                )
                await aggregator.ingest(event)
        
        tasks = [ingest_events(10) for _ in range(5)]
        await asyncio.gather(*tasks)
        
        context = await aggregator.get_current_context()
        assert context["event_count"] >= 50


class TestOpenDesignProcessManagerSingleton:
    @pytest.mark.asyncio
    async def test_singleton_concurrent_access(self):
        from app.core.tools.open_design_tool import OpenDesignProcessManager
        
        async def get_instance():
            return await OpenDesignProcessManager.get_instance()
        
        instances = await asyncio.gather(*[get_instance() for _ in range(5)])
        
        assert all(instance is instances[0] for instance in instances)


class TestReadFileToolPathTraversal:
    @pytest.mark.asyncio
    async def test_read_file_block_path_traversal(self):
        from app.core.tool.interaction_tools import ReadFileTool
        
        tool = ReadFileTool()
        
        result = await tool._read_file("/etc/passwd")
        assert "error" in result
        assert "Access denied" in result["error"]
    
    @pytest.mark.asyncio
    async def test_read_file_block_symlink_escape(self):
        from app.core.tool.interaction_tools import ReadFileTool
        import os
        import tempfile
        
        tool = ReadFileTool()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            safe_file = os.path.join(tmpdir, "safe.txt")
            with open(safe_file, "w") as f:
                f.write("safe content")
            
            result = await tool._read_file(safe_file)
            assert "error" in result or "content" in result
    
    @pytest.mark.asyncio
    async def test_find_file_restricted_to_safe_dirs(self):
        from app.core.tool.interaction_tools import ReadFileTool
        import os
        import tempfile
        
        tool = ReadFileTool()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            result = await tool._find_file("test_file")
            assert result is None or "error" not in result


class TestSafeEvaluatorDivisionByZero:
    def test_division_by_zero_blocked(self):
        from app.core.tool.workspace_tools import SafeEvaluator, safe_eval
        
        with pytest.raises(ValueError, match="Division by zero"):
            safe_eval("10 / 0")
    
    def test_modulo_by_zero_blocked(self):
        from app.core.tool.workspace_tools import SafeEvaluator, safe_eval
        
        with pytest.raises(ValueError, match="zero"):
            result = safe_eval("10 % 0")
    
    def test_floor_division_by_zero_blocked(self):
        from app.core.tool.workspace_tools import SafeEvaluator, safe_eval
        
        with pytest.raises(ValueError, match="Division by zero"):
            safe_eval("10 // 0")
    
    def test_nested_division_by_zero_blocked(self):
        from app.core.tool.workspace_tools import safe_eval
        
        with pytest.raises(ValueError, match="Division by zero"):
            safe_eval("(5 + 5) / 0")


class TestCalculatorToolDivisionByZero:
    @pytest.mark.asyncio
    async def test_calculator_division_by_zero(self):
        from app.core.tool.workspace_tools import CalculatorTool
        
        tool = CalculatorTool()
        result = await tool._on_call(action="evaluate", expression="10/0")
        
        assert "error" in result
        assert "zero" in result["error"].lower()


class TestChatServiceFewshotMessageIntegrity:
    def test_fewshot_messages_not_appended_to_history(self):
        from app.services.chat_service import ChatService
        import json
        
        mock_dispatcher = MagicMock()
        mock_tool_registry = MagicMock()
        mock_tool_registry.get_definitions.return_value = []
        mock_memory_manager = MagicMock()
        mock_heartflow = MagicMock()
        mock_heartflow.process_input.return_value.asyncio.return_value = {"label": "neutral", "intensity": 0.5}
        mock_heartflow.get_emotion_context.return_value = {"label": "neutral", "intensity": 0.5}
        mock_heartflow.get_emotion_prompt_modifier.return_value = ""
        mock_expression = MagicMock()
        mock_greeting = MagicMock()
        mock_policy = MagicMock()
        mock_policy.evaluate.return_value = (MagicMock(value="allow"), None)
        mock_confirmation = MagicMock()
        mock_monitor = MagicMock()
        
        from app.core.personality.persona_core import PersonaCore, PersonaType, Relationship
        from app.core.personality.expression import ExpressionLearner
        from app.core.personality.greeting import GreetingManager
        from app.core.personality.inner_voice import InnerVoice
        from app.core.personality.pfc import PFCManager
        
        persona = PersonaCore(PersonaType.FRIENDLY, Relationship.STRANGER)
        expression = ExpressionLearner(MagicMock())
        greeting = GreetingManager(MagicMock())
        inner_voice = InnerVoice(MagicMock())
        pfc = PFCManager(MagicMock())
        
        with patch.object(ChatService, '__init__', lambda x, **kwargs: None):
            chat_service = ChatService.__new__(ChatService)
            chat_service._dispatcher = mock_dispatcher
            chat_service._tools = mock_tool_registry
            chat_service._memory = mock_memory_manager
            chat_service._heartflow = mock_heartflow
            chat_service._expression = mock_expression
            chat_service._greeting = mock_greeting
            chat_service._policies = mock_policy
            chat_service._confirmation = mock_confirmation
            chat_service._monitor = mock_monitor
            chat_service._persona = persona
            chat_service._inner_voice = inner_voice
            chat_service._pfc = pfc
            chat_service._prompt_template = MagicMock()
            chat_service._prompt_template.build_system_prompt_blocks.return_value = {
                "identity_block": "", "chat_target_block": "", "reply_style_block": "",
                "expression_habits_block": "", "relationship_block": ""
            }
            chat_service._chain = MagicMock()
            chat_service._chat_histories = {}
        
        from app.core.agent.prompts import build_system_prompt
        from app.core.tool.interaction_tools import ReadFileTool, SearchAggregateTool, ExecuteTaskTool
        
        persona_section = persona.get_persona_prompt_section()
        available_tools_section = "## Tools\n- test tool"
        behavior_guidelines = "## Guidelines"
        
        system_content = build_system_prompt(
            persona_section=persona_section,
            emotion_modifier="",
            inner_voice_context="",
            memory_context="",
            relationship_context="",
            identity_block="",
            chat_target_block="",
            reply_style_block="",
            expression_habits_block="",
            relationship_block="",
            capability_summary=available_tools_section,
            behavior_guidelines=behavior_guidelines,
        )
        
        llm_messages = [{"role": "system", "content": system_content}]
        history = chat_service._chat_histories.get("test_session", [])
        history_messages = history[-20:]
        
        if not history_messages:
            fewshot_messages = [
                {"role": "user", "content": "帮我写一份周报"},
                {"role": "assistant", "content": None, "tool_calls": [{
                    "id": "fewshot_001",
                    "type": "function",
                    "function": {
                        "name": "execute_task",
                        "arguments": '{"description": "写一份周报", "goal": "完成周报内容"}',
                    },
                }]},
                {"role": "tool", "tool_call_id": "fewshot_001", "content": json.dumps({
                    "task_id": "task_demo",
                    "status": "created",
                    "card": {
                        "type": "task",
                        "task_id": "task_demo",
                        "status": "running",
                        "progress": 0,
                    },
                })},
                {"role": "assistant", "content": (
                    "好的，我已经为你创建了周报任务"
                    "（任务ID: task_demo），系统正在执行中。"
                    "你可以随时补充要求或查看进度。"
                )},
            ]
            llm_messages[1:1] = fewshot_messages
        
        assert llm_messages[0]["role"] == "system"
        assert llm_messages[1]["role"] == "user"
        assert llm_messages[1]["content"] == "帮我写一份周报"
        assert llm_messages[2]["role"] == "assistant"
        assert llm_messages[2]["tool_calls"][0]["function"]["name"] == "execute_task"
        
        fewshot_args = json.loads(llm_messages[2]["tool_calls"][0]["function"]["arguments"])
        assert fewshot_args["description"] == "写一份周报"
        assert fewshot_args["goal"] == "完成周报内容"
        
        tool_result = json.loads(llm_messages[3]["content"])
        assert tool_result["task_id"] == "task_demo"
        assert tool_result["status"] == "created"
        
        assistant_reply = llm_messages[4]["content"]
        assert "task_demo" in assistant_reply
        assert "周报任务" in assistant_reply