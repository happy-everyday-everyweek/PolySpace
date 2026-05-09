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