
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from app.services.auth_service import (
    LoginRequest,
    UserCreateRequest,
    UserRole,
    UserUpdateRequest,
    auth_service,
)

router = APIRouter()


async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        return None
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    user = await auth_service.validate_token(token)
    return user


@router.post("/register")
async def register(req: UserCreateRequest):
    try:
        user = await auth_service.register(req)
        return {"id": user.id, "username": user.username, "display_name": user.display_name, "role": user.role.value}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(req: LoginRequest):
    try:
        result = await auth_service.login(req)
        return result.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me")
async def get_me(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"id": user.id, "username": user.username, "display_name": user.display_name, "role": user.role.value, "email": user.email, "avatar": user.avatar}


@router.get("/users")
async def list_users(user=Depends(get_current_user)):
    if not user or user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    users = await auth_service.list_users()
    return {"users": [{"id": u.id, "username": u.username, "display_name": u.display_name, "role": u.role.value, "status": u.status.value} for u in users]}


@router.patch("/users/{user_id}")
async def update_user(user_id: str, req: UserUpdateRequest, current_user=Depends(get_current_user)):
    if not current_user or (current_user.role != UserRole.ADMIN and current_user.id != user_id):
        raise HTTPException(status_code=403, detail="Access denied")
    user = await auth_service.update_user(user_id, req)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "username": user.username, "display_name": user.display_name}


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user=Depends(get_current_user)):
    if not current_user or current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    deleted = await auth_service.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "deleted"}


class CreateWorkspaceRequest(BaseModel):
    name: str
    member_ids: list[str] | None = None


@router.post("/workspaces/shared")
async def create_shared_workspace(req: CreateWorkspaceRequest, current_user=Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    ws = await auth_service.create_shared_workspace(req.name, current_user.id, req.member_ids)
    return ws.model_dump()


@router.get("/workspaces/shared")
async def list_shared_workspaces(current_user=Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    workspaces = await auth_service.list_shared_workspaces(current_user.id)
    return {"workspaces": [ws.model_dump() for ws in workspaces]}


class AddMemberRequest(BaseModel):
    user_id: str
    role: str = "member"


@router.post("/workspaces/shared/{workspace_id}/members")
async def add_workspace_member(workspace_id: str, req: AddMemberRequest, current_user=Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    added = await auth_service.add_workspace_member(workspace_id, req.user_id, req.role)
    if not added:
        raise HTTPException(status_code=400, detail="Failed to add member")
    return {"status": "added"}


@router.delete("/workspaces/shared/{workspace_id}/members/{user_id}")
async def remove_workspace_member(workspace_id: str, user_id: str, current_user=Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    removed = await auth_service.remove_workspace_member(workspace_id, user_id)
    if not removed:
        raise HTTPException(status_code=400, detail="Failed to remove member")
    return {"status": "removed"}
