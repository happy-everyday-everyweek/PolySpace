from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MemoryPoint:
    category: str
    content: str
    weight: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)
    source: str = ""


@dataclass
class Person:
    person_id: str
    name: str = ""
    nickname: str = ""
    memory_points: list[MemoryPoint] = field(default_factory=list)
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    interaction_count: int = 0
    relationship_tags: list[str] = field(default_factory=list)


class PersonInfoManager:
    def __init__(self, llm_dispatcher):
        self._dispatcher = llm_dispatcher
        self._persons: dict[str, Person] = {}

    def get_or_create_person(self, person_id: str) -> Person:
        if person_id not in self._persons:
            self._persons[person_id] = Person(person_id=person_id)
        return self._persons[person_id]

    async def assign_name(self, person_id: str, context: str = "") -> str:
        person = self.get_or_create_person(person_id)
        if person.name:
            return person.name
        if not context:
            return f"User_{person_id[:6]}"
        messages = [
            {
                "role": "system",
                "content": (
                    "Based on the conversation context, suggest a short friendly name "
                    "for this person. Return JSON: {name}. "
                    "Use a natural, casual name. Do not use real names from the context."
                ),
            },
            {"role": "user", "content": context},
        ]
        from app.core.llm.dispatcher import TaskCategory

        response = await self._dispatcher.dispatch(TaskCategory.INTENT, messages=messages)
        content = response.choices[0].message.content
        try:
            import json
            data = json.loads(content)
            name = data.get("name", f"User_{person_id[:6]}")
            person.name = name
            return name
        except (json.JSONDecodeError, ValueError):
            person.name = f"User_{person_id[:6]}"
            return person.name

    async def add_memory_point(self, person_id: str, category: str,
                                content: str, weight: float = 1.0) -> None:
        person = self.get_or_create_person(person_id)
        for mp in person.memory_points:
            if self._compute_similarity(mp.content, content) > 0.8:
                mp.weight = max(mp.weight, weight)
                mp.content = content
                return
        person.memory_points.append(MemoryPoint(
            category=category, content=content, weight=weight
        ))
        if len(person.memory_points) > 50:
            person.memory_points.sort(key=lambda m: m.weight, reverse=True)
            person.memory_points = person.memory_points[:50]

    async def extract_memories(self, person_id: str, conversation: str) -> list[MemoryPoint]:
        messages = [
            {
                "role": "system",
                "content": (
                    "Extract memorable facts about the user from this conversation. "
                    "Return JSON array: [{category, content, weight: 0.0-1.0}]. "
                    "Categories: preference, fact, opinion, experience, relationship, goal. "
                    "Focus on personally meaningful and distinctive information."
                ),
            },
            {"role": "user", "content": conversation},
        ]
        from app.core.llm.dispatcher import TaskCategory

        response = await self._dispatcher.dispatch(TaskCategory.MEMORY, messages=messages)
        content = response.choices[0].message.content
        extracted = []
        try:
            import json
            data = json.loads(content)
            if isinstance(data, list):
                for item in data:
                    category = item.get("category", "fact")
                    mem_content = item.get("content", "")
                    weight = float(item.get("weight", 0.5))
                    if mem_content:
                        await self.add_memory_point(person_id, category, mem_content, weight)
                        extracted.append(MemoryPoint(category=category, content=mem_content, weight=weight))
        except (json.JSONDecodeError, ValueError):
            pass
        return extracted

    def get_relevant_memories(self, person_id: str, query: str, top_k: int = 5) -> list[MemoryPoint]:
        person = self.get_or_create_person(person_id)
        if not person.memory_points:
            return []
        scored = []
        for mp in person.memory_points:
            sim = self._compute_similarity(mp.content, query)
            score = sim * mp.weight
            scored.append((score, mp))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [mp for _, mp in scored[:top_k]]

    def get_person_summary(self, person_id: str) -> str:
        person = self.get_or_create_person(person_id)
        parts = [f"Name: {person.name or 'Unknown'}"]
        if person.nickname:
            parts.append(f"Nickname: {person.nickname}")
        parts.append(f"Interactions: {person.interaction_count}")
        if person.relationship_tags:
            parts.append(f"Relationship: {', '.join(person.relationship_tags)}")
        if person.memory_points:
            categories = {}
            for mp in person.memory_points:
                categories.setdefault(mp.category, []).append(mp.content)
            for cat, items in categories.items():
                parts.append(f"{cat}: {'; '.join(items[:3])}")
        return "\n".join(parts)

    def update_interaction(self, person_id: str) -> None:
        person = self.get_or_create_person(person_id)
        person.last_seen = datetime.now()
        person.interaction_count += 1

    def sync_relationship_to_persona(self, person_id: str, persona_core) -> None:
        person = self.get_or_create_person(person_id)
        days_known = (datetime.now() - person.first_seen).days
        avg_depth = sum(mp.weight for mp in person.memory_points) / max(1, len(person.memory_points))
        persona_core.update_relationship(
            interaction_count=person.interaction_count,
            avg_depth=avg_depth,
            days_known=days_known,
        )
        stage = persona_core.relationship.value
        if stage not in person.relationship_tags:
            person.relationship_tags = [stage]

    def _compute_similarity(self, a: str, b: str) -> float:
        if a == b:
            return 1.0
        set_a = set(a.lower().split())
        set_b = set(b.lower().split())
        if not set_a or not set_b:
            return 0.0
        intersection = set_a & set_b
        union = set_a | set_b
        return len(intersection) / len(union)
