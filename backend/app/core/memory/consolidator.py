

class MemoryConsolidator:
    def __init__(self, llm_dispatcher=None):
        self._dispatcher = llm_dispatcher

    async def consolidate(self, short_term: list, long_term: list) -> None:
        if not short_term or not self._dispatcher:
            return
        recent_items = short_term[-20:]
        contents = [item.content for item in recent_items]
        combined = "\n".join(contents)
        messages = [
            {
                "role": "system",
                "content": (
                    "Consolidate these memories into a concise summary. "
                    "Remove duplicates and keep important information."
                ),
            },
            {"role": "user", "content": combined},
        ]
        from app.core.llm.dispatcher import TaskCategory

        response = await self._dispatcher.dispatch(TaskCategory.MEMORY, messages=messages)
        summary = response.choices[0].message.content
        import uuid

        from app.core.memory.manager import MemoryItem

        consolidated = MemoryItem(
            id=str(uuid.uuid4()),
            content=summary,
            metadata={"type": "consolidated", "source_count": len(recent_items)},
        )
        long_term.append(consolidated)
