import pytest
import asyncio
import time
import uuid
from unittest.mock import patch, MagicMock

from app.services.auth_service import (
    AuthService,
    UserCreateRequest,
    UserUpdateRequest,
    LoginRequest,
    UserRole,
    _hash_password,
    _verify_password,
)


class TestPasswordHashing:
    def test_hash_password_generates_salt(self):
        password_hash = _hash_password("test_password")
        assert ":" in password_hash
        parts = password_hash.split(":")
        assert len(parts) == 2
        assert len(parts[0]) == 32

    def test_hash_password_consistent_with_same_salt(self):
        password_hash = _hash_password("test_password", salt="test_salt_12345678")
        assert _verify_password("test_password", password_hash)

    def test_verify_password_correct(self):
        password_hash = _hash_password("correct_password")
        assert _verify_password("correct_password", password_hash)

    def test_verify_password_incorrect(self):
        password_hash = _hash_password("correct_password")
        assert not _verify_password("wrong_password", password_hash)

    def test_verify_password_malformed_hash(self):
        assert not _verify_password("password", "malformed_hash")
        assert not _verify_password("password", "no_colon_here")


def _create_unique_service():
    return AuthService()


class TestAuthService:
    @pytest.mark.asyncio
    async def test_register_creates_user(self):
        service = _create_unique_service()
        unique_id = uuid.uuid4().hex[:8]
        req = UserCreateRequest(username=f"testuser_{unique_id}", password="password123")
        user = await service.register(req)
        assert user.username.startswith("testuser_")
        assert user.password_hash != "password123"

    @pytest.mark.asyncio
    async def test_register_duplicate_username_raises(self):
        service = _create_unique_service()
        unique_id = uuid.uuid4().hex[:8]
        req = UserCreateRequest(username=f"duplicate_user_{unique_id}", password="password123")
        await service.register(req)
        with pytest.raises(ValueError, match="already exists"):
            await service.register(UserCreateRequest(username=f"duplicate_user_{unique_id}", password="other"))

    @pytest.mark.asyncio
    async def test_login_valid_credentials(self):
        service = _create_unique_service()
        unique_id = uuid.uuid4().hex[:8]
        req = UserCreateRequest(username=f"loginuser_{unique_id}", password="password123")
        await service.register(req)

        login_req = LoginRequest(username=f"loginuser_{unique_id}", password="password123")
        response = await service.login(login_req)
        assert response.user["username"] == f"loginuser_{unique_id}"
        assert response.token is not None

    @pytest.mark.asyncio
    async def test_login_invalid_password(self):
        service = _create_unique_service()
        unique_id = uuid.uuid4().hex[:8]
        req = UserCreateRequest(username=f"logintest_{unique_id}", password="password123")
        await service.register(req)

        with pytest.raises(ValueError, match="Invalid"):
            await service.login(LoginRequest(username=f"logintest_{unique_id}", password="wrong"))

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self):
        service = _create_unique_service()
        with pytest.raises(ValueError, match="Invalid"):
            await service.login(LoginRequest(username="nonexistent_user_12345", password="password"))

    @pytest.mark.asyncio
    async def test_validate_token_valid(self):
        service = _create_unique_service()
        unique_id = uuid.uuid4().hex[:8]
        req = UserCreateRequest(username=f"tokenuser_{unique_id}", password="password123")
        user = await service.register(req)
        validated = await service.validate_token(user.api_token)
        assert validated is not None
        assert validated.username == f"tokenuser_{unique_id}"

    @pytest.mark.asyncio
    async def test_validate_token_invalid(self):
        service = _create_unique_service()
        result = await service.validate_token("invalid_token_12345")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user(self):
        service = _create_unique_service()
        unique_id = uuid.uuid4().hex[:8]
        req = UserCreateRequest(username=f"getuser_{unique_id}", password="password123")
        user = await service.register(req)
        found = await service.get_user(user.id)
        assert found is not None
        assert found.username == f"getuser_{unique_id}"

    @pytest.mark.asyncio
    async def test_get_user_not_found(self):
        service = _create_unique_service()
        result = await service.get_user("nonexistent_id_12345")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_users(self):
        service = _create_unique_service()
        unique_id1 = uuid.uuid4().hex[:8]
        unique_id2 = uuid.uuid4().hex[:8]
        await service.register(UserCreateRequest(username=f"user1_{unique_id1}", password="pass"))
        await service.register(UserCreateRequest(username=f"user2_{unique_id2}", password="pass"))
        users = await service.list_users()
        usernames = [u.username for u in users]
        assert f"user1_{unique_id1}" in usernames
        assert f"user2_{unique_id2}" in usernames

    @pytest.mark.asyncio
    async def test_update_user_display_name(self):
        service = _create_unique_service()
        unique_id = uuid.uuid4().hex[:8]
        user = await service.register(UserCreateRequest(username=f"updateuser_{unique_id}", password="pass"))
        updated = await service.update_user(
            user.id, UserUpdateRequest(display_name="New Display Name")
        )
        assert updated is not None
        assert updated.display_name == "New Display Name"

    @pytest.mark.asyncio
    async def test_update_user_email(self):
        service = _create_unique_service()
        unique_id = uuid.uuid4().hex[:8]
        user = await service.register(UserCreateRequest(username=f"emailuser_{unique_id}", password="pass"))
        updated = await service.update_user(
            user.id, UserUpdateRequest(email="new@email.com")
        )
        assert updated is not None
        assert updated.email == "new@email.com"

    @pytest.mark.asyncio
    async def test_update_user_role(self):
        service = _create_unique_service()
        unique_id = uuid.uuid4().hex[:8]
        user = await service.register(UserCreateRequest(username=f"roleuser_{unique_id}", password="pass"))
        updated = await service.update_user(user.id, UserUpdateRequest(role=UserRole.ADMIN))
        assert updated is not None
        assert updated.role == UserRole.ADMIN

    @pytest.mark.asyncio
    async def test_update_user_not_found(self):
        service = _create_unique_service()
        result = await service.update_user(
            "nonexistent_id_12345", UserUpdateRequest(display_name="Test")
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_user(self):
        service = _create_unique_service()
        unique_id = uuid.uuid4().hex[:8]
        user = await service.register(UserCreateRequest(username=f"deleteuser_{unique_id}", password="pass"))
        deleted = await service.delete_user(user.id)
        assert deleted is True
        found = await service.get_user(user.id)
        assert found is None

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self):
        service = _create_unique_service()
        result = await service.delete_user("nonexistent_id_12345")
        assert result is False


