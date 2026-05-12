import pytest
import asyncio
import time

from app.core.coordination.context.aggregator import (
    ContextAggregator,
    ContextEvent,
    ContextSource,
)


class TestContextAggregator:
    def setup_method(self):
        self.aggregator = ContextAggregator()

    def test_aggregator_initialization(self):
        assert self.aggregator._max_events == 200
        assert self.aggregator._buffer_max == 20
        assert len(self.aggregator._events) == 0

    @pytest.mark.asyncio
    async def test_ingest_single_event(self):
        event = ContextEvent(
            source=ContextSource.CHAT,
            data={"message": "test"},
        )
        await self.aggregator.ingest(event)
        assert len(self.aggregator._events) == 1

    @pytest.mark.asyncio
    async def test_ingest_event_deduplication(self):
        event = ContextEvent(
            source=ContextSource.CHAT,
            data={"message": "test"},
        )
        await self.aggregator.ingest(event)
        await self.aggregator.ingest(event)
        assert len(self.aggregator._events) == 1

    @pytest.mark.asyncio
    async def test_ingest_different_events_same_hash_different_data(self):
        event1 = ContextEvent(
            source=ContextSource.CHAT,
            data={"app": "app1"},
        )
        event2 = ContextEvent(
            source=ContextSource.CHAT,
            data={"app": "app2"},
        )
        await self.aggregator.ingest(event1)
        await self.aggregator.ingest(event2)
        assert len(self.aggregator._events) == 2

    @pytest.mark.asyncio
    async def test_ingest_respects_max_events(self):
        for i in range(250):
            event = ContextEvent(
                source=ContextSource.CHAT,
                data={"index": i},
            )
            await self.aggregator.ingest(event)
        assert len(self.aggregator._events) <= 200

    @pytest.mark.asyncio
    async def test_ingest_batch(self):
        events = [
            ContextEvent(source=ContextSource.CHAT, data={"app": f"app_{i}"})
            for i in range(10)
        ]
        await self.aggregator.ingest_batch(events)
        assert len(self.aggregator._events) == 10

    @pytest.mark.asyncio
    async def test_get_current_context(self):
        for i in range(5):
            await self.aggregator.ingest(
                ContextEvent(source=ContextSource.CHAT, data={"app": f"app_{i}"})
            )
        ctx = await self.aggregator.get_current_context()
        assert "event_count" in ctx
        assert ctx["event_count"] >= 5
        assert "sources" in ctx
        assert "recent_events" in ctx

    @pytest.mark.asyncio
    async def test_context_caching(self):
        await self.aggregator.ingest(
            ContextEvent(source=ContextSource.CHAT, data={"test": True})
        )
        ctx1 = await self.aggregator.get_current_context()
        ctx2 = await self.aggregator.get_current_context()
        assert ctx1 == ctx2

    def test_subscribe_unsubscribe(self):
        callback_called = []

        def callback(event):
            callback_called.append(event)

        self.aggregator.subscribe(callback)
        assert len(self.aggregator._subscribers) == 1

        self.aggregator.unsubscribe(callback)
        assert len(self.aggregator._subscribers) == 0

    @pytest.mark.asyncio
    async def test_subscriber_called_on_ingest(self):
        callback_called = []

        async def callback(event):
            callback_called.append(event)

        self.aggregator.subscribe(callback)
        await self.aggregator.ingest(
            ContextEvent(source=ContextSource.CHAT, data={"test": True})
        )
        assert len(callback_called) == 1

    @pytest.mark.asyncio
    async def test_subscriber_exception_handled(self):
        def bad_callback(event):
            raise ValueError("Test error")

        self.aggregator.subscribe(bad_callback)
        await self.aggregator.ingest(
            ContextEvent(source=ContextSource.CHAT, data={"test": True})
        )
        assert len(self.aggregator._subscribers) == 1

    def test_get_incremental_events(self):
        for i in range(5):
            self.aggregator._events.append(
                ContextEvent(
                    source=ContextSource.CHAT,
                    data={"i": i},
                    timestamp=time.time() - (5 - i),
                )
            )
        ts = time.time() - 3
        events = self.aggregator.get_incremental_events(ts)
        assert len(events) >= 2

    def test_get_events_since(self):
        now = time.time()
        for i in range(5):
            self.aggregator._events.append(
                ContextEvent(
                    source=ContextSource.CHAT,
                    data={"app": f"app_{i}"},
                    timestamp=now - (5 - i),
                )
            )
        events = self.aggregator.get_events_since(now - 2)
        assert isinstance(events, list)

    def test_build_activity_summary(self):
        events = [
            {
                "source": "chat",
                "data": {"app": "test_app", "action": "test_action"},
            }
            for _ in range(5)
        ]
        summary = self.aggregator.build_activity_summary(events)
        assert summary is not None
        assert summary["primary_source"] == "chat"
        assert summary["event_count"] == 5

    def test_build_activity_summary_empty(self):
        summary = self.aggregator.build_activity_summary([])
        assert summary is None

    def test_get_recent_summaries(self):
        events = [{"source": "chat", "data": {}} for _ in range(5)]
        self.aggregator.build_activity_summary(events[:2])
        self.aggregator.build_activity_summary(events[2:])
        summaries = self.aggregator.get_recent_summaries(limit=5)
        assert len(summaries) == 2

    def test_get_source_events(self):
        for i in range(25):
            self.aggregator._source_buffers[ContextSource.CHAT].append(
                ContextEvent(
                    source=ContextSource.CHAT,
                    data={"i": i},
                )
            )
        events = self.aggregator.get_source_events(ContextSource.CHAT, limit=10)
        assert len(events) == 10

    def test_get_source_events_respects_expiration(self):
        now = time.time()
        self.aggregator._source_buffers[ContextSource.CHAT].append(
            ContextEvent(
                source=ContextSource.CHAT,
                data={"i": 1},
                timestamp=now - 4000,
                ttl=3600,
            )
        )
        events = self.aggregator.get_source_events(ContextSource.CHAT)
        assert len(events) == 0

    @pytest.mark.asyncio
    async def test_get_context_for_llm(self):
        await self.aggregator.ingest(
            ContextEvent(
                source=ContextSource.CHAT,
                data={"app": "test", "title": "Test App"},
            )
        )
        ctx_str = await self.aggregator.get_context_for_llm()
        assert isinstance(ctx_str, str)
        assert len(ctx_str) > 0

    @pytest.mark.asyncio
    async def test_get_current_context_for_agent(self):
        await self.aggregator.ingest(
            ContextEvent(
                source=ContextSource.CHAT,
                data={"app": "test", "title": "Test App"},
            )
        )
        ctx = await self.aggregator.get_current_context_for_agent()
        assert "active_sources" in ctx
        assert "urgent_count" in ctx

    @pytest.mark.asyncio
    async def test_search_context(self):
        await self.aggregator.ingest(
            ContextEvent(source=ContextSource.CHAT, data={"message": "hello world"})
        )
        await self.aggregator.ingest(
            ContextEvent(source=ContextSource.EMAIL, data={"subject": "test email"})
        )
        results = await self.aggregator.search_context("hello")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_search_context_by_source(self):
        await self.aggregator.ingest(
            ContextEvent(source=ContextSource.EMAIL, data={"subject": "specific"})
        )
        results = await self.aggregator.search_context("email")
        assert len(results) >= 1


