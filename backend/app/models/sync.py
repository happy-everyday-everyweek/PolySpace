from typing import Optional

from pydantic import BaseModel


class SyncDeviceModel(BaseModel):
    id: str
    name: str
    is_main_branch: bool = False
    last_sync: Optional[str] = None


class SyncChangeModel(BaseModel):
    id: str
    device_id: str
    change_type: str
    data: dict
    timestamp: str