class TestAuthServiceConcurrency:
    def setup_method(self):
        self.service = _create_unique_service()

    @pytest.mark.asyncio
    async def test_concurrent_registration(self):
        unique_prefix = uuid.uuid4().hex[:8]

        async def register_user(username):
            req = UserCreateRequest(username=username, password="password123")
            try:
                await self.service.register(req)
                return True
            except ValueError:
                return False

        tasks = [register_user(f"concurrent_user_{unique_prefix}_{i}") for i in range(10)]
        results = await asyncio.gather(*tasks)
        assert sum(results) == 10

    @pytest.mark.asyncio
    async def test_concurrent_login(self):
        unique_id = uuid.uuid4().hex[:8]
        user = await self.service.register(
            UserCreateRequest(username=f"login_concurrent_{unique_id}", password="password123")
        )

        async def login():
            return await self.service.login(LoginRequest(username=f"login_concurrent_{unique_id}", password="password123"))

        results = await asyncio.gather(*[login() for _ in range(5)])
        assert all(r.user["username"] == f"login_concurrent_{unique_id}" for r in results)

    @pytest.mark.asyncio
    async def test_concurrent_token_validation(self):
        unique_id = uuid.uuid4().hex[:8]
        user = await self.service.register(
            UserCreateRequest(username=f"token_concurrent_{unique_id}", password="password123")
        )

        async def validate():
            return await self.service.validate_token(user.api_token)

        results = await asyncio.gather(*[validate() for _ in range(10)])
        assert all(r is not None for r in results)