class TestContextEvent:
    def test_event_expiration(self):
        event = ContextEvent(
            source=ContextSource.CHAT,
            data={},
            ttl=1.0,
            timestamp=time.time() - 2,
        )
        assert event.is_expired()

    def test_event_not_expired(self):
        event = ContextEvent(
            source=ContextSource.CHAT,
            data={},
            ttl=3600,
        )
        assert not event.is_expired()

    def test_compute_hash(self):
        event = ContextEvent(
            source=ContextSource.CHAT,
            data={"app": "test", "title": "Test"},
        )
        hash1 = event.compute_hash()
        hash2 = event.compute_hash()
        assert hash1 == hash2

    def test_compute_hash_different_data(self):
        event1 = ContextEvent(
            source=ContextSource.CHAT,
            data={"app": "test1"},
        )
        event2 = ContextEvent(
            source=ContextSource.CHAT,
            data={"app": "test2"},
        )
        assert event1.compute_hash() != event2.compute_hash()


class TestContextAggregatorConcurrency:
    def setup_method(self):
        self.aggregator = ContextAggregator()

    @pytest.mark.asyncio
    async def test_concurrent_ingest(self):
        aggregator = ContextAggregator()

        async def ingest_events(count, prefix):
            for i in range(count):
                await aggregator.ingest(
                    ContextEvent(source=ContextSource.CHAT, data={"app": f"{prefix}_{i}"})
                )

        tasks = [ingest_events(20, f"batch{i}") for i in range(5)]
        await asyncio.gather(*tasks)

        ctx = await aggregator.get_current_context()
        assert ctx["event_count"] >= 50

    @pytest.mark.asyncio
    async def test_concurrent_context_access(self):
        aggregator = ContextAggregator()
        await aggregator.ingest(
            ContextEvent(source=ContextSource.CHAT, data={"app": "test"})
        )

        async def get_context():
            return await aggregator.get_current_context()

        results = await asyncio.gather(*[get_context() for _ in range(10)])
        assert all(r["event_count"] >= 1 for r in results)
