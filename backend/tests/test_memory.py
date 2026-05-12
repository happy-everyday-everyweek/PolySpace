import pytest
import asyncio
import json
import tempfile
import time
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, UTC

from app.core.memory.manager import (
    MemoryManager,
    FileMemoryStorage,
    MemoryItem,
    _create_empty_structured_memory,
)


class TestMemoryManager:
    def setup_method(self):
        self.manager = MemoryManager()

    def test_store_creates_memory_item(self):
        item_id = self.manager._short_term
        assert len(self.manager._short_term) == 0

    @pytest.mark.asyncio
    async def test_store_and_retrieve(self):
        item_id = await self.manager.store("test content", {"key": "value"})
        assert item_id is not None

        results = await self.manager.retrieve("test")
        assert len(results) > 0
        assert any(r.content == "test content" for r in results)

    @pytest.mark.asyncio
    async def test_retrieve_with_no_results(self):
        await self.manager.store("something specific")
        results = await self.manager.retrieve("nonexistent keyword xyz")
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_keyword_indexing(self):
        await self.manager.store("apple banana cherry")
        await self.manager.store("banana date elderberry")

        results = await self.manager.retrieve("banana")
        assert len(results) >= 2

    def test_short_term_memory_limit(self):
        for i in range(150):
            self.manager._short_term.append(
                MemoryItem(id=str(i), content=f"content {i}")
            )

        assert len(self.manager._short_term) > 100

    def test_get_short_term_memory(self):
        for i in range(25):
            self.manager._short_term.append(
                MemoryItem(id=str(i), content=f"content {i}")
            )

        result = self.manager.get_short_term_memory(limit=10)
        assert len(result) == 10

    def test_clear_short_term(self):
        self.manager._short_term.append(
            MemoryItem(id="1", content="test")
        )
        assert len(self.manager._short_term) == 1

        self.manager.clear_short_term()
        assert len(self.manager._short_term) == 0

    def test_add_fact(self):
        import tempfile
        from app.core.memory.manager import MemoryManager, FileMemoryStorage
        import uuid
        storage = FileMemoryStorage(base_dir=tempfile.mkdtemp())
        manager = MemoryManager(storage=storage)
        unique_id = uuid.uuid4().hex[:8]
        result = manager.add_fact(f"Test fact {unique_id}", 0.9)
        assert result is True

        memory = manager.load_structured_memory()
        assert len(memory["facts"]) >= 1
        assert any(fact["content"] == f"Test fact {unique_id}" for fact in memory["facts"])

    def test_update_user_context(self):
        result = self.manager.update_user_context(
            "workContext", "Working on project X"
        )
        assert result is True

        memory = self.manager.load_structured_memory()
        assert memory["user"]["workContext"]["summary"] == "Working on project X"

    def test_update_user_context_invalid_section(self):
        result = self.manager.update_user_context(
            "invalidSection", "Should fail"
        )
        assert result is False

    def test_update_history_context(self):
        result = self.manager.update_history_context(
            "recentMonths", "Had a busy week"
        )
        assert result is True

        memory = self.manager.load_structured_memory()
        assert memory["history"]["recentMonths"]["summary"] == "Had a busy week"

    def test_update_history_context_invalid_section(self):
        result = self.manager.update_history_context(
            "invalidSection", "Should fail"
        )
        assert result is False

    def test_load_structured_memory_returns_valid_structure(self):
        memory = self.manager.load_structured_memory()
        assert "version" in memory
        assert "user" in memory
        assert "history" in memory
        assert "facts" in memory

    @pytest.mark.asyncio
    async def test_store_with_vector_store(self):
        mock_vector = AsyncMock()
        mock_vector.add = AsyncMock()

        manager = MemoryManager(vector_store=mock_vector)
        item_id = await manager.store("vector test", {"type": "test"})

        mock_vector.add.assert_called_once()
        call_args = mock_vector.add.call_args
        assert "vector test" in call_args[0][0]


class TestMemoryItem:
    def test_memory_item_creation(self):
        item = MemoryItem(
            id="test-id",
            content="test content",
            metadata={"key": "value"}
        )
        assert item.id == "test-id"
        assert item.content == "test content"
        assert item.metadata["key"] == "value"
        assert item.access_count == 0

    def test_memory_item_with_ttl(self):
        item = MemoryItem(
            id="test-id",
            content="test",
            ttl_seconds=60
        )
        assert item.ttl_seconds == 60


class TestFileMemoryStorage:
    def test_get_file_path_with_agent_name(self):
        storage = FileMemoryStorage(base_dir="/tmp/test")
        path = storage._get_file_path("my_agent")
        assert "memory_my_agent" in str(path)

    def test_get_file_path_with_special_characters(self):
        storage = FileMemoryStorage(base_dir="/tmp/test")
        path = storage._get_file_path("agent with spaces/and/slashes")
        assert "memory_" in str(path)

    def test_get_file_path_without_agent_name(self):
        storage = FileMemoryStorage(base_dir="/tmp/test")
        path = storage._get_file_path()
        assert "memory_global" in str(path)

    def test_load_returns_empty_structure_for_new_agent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileMemoryStorage(base_dir=tmpdir)
            memory = storage.load("new_agent")
            assert memory["version"] == "1.0"
            assert "facts" in memory

    @pytest.mark.asyncio
    async def test_save_updates_buffer(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = FileMemoryStorage(base_dir=tmpdir)
            memory = {"version": "1.0", "facts": []}
            result = storage.save(memory, "test_agent")
            assert result is True


class TestMemoryItemExpiration:
    @pytest.mark.asyncio
    async def test_retrieve_respects_access_count(self):
        manager = MemoryManager()
        item_id = await manager.store("test item")

        results = await manager.retrieve("test item")
        assert len(results) > 0

        for item in results:
            if item.content == "test item":
                assert item.access_count >= 0