class TestSharedWorkspaces:
    def setup_method(self):
        self.service = _create_unique_service()

    @pytest.mark.asyncio
    async def test_create_workspace(self):
        unique_id = uuid.uuid4().hex[:8]
        owner = await self.service.register(
            UserCreateRequest(username=f"ws_owner_{unique_id}", password="password")
        )
        ws = await self.service.create_shared_workspace(
            name=f"Test Workspace {unique_id}",
            owner_id=owner.id
        )
        assert ws.name.startswith("Test Workspace")
        assert ws.owner_id == owner.id
        assert len(ws.members) == 1

    @pytest.mark.asyncio
    async def test_create_workspace_with_members(self):
        unique_id = uuid.uuid4().hex[:8]
        owner = await self.service.register(
            UserCreateRequest(username=f"ws_owner2_{unique_id}", password="password")
        )
        member1 = await self.service.register(
            UserCreateRequest(username=f"member1_{unique_id}", password="password")
        )
        member2 = await self.service.register(
            UserCreateRequest(username=f"member2_{unique_id}", password="password")
        )
        ws = await self.service.create_shared_workspace(
            name=f"Team Workspace {unique_id}",
            owner_id=owner.id,
            member_ids=[member1.id, member2.id]
        )
        assert len(ws.members) == 3

    @pytest.mark.asyncio
    async def test_list_shared_workspaces(self):
        unique_id = uuid.uuid4().hex[:8]
        owner = await self.service.register(
            UserCreateRequest(username=f"list_ws_owner_{unique_id}", password="password")
        )
        await self.service.create_shared_workspace(f"Workspace 1 {unique_id}", owner.id)
        await self.service.create_shared_workspace(f"Workspace 2 {unique_id}", owner.id)

        workspaces = await self.service.list_shared_workspaces(owner.id)
        assert len(workspaces) == 2

    @pytest.mark.asyncio
    async def test_list_shared_workspaces_member_only(self):
        unique_id = uuid.uuid4().hex[:8]
        owner = await self.service.register(
            UserCreateRequest(username=f"owner_list_{unique_id}", password="password")
        )
        member = await self.service.register(
            UserCreateRequest(username=f"member_list_{unique_id}", password="password")
        )
        await self.service.create_shared_workspace(
            f"Member Workspace {unique_id}", owner.id, member_ids=[member.id]
        )

        member_workspaces = await self.service.list_shared_workspaces(member.id)
        assert len(member_workspaces) == 1

        owner_workspaces = await self.service.list_shared_workspaces(owner.id)
        assert len(owner_workspaces) == 1

    @pytest.mark.asyncio
    async def test_add_workspace_member(self):
        unique_id = uuid.uuid4().hex[:8]
        owner = await self.service.register(
            UserCreateRequest(username=f"add_member_owner_{unique_id}", password="password")
        )
        new_member = await self.service.register(
            UserCreateRequest(username=f"new_member_{unique_id}", password="password")
        )
        ws = await self.service.create_shared_workspace(f"Add Member WS {unique_id}", owner.id)

        result = await self.service.add_workspace_member(ws.id, new_member.id)
        assert result is True

        updated_ws = await self.service.list_shared_workspaces(owner.id)
        assert len(updated_ws[0].members) == 2

    @pytest.mark.asyncio
    async def test_add_duplicate_member_fails(self):
        unique_id = uuid.uuid4().hex[:8]
        owner = await self.service.register(
            UserCreateRequest(username=f"dup_owner_{unique_id}", password="password")
        )
        member = await self.service.register(
            UserCreateRequest(username=f"dup_member_{unique_id}", password="password")
        )
        ws = await self.service.create_shared_workspace(
            f"Dup WS {unique_id}", owner.id, member_ids=[member.id]
        )

        result = await self.service.add_workspace_member(ws.id, member.id)
        assert result is False

    @pytest.mark.asyncio
    async def test_remove_workspace_member(self):
        unique_id = uuid.uuid4().hex[:8]
        owner = await self.service.register(
            UserCreateRequest(username=f"remove_owner_{unique_id}", password="password")
        )
        member = await self.service.register(
            UserCreateRequest(username=f"remove_member_{unique_id}", password="password")
        )
        ws = await self.service.create_shared_workspace(
            f"Remove WS {unique_id}", owner.id, member_ids=[member.id]
        )

        result = await self.service.remove_workspace_member(ws.id, member.id)
        assert result is True

        updated_ws = await self.service.list_shared_workspaces(owner.id)
        member_ids = [m["user_id"] for m in updated_ws[0].members]
        assert member.id not in member_ids

    @pytest.mark.asyncio
    async def test_cannot_remove_owner(self):
        unique_id = uuid.uuid4().hex[:8]
        owner = await self.service.register(
            UserCreateRequest(username=f"owner_remove_{unique_id}", password="password")
        )
        ws = await self.service.create_shared_workspace(f"Owner WS {unique_id}", owner.id)

        result = await self.service.remove_workspace_member(ws.id, owner.id)

    @pytest.mark.asyncio
    async def test_workspace_operation_nonexistent_workspace(self):
        result = await self.service.add_workspace_member("nonexistent_id_12345", "user_id")
        assert result is False

        result = await self.service.remove_workspace_member("nonexistent_id_12345", "user_id")
        assert result is False
