import logging
from typing import Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class ServiceContainer:
    def __init__(self):
        self._services: dict[str, Any] = {}
        self._started: bool = False

    def register(self, name: str, service: Any) -> None:
        self._services[name] = service
        logger.debug("Service registered: %s", name)

    def get(self, name: str) -> Optional[Any]:
        return self._services.get(name)

    def require(self, name: str) -> Any:
        service = self._services.get(name)
        if service is None:
            from app.core.exceptions import ServiceUnavailableError
            raise ServiceUnavailableError(service=name)
        return service

    @property
    def is_started(self) -> bool:
        return self._started

    async def start_all(self) -> None:
        if self._started:
            return

        logger.info("Starting all services...")

        memory_manager = self._services.get("memory_manager")
        if memory_manager and hasattr(memory_manager, "initialize"):
            await memory_manager.initialize()
            logger.info("MemoryManager initialized")

        memory_dreamer = self._services.get("memory_dreamer")
        if memory_dreamer and hasattr(memory_dreamer, "start"):
            await memory_dreamer.start()
            logger.info("MemoryDreamer started")

        cron_service = self._services.get("cron_service")
        if cron_service and hasattr(cron_service, "start"):
            await cron_service.start()
            logger.info("CronService started")

        evolution_engine = self._services.get("evolution_engine")
        if evolution_engine and hasattr(evolution_engine, "start"):
            await evolution_engine.start()
            logger.info("EvolutionEngine started")

        self._started = True
        logger.info("All services started successfully")

    async def stop_all(self) -> None:
        if not self._started:
            return

        logger.info("Stopping all services...")

        evolution_engine = self._services.get("evolution_engine")
        if evolution_engine and hasattr(evolution_engine, "stop"):
            await evolution_engine.stop()
            logger.info("EvolutionEngine stopped")

        cron_service = self._services.get("cron_service")
        if cron_service and hasattr(cron_service, "stop"):
            await cron_service.stop()
            logger.info("CronService stopped")

        memory_dreamer = self._services.get("memory_dreamer")
        if memory_dreamer and hasattr(memory_dreamer, "stop"):
            await memory_dreamer.stop()
            logger.info("MemoryDreamer stopped")

        self._started = False
        logger.info("All services stopped")

    def list_services(self) -> dict[str, str]:
        return {
            name: type(svc).__name__
            for name, svc in self._services.items()
        }


container = ServiceContainer()


def _init_services() -> None:
    from app.core.agent.cron import CronService
    from app.core.agent.evolution import SelfEvolutionEngine
    from app.core.agent.session import SessionRouter
    from app.core.llm.dispatcher import ModelDispatcher
    from app.core.llm.gateway import LLMGateway
    from app.core.memory.dreaming import MemoryDreamer
    from app.core.memory.manager import MemoryManager
    from app.core.safety.monitor import RuntimeMonitor
    from app.core.safety.policies import PolicyEngine
    from app.core.tool.registry import ToolRegistry

    if not container.get("policy_engine"):
        policy_engine = PolicyEngine(settings.POLICIES_PATH)
        container.register("policy_engine", policy_engine)

    if not container.get("runtime_monitor"):
        runtime_monitor = RuntimeMonitor()
        container.register("runtime_monitor", runtime_monitor)

    if not container.get("llm_gateway"):
        llm_gateway = LLMGateway()
        container.register("llm_gateway", llm_gateway)

    if not container.get("model_dispatcher"):
        from app.core.llm.config_store import get_model_config_store
        store = get_model_config_store()
        dispatcher_config = store.get_dispatcher_config()
        model_dispatcher = ModelDispatcher(config=dispatcher_config)
        container.register("model_dispatcher", model_dispatcher)

    if not container.get("tool_registry"):
        tool_registry = ToolRegistry()
        container.register("tool_registry", tool_registry)

    if not container.get("capability_registry"):
        from app.core.capability.providers.cli import CLIProvider
        from app.core.capability.providers.device_bridge import DeviceBridgeProvider
        from app.core.capability.providers.internal import InternalProvider
        from app.core.capability.providers.mcp import MCPProvider
        from app.core.capability.providers.skill import SkillProvider
        from app.core.capability.registry import capability_registry
        capability_registry.add_provider(InternalProvider())
        capability_registry.add_provider(MCPProvider())
        capability_registry.add_provider(SkillProvider())
        capability_registry.add_provider(CLIProvider())
        capability_registry.add_provider(DeviceBridgeProvider())
        container.register("capability_registry", capability_registry)

    if not container.get("memory_manager"):
        memory_manager = MemoryManager()
        container.register("memory_manager", memory_manager)

    if not container.get("memory_dreamer"):
        memory_dreamer = MemoryDreamer()
        container.register("memory_dreamer", memory_dreamer)

    if not container.get("cron_service"):
        cron_service = CronService(
            store_path=str(settings.cron_store_path),
        )
        container.register("cron_service", cron_service)

    if not container.get("evolution_engine"):
        evolution_engine = SelfEvolutionEngine(
            storage_dir=str(settings.evolution_dir),
        )
        container.register("evolution_engine", evolution_engine)

    if not container.get("session_router"):
        session_router = SessionRouter()
        container.register("session_router", session_router)

    if not container.get("chat_service"):
        from app.core.personality.expression import ExpressionLearner
        from app.core.personality.greeting import GreetingManager
        from app.core.personality.heartflow import HeartFlow
        from app.core.safety.confirmation import ConfirmationManager
        from app.services.chat_service import ChatService

        model_dispatcher = container.require("model_dispatcher")
        tool_registry = container.require("tool_registry")
        memory_manager = container.require("memory_manager")
        policy_engine = container.require("policy_engine")
        runtime_monitor = container.require("runtime_monitor")

        heartflow = HeartFlow(model_dispatcher)
        expression_learner = ExpressionLearner(model_dispatcher)
        greeting_manager = GreetingManager(model_dispatcher)
        confirmation_manager = ConfirmationManager()

        chat_service = ChatService(
            model_dispatcher=model_dispatcher,
            tool_registry=tool_registry,
            memory_manager=memory_manager,
            heartflow=heartflow,
            expression_learner=expression_learner,
            greeting_manager=greeting_manager,
            policy_engine=policy_engine,
            confirmation_manager=confirmation_manager,
            runtime_monitor=runtime_monitor,
        )
        container.register("chat_service", chat_service)

    logger.info("Services registered: %s", list(container._services.keys()))


def init_services() -> None:
    _init_services()
