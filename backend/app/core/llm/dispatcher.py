from typing import Any, Optional

from app.core.llm.gateway import llm_gateway
from app.core.llm.models import ModelConfig, ModelDispatcherConfig


class TaskCategory:
    PLANNING = "planning"
    DAILY = "daily"
    INTENT = "intent"
    MEMORY = "memory"
    BROWSER = "browser"
    SCREEN_OPERATION = "screen_operation"
    MULTIMODAL = "multimodal"
    CUSTOM = "custom"


class ModelDispatcher:
    def __init__(self, config: ModelDispatcherConfig):
        self._config = config

    @property
    def config(self) -> ModelDispatcherConfig:
        return self._config

    def resolve_model(self, task_category: str, **kwargs) -> ModelConfig:
        if not self._config.has_tier_models:
            return self._config.base_model

        if task_category == TaskCategory.PLANNING:
            return self._config.strong_model or self._config.base_model

        if task_category == TaskCategory.DAILY:
            return self._config.performance_model or self._config.base_model

        if task_category in (TaskCategory.INTENT, TaskCategory.MEMORY, TaskCategory.BROWSER):
            return self._config.cost_effective_model or self._config.performance_model or self._config.base_model

        if task_category == TaskCategory.SCREEN_OPERATION:
            screen_model = self._config.get_screen_model()
            if screen_model:
                return screen_model
            return self._config.performance_model or self._config.base_model

        if task_category == TaskCategory.MULTIMODAL:
            mm_model = self._config.get_multimodal_model()
            if mm_model:
                return mm_model
            return self._config.base_model

        if task_category == TaskCategory.CUSTOM:
            custom_model_name = kwargs.get("vertical_model_name")
            if custom_model_name:
                vm = self._config.get_vertical_model(custom_model_name)
                if vm:
                    return vm
            return self._config.cost_effective_model or self._config.base_model

        return self._config.performance_model or self._config.base_model

    def _get_model_kwargs(self, model_config: ModelConfig) -> dict:
        kwargs: dict = {}
        if model_config.api_key:
            kwargs["api_key"] = model_config.api_key
        if model_config.api_base:
            kwargs["api_base"] = model_config.api_base
        return kwargs

    async def should_use_vertical_model(self, query: str, vertical_model: ModelConfig) -> bool:
        if not self._config.cost_effective_model:
            return False
        if not vertical_model.scene_description:
            return False
        model = self._config.cost_effective_model
        model_id = llm_gateway.get_model_id(model)
        model_kwargs = self._get_model_kwargs(model)
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a model router. Given a user query and a vertical model's scene description, "
                    "determine if the query should be handled by the vertical model. "
                    "Respond with only 'yes' or 'no'."
                ),
            },
            {
                "role": "user",
                "content": f"Query: {query}\n\nVertical model scene: {vertical_model.scene_description}",
            },
        ]
        response = await llm_gateway.acompletion(model=model_id, messages=messages, **model_kwargs)
        answer = response.choices[0].message.content.strip().lower()
        return answer == "yes"

    async def dispatch(
        self,
        task_category: str,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        **kwargs,
    ) -> Any:
        model_config = self.resolve_model(task_category, **kwargs)

        needs_multimodal = kwargs.get("has_multimodal_input", False)
        current_capabilities = model_config.capabilities
        if needs_multimodal and "vision" not in current_capabilities:
            mm_model = self._config.get_multimodal_model()
            if mm_model:
                mm_model_id = llm_gateway.get_model_id(mm_model)
                mm_kwargs = self._get_model_kwargs(mm_model)
                mm_messages = [
                    {
                        "role": "system",
                        "content": "Describe the visual content in detail for another model to understand.",
                    }
                ] + messages
                mm_response = await llm_gateway.acompletion(model=mm_model_id, messages=mm_messages, **mm_kwargs)
                description = mm_response.choices[0].message.content
                enriched_messages = []
                for msg in messages:
                    enriched_messages.append(msg)
                enriched_messages.append({
                    "role": "system",
                    "content": f"Visual content description: {description}",
                })
                if tools:
                    ask_mm_tool = {
                        "type": "function",
                        "function": {
                            "name": "ask_multimodal_model",
                            "description": "Ask the multimodal model about visual content (images, videos, audio)",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "question": {
                                        "type": "string",
                                        "description": "Question about the visual content",
                                    }
                                },
                                "required": ["question"],
                            },
                        },
                    }
                    tools = tools + [ask_mm_tool]
                messages = enriched_messages

        model_id = llm_gateway.get_model_id(model_config)
        model_kwargs = self._get_model_kwargs(model_config)
        return await llm_gateway.acompletion(model=model_id, messages=messages, tools=tools, **model_kwargs)

    async def dispatch_stream(
        self,
        task_category: str,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        **kwargs,
    ):
        model_config = self.resolve_model(task_category, **kwargs)
        model_id = llm_gateway.get_model_id(model_config)
        model_kwargs = self._get_model_kwargs(model_config)
        stream_kwargs = {k: v for k, v in kwargs.items() if k not in (
            "has_multimodal_input", "vertical_model_name",
        )}
        stream_kwargs.update(model_kwargs)
        async for chunk in llm_gateway.acompletion_stream(
            model=model_id, messages=messages, tools=tools, **stream_kwargs
        ):
            yield chunk


def get_model_dispatcher() -> ModelDispatcher:
    from app.dependencies import container
    dispatcher = container.get("model_dispatcher")
    if dispatcher is not None:
        return dispatcher
    from app.core.llm.config_store import get_model_config_store
    store = get_model_config_store()
    config = store.get_dispatcher_config()
    return ModelDispatcher(config=config)
