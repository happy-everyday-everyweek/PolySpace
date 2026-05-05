from __future__ import annotations

import hashlib
import json
import os
import secrets
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class UserStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"


class User(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    username: str
    email: Optional[str] = None
    display_name: str = ""
    avatar: Optional[str] = None
    role: UserRole = UserRole.MEMBER
    status: UserStatus = UserStatus.ACTIVE
    password_hash: str = ""
    api_token: str = Field(default_factory=lambda: secrets.token_hex(32))
    last_login_at: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class UserCreateRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    role: UserRole = UserRole.MEMBER


class UserUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None
    role: Optional[UserRole] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    user: dict
    token: str
    expires_at: str


class SharedWorkspace(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str
    owner_id: str
    members: list[dict] = Field(default_factory=list)
    permissions: dict[str, list[str]] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "users")
_WORKSPACE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "shared_workspaces")


def _hash_password(password: str, salt: str = "") -> str:
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    return f"{salt}:{hashed.hex()}"


def _verify_password(password: str, password_hash: str) -> bool:
    try:
        salt, _ = password_hash.split(":", 1)
        return _hash_password(password, salt) == password_hash
    except Exception:
        return False


class AuthService:
    def __init__(self):
        self._users: dict[str, User] = {}
        self._tokens: dict[str, str] = {}
        self._shared_workspaces: dict[str, SharedWorkspace] = {}
        self._load_all()

    def _load_all(self):
        try:
            if os.path.exists(_DATA_DIR):
                for fname in os.listdir(_DATA_DIR):
                    if fname.endswith(".json"):
                        with open(os.path.join(_DATA_DIR, fname), "r", encoding="utf-8") as f:
                            data = json.load(f)
                            user = User(**data)
                            self._users[user.id] = user
                            self._tokens[user.api_token] = user.id
        except Exception:
            pass
        try:
            if os.path.exists(_WORKSPACE_DIR):
                for fname in os.listdir(_WORKSPACE_DIR):
                    if fname.endswith(".json"):
                        with open(os.path.join(_WORKSPACE_DIR, fname), "r", encoding="utf-8") as f:
                            data = json.load(f)
                            ws = SharedWorkspace(**data)
                            self._shared_workspaces[ws.id] = ws
        except Exception:
            pass

    def _save_user(self, user: User):
        os.makedirs(_DATA_DIR, exist_ok=True)
        path = os.path.join(_DATA_DIR, f"{user.id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(user.model_dump(), f, ensure_ascii=False, indent=2)

    def _save_workspace(self, ws: SharedWorkspace):
        os.makedirs(_WORKSPACE_DIR, exist_ok=True)
        path = os.path.join(_WORKSPACE_DIR, f"{ws.id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(ws.model_dump(), f, ensure_ascii=False, indent=2)

    async def register(self, req: UserCreateRequest) -> User:
        for user in self._users.values():
            if user.username == req.username:
                raise ValueError("Username already exists")
        password_hash = _hash_password(req.password)
        user = User(
            username=req.username,
            email=req.email,
            display_name=req.display_name or req.username,
            role=req.role,
            password_hash=password_hash,
        )
        self._users[user.id] = user
        self._tokens[user.api_token] = user.id
        self._save_user(user)
        return user

    async def login(self, req: LoginRequest) -> LoginResponse:
        user = None
        for u in self._users.values():
            if u.username == req.username:
                user = u
                break
        if not user or not _verify_password(req.password, user.password_hash):
            raise ValueError("Invalid username or password")
        if user.status == UserStatus.DISABLED:
            raise ValueError("Account is disabled")
        user.last_login_at = datetime.now().isoformat()
        self._save_user(user)
        from datetime import timedelta
        expires = (datetime.now() + timedelta(days=7)).isoformat()
        return LoginResponse(
            user={"id": user.id, "username": user.username, "display_name": user.display_name, "role": user.role.value, "avatar": user.avatar},
            token=user.api_token,
            expires_at=expires,
        )

    async def validate_token(self, token: str) -> Optional[User]:
        user_id = self._tokens.get(token)
        if user_id:
            return self._users.get(user_id)
        return None

    async def get_user(self, user_id: str) -> Optional[User]:
        return self._users.get(user_id)

    async def list_users(self) -> list[User]:
        return list(self._users.values())

    async def update_user(self, user_id: str, req: UserUpdateRequest) -> Optional[User]:
        user = self._users.get(user_id)
        if not user:
            return None
        if req.display_name is not None:
            user.display_name = req.display_name
        if req.email is not None:
            user.email = req.email
        if req.avatar is not None:
            user.avatar = req.avatar
        if req.role is not None:
            user.role = req.role
        self._save_user(user)
        return user

    async def delete_user(self, user_id: str) -> bool:
        if user_id in self._users:
            user = self._users[user_id]
            if user.api_token in self._tokens:
                del self._tokens[user.api_token]
            del self._users[user_id]
            path = os.path.join(_DATA_DIR, f"{user_id}.json")
            if os.path.exists(path):
                os.remove(path)
            return True
        return False

    async def create_shared_workspace(self, name: str, owner_id: str, member_ids: list[str] | None = None) -> SharedWorkspace:
        members = [{"user_id": owner_id, "role": "owner"}]
        if member_ids:
            for mid in member_ids:
                if mid != owner_id:
                    members.append({"user_id": mid, "role": "member"})
        ws = SharedWorkspace(name=name, owner_id=owner_id, members=members)
        self._shared_workspaces[ws.id] = ws
        self._save_workspace(ws)
        return ws

    async def list_shared_workspaces(self, user_id: str) -> list[SharedWorkspace]:
        results = []
        for ws in self._shared_workspaces.values():
            for member in ws.members:
                if member.get("user_id") == user_id:
                    results.append(ws)
                    break
        return results

    async def add_workspace_member(self, workspace_id: str, user_id: str, role: str = "member") -> bool:
        ws = self._shared_workspaces.get(workspace_id)
        if not ws:
            return False
        for member in ws.members:
            if member.get("user_id") == user_id:
                return False
        ws.members.append({"user_id": user_id, "role": role})
        self._save_workspace(ws)
        return True

    async def remove_workspace_member(self, workspace_id: str, user_id: str) -> bool:
        ws = self._shared_workspaces.get(workspace_id)
        if not ws:
            return False
        ws.members = [m for m in ws.members if m.get("user_id") != user_id or m.get("role") == "owner"]
        self._save_workspace(ws)
        return True


auth_service = AuthService()
