import json
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class IMChannelType(str, Enum):
    WECHAT = "wechat"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    SLACK = "slack"
    FEISHU = "feishu"
    WECOM = "wecom"
    DINGTALK = "dingtalk"


class IMMessageDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


@dataclass
class IMMessage:
    id: str = ""
    channel: IMChannelType = IMChannelType.WECHAT
    direction: IMMessageDirection = IMMessageDirection.INBOUND
    sender_id: str = ""
    sender_name: str = ""
    chat_id: str = ""
    chat_name: str = ""
    content: str = ""
    content_type: str = "text"
    raw_data: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "channel": self.channel.value,
            "direction": self.direction.value,
            "sender_id": self.sender_id,
            "sender_name": self.sender_name,
            "chat_id": self.chat_id,
            "chat_name": self.chat_name,
            "content": self.content,
            "content_type": self.content_type,
            "created_at": self.created_at,
        }


@dataclass
class IMChannelConfig:
    channel_type: IMChannelType
    enabled: bool = False
    config: dict = field(default_factory=dict)


class IMChannel:
    def __init__(self):
        self._channels: dict[IMChannelType, dict] = {}
        self._configs: dict[IMChannelType, IMChannelConfig] = {}
        self._messages: list[IMMessage] = []
        self._max_messages = 200
        self._daily_count: dict[str, dict[str, int]] = {}
        self._max_daily_per_channel = 20
        self._load_configs()
        for ct in IMChannelType:
            if ct not in self._configs:
                self._configs[ct] = IMChannelConfig(channel_type=ct, enabled=False, config={})

    def _load_configs(self):
        try:
            config_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "im_channels")
            path = os.path.join(config_dir, "configs.json")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data:
                    ct = IMChannelType(item.get("channel_type", "wechat"))
                    self._configs[ct] = IMChannelConfig(
                        channel_type=ct,
                        enabled=item.get("enabled", False),
                        config=item.get("config", {}),
                    )
        except Exception:
            pass

    def _save_configs(self):
        try:
            config_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "im_channels")
            os.makedirs(config_dir, exist_ok=True)
            path = os.path.join(config_dir, "configs.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(
                    [c.__dict__ | {"channel_type": c.channel_type.value, "config": c.config} for c in self._configs.values()],
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception:
            pass

    async def send(self, channel_type: IMChannelType, chat_id: str, content: str, **kwargs) -> Optional[IMMessage]:
        config = self._configs.get(channel_type)
        if not config or not config.enabled:
            logger.warning(f"IM channel {channel_type.value} not enabled")
            return None
        today = time.strftime("%Y-%m-%d")
        if today not in self._daily_count:
            self._daily_count[today] = {}
        self._daily_count[today][channel_type.value] = self._daily_count[today].get(channel_type.value, 0) + 1
        if self._daily_count[today][channel_type.value] > self._max_daily_per_channel:
            logger.warning(f"IM channel {channel_type.value} daily limit reached")
            return None
        msg = IMMessage(
            id=f"im_{int(time.time()*1000)}",
            channel=channel_type,
            direction=IMMessageDirection.OUTBOUND,
            chat_id=chat_id,
            content=content,
            created_at=time.time(),
        )
        self._messages.append(msg)
        if len(self._messages) > self._max_messages:
            self._messages = self._messages[-self._max_messages:]
        logger.info(f"IM sent via {channel_type.value} to {chat_id}: {content[:50]}")
        return msg

    async def receive(self, channel_type: IMChannelType, raw_data: dict) -> IMMessage:
        msg = IMMessage(
            id=f"im_{int(time.time()*1000)}",
            channel=channel_type,
            direction=IMMessageDirection.INBOUND,
            sender_id=raw_data.get("sender_id", ""),
            sender_name=raw_data.get("sender_name", ""),
            chat_id=raw_data.get("chat_id", ""),
            chat_name=raw_data.get("chat_name", ""),
            content=raw_data.get("content", ""),
            raw_data=raw_data,
            created_at=time.time(),
        )
        self._messages.append(msg)
        if len(self._messages) > self._max_messages:
            self._messages = self._messages[-self._max_messages:]
        return msg

    def configure(self, channel_type: IMChannelType, config: dict, enabled: bool = True) -> IMChannelConfig:
        self._configs[channel_type] = IMChannelConfig(channel_type=channel_type, enabled=enabled, config=config)
        self._save_configs()
        return self._configs[channel_type]

    def get_config(self, channel_type: IMChannelType) -> IMChannelConfig:
        return self._configs.get(channel_type, IMChannelConfig(channel_type=channel_type))

    def list_channels(self) -> list[dict]:
        result = []
        for ct in IMChannelType:
            config = self._configs.get(ct, IMChannelConfig(channel_type=ct))
            result.append({
                "channel_type": ct.value,
                "enabled": config.enabled,
                "connected": config.enabled,
                "daily_count": self._daily_count.get(time.strftime("%Y-%m-%d"), {}).get(ct.value, 0),
            })
        return result

    def get_messages(self, channel_type: Optional[IMChannelType] = None, limit: int = 50) -> list[dict]:
        msgs = self._messages
        if channel_type:
            msgs = [m for m in msgs if m.channel == channel_type]
        msgs = sorted(msgs, key=lambda m: m.created_at, reverse=True)
        return [m.to_dict() for m in msgs[:limit]]

    def get_daily_count(self, channel_type: Optional[IMChannelType] = None) -> dict:
        today = time.strftime("%Y-%m-%d")
        counts = self._daily_count.get(today, {})
        if channel_type:
            return {channel_type.value: counts.get(channel_type.value, 0)}
        return counts


_channel: Optional["IMChannel"] = None


def get_im_channel() -> IMChannel:
    global _channel
    if _channel is None:
        _channel = IMChannel()
    return _channel
