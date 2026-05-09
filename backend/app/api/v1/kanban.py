from typing import Optional

from app.api.v1.auth import get_current_user
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from ...services.kanban_service import KanbanService
from ...services.todo_service import todo_service

router = APIRouter(tags=["kanban"])
kanban_service = KanbanService()


class BoardCreate(BaseModel):
    name: str
    description: str = ""


class BoardUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ColumnCreate(BaseModel):
    board_id: int
    name: str
    color: str = "#7c6ff7"
    wip_limit: int = 0


class ColumnUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    position: Optional[int] = None
    wip_limit: Optional[int] = None


class ColumnReorder(BaseModel):
    column_ids: list[int]


class CardCreate(BaseModel):
    column_id: int
    title: str
    description: str = ""
    assignee: str = ""
    priority: str = "medium"
    tags: str = ""
    due_date: str = ""


class CardMove(BaseModel):
    target_column_id: int
    target_position: int = 0


class CardUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assignee: Optional[str] = None
    priority: Optional[str] = None
    tags: Optional[str] = None
    due_date: Optional[str] = None


@router.post("/boards")
async def create_board(board: BoardCreate, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    board_id = await kanban_service.create_board(board.name, board.description)
    return {"id": board_id}


@router.get("/boards")
async def list_boards(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    boards = await kanban_service.list_boards()
    return {"boards": boards}


@router.get("/boards/{board_id}")
async def get_board(board_id: int, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    board = await kanban_service.get_board(board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    return board


@router.put("/boards/{board_id}")
async def update_board(board_id: int, update: BoardUpdate, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    updates = {k: v for k, v in update.model_dump().items() if v is not None}
    await kanban_service.update_board(board_id, **updates)
    return {"status": "updated"}


@router.delete("/boards/{board_id}")
async def delete_board(board_id: int, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    await kanban_service.delete_board(board_id)
    return {"status": "deleted"}


@router.get("/boards/{board_id}/stats")
async def get_board_stats(board_id: int, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    stats = await kanban_service.get_board_stats(board_id)
    return stats


@router.get("/boards/{board_id}/search")
async def search_cards(board_id: int, q: str = Query(..., min_length=1)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    results = await kanban_service.search_cards(board_id, q)
    return {"results": results}


@router.get("/boards/{board_id}/archived")
async def get_archived_cards(board_id: int, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    cards = await kanban_service.get_archived_cards(board_id)
    return {"cards": cards}


@router.post("/columns")
async def add_column(column: ColumnCreate, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    column_id = await kanban_service.add_column(
        column.board_id, column.name, column.color, column.wip_limit
    )
    return {"id": column_id}


@router.put("/columns/{column_id}")
async def update_column(column_id: int, update: ColumnUpdate, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    updates = {k: v for k, v in update.model_dump().items() if v is not None}
    await kanban_service.update_column(column_id, **updates)
    return {"status": "updated"}


@router.delete("/columns/{column_id}")
async def delete_column(column_id: int, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    await kanban_service.delete_column(column_id)
    return {"status": "deleted"}


@router.put("/boards/{board_id}/columns/reorder")
async def reorder_columns(board_id: int, reorder: ColumnReorder, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    await kanban_service.reorder_columns(board_id, reorder.column_ids)
    return {"status": "reordered"}


@router.post("/cards")
async def add_card(card: CardCreate, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    card_id = await kanban_service.add_card(
        column_id=card.column_id,
        title=card.title,
        description=card.description,
        assignee=card.assignee,
        priority=card.priority,
        tags=card.tags,
        due_date=card.due_date,
    )
    return {"id": card_id}


@router.put("/cards/{card_id}/move")
async def move_card(card_id: int, move: CardMove, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    await kanban_service.move_card(card_id, move.target_column_id, move.target_position)
    await _sync_kanban_move_to_todo(card_id, move.target_column_id)
    return {"status": "moved"}


@router.put("/cards/{card_id}")
async def update_card(card_id: int, update: CardUpdate, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    updates = {k: v for k, v in update.model_dump().items() if v is not None}
    await kanban_service.update_card(card_id, **updates)
    return {"status": "updated"}


@router.delete("/cards/{card_id}")
async def delete_card(card_id: int, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    await kanban_service.delete_card(card_id)
    return {"status": "deleted"}


@router.put("/cards/{card_id}/archive")
async def archive_card(card_id: int, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    await kanban_service.archive_card(card_id)
    return {"status": "archived"}


@router.put("/cards/{card_id}/unarchive")
async def unarchive_card(card_id: int, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    await kanban_service.unarchive_card(card_id)
    return {"status": "unarchived"}


class CardToTodoRequest(BaseModel):
    card_id: int
    board_id: int


@router.post("/todo-bridge/to-todo")
async def card_to_todo(req: CardToTodoRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    board = await kanban_service.get_board(req.board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Kanban board not found")

    card = None
    col_name = ""
    for col in board.get("columns", []):
        for c in col.get("cards", []):
            if c["id"] == req.card_id:
                card = c
                col_name = col["name"]
                break
        if card:
            break

    if not card:
        archived = await kanban_service.get_archived_cards(req.board_id)
        for c in archived:
            if c["id"] == req.card_id:
                card = c
                break

    if not card:
        raise HTTPException(status_code=404, detail="Kanban card not found")

    is_done = col_name.lower() in ("done", "完成")
    status = "completed" if is_done else "pending"
    tags_list = [t.strip() for t in card.get("tags", "").split(",") if t.strip()] if card.get("tags") else []

    todo = await todo_service.create_task(
        title=card["title"],
        description=card.get("description", ""),
        priority=card.get("priority", "none"),
        due_date=card.get("due_date") or None,
        tags=tags_list,
        kanban_card_id=req.card_id,
        kanban_board_id=req.board_id,
    )

    if status == "completed":
        await todo_service.complete_task(todo["id"])

    return {"todo_id": todo["id"], "card_id": req.card_id, "status": status}


@router.get("/todo-bridge/linked/{card_id}")
async def get_card_linked_todos(card_id: int, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    todos = await todo_service.get_linked_todos(card_id)
    return {"todos": todos}


async def _sync_kanban_move_to_todo(card_id: int, target_column_id: int):
    linked_todos = await todo_service.get_linked_todos(card_id)
    if not linked_todos:
        return

    board = None
    for t in linked_todos:
        bid = t.get("kanban_board_id")
        if bid:
            board = await kanban_service.get_board(bid)
            break
    if not board:
        return

    target_col_name = ""
    for col in board.get("columns", []):
        if col["id"] == target_column_id:
            target_col_name = col["name"].lower()
            break

    is_done = target_col_name in ("done", "完成")
    for t in linked_todos:
        if t["status"] == "completed" and not is_done:
            await todo_service.reopen_task(t["id"])
        elif t["status"] != "completed" and is_done:
            await todo_service.complete_task(t["id"])
