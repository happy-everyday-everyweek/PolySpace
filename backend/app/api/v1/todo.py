from typing import Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from ...services.kanban_service import KanbanService
from ...services.todo_service import todo_service

router = APIRouter(tags=["todo"])
kanban_service = KanbanService()


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    priority: str = "none"
    importance: str = "normal"
    urgency: str = "normal"
    due_date: Optional[str] = None
    due_time: Optional[str] = None
    start_date: Optional[str] = None
    start_time: Optional[str] = None
    recurrence: Optional[dict] = None
    list_id: Optional[int] = None
    tags: list[str] = []
    notes: str = ""
    source: str = "manual"
    reminders: list[dict] = []
    subtasks: list[str] = []


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    importance: Optional[str] = None
    urgency: Optional[str] = None
    due_date: Optional[str] = None
    due_time: Optional[str] = None
    start_date: Optional[str] = None
    start_time: Optional[str] = None
    recurrence: Optional[dict] = None
    list_id: Optional[int] = None
    tags: Optional[list[str]] = None
    notes: Optional[str] = None
    sort_order: Optional[int] = None


class SmartCreate(BaseModel):
    text: str
    source: str = "smart"


class SubtaskCreate(BaseModel):
    title: str
    sort_order: int = 0


class SubtaskUpdate(BaseModel):
    title: Optional[str] = None
    completed: Optional[int] = None
    sort_order: Optional[int] = None


class ReminderCreate(BaseModel):
    remind_at: str
    repeat_type: str = "none"
    repeat_interval: int = 1
    repeat_days: str = ""
    repeat_end_date: Optional[str] = None


class TaskListCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None
    color: str = ""
    icon: str = ""
    sort_order: int = 0


class TaskListUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None


class HabitCreate(BaseModel):
    title: str
    description: str = ""
    frequency: str = "daily"
    target_days: str = ""
    color: str = ""
    icon: str = ""
    reminder_time: str = ""
    sort_order: int = 0


class HabitUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    frequency: Optional[str] = None
    target_days: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    reminder_time: Optional[str] = None
    sort_order: Optional[int] = None


class HabitCheckin(BaseModel):
    date: Optional[str] = None
    note: str = ""


class PomodoroStart(BaseModel):
    task_id: Optional[int] = None
    habit_id: Optional[int] = None
    focus_duration: Optional[int] = None
    break_duration: Optional[int] = None
    long_break_duration: Optional[int] = None
    sessions_before_long_break: Optional[int] = None


class PomodoroSettingsUpdate(BaseModel):
    focus_duration: Optional[int] = None
    break_duration: Optional[int] = None
    long_break_duration: Optional[int] = None
    sessions_before_long_break: Optional[int] = None
    auto_start_break: Optional[int] = None
    auto_start_focus: Optional[int] = None


class TodoToKanbanRequest(BaseModel):
    todo_id: int
    board_id: int
    column_id: Optional[int] = None


class KanbanToTodoRequest(BaseModel):
    card_id: int
    board_id: int


class SyncStatusRequest(BaseModel):
    todo_id: int
    new_status: str


# ── Task Lists ────────────────────────────────────────────────

@router.post("/lists")
async def create_list(req: TaskListCreate):
    return await todo_service.create_list(
        name=req.name, parent_id=req.parent_id,
        color=req.color, icon=req.icon, sort_order=req.sort_order,
    )


@router.get("/lists")
async def list_lists(parent_id: Optional[int] = Query(None)):
    return {"lists": await todo_service.list_lists(parent_id=parent_id)}


@router.get("/lists/{list_id}")
async def get_list(list_id: int):
    result = await todo_service.get_list(list_id)
    if not result:
        raise HTTPException(status_code=404, detail="List not found")
    return result


@router.put("/lists/{list_id}")
async def update_list(list_id: int, req: TaskListUpdate):
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = await todo_service.update_list(list_id, **updates)
    if not result:
        raise HTTPException(status_code=404, detail="List not found")
    return result


@router.delete("/lists/{list_id}")
async def delete_list(list_id: int):
    deleted = await todo_service.delete_list(list_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="List not found")
    return {"status": "deleted"}


# ── Tasks ─────────────────────────────────────────────────────

@router.post("/items")
async def create_task(task: TaskCreate):
    return await todo_service.create_task(
        title=task.title, description=task.description,
        priority=task.priority, importance=task.importance,
        urgency=task.urgency, due_date=task.due_date,
        due_time=task.due_time, start_date=task.start_date,
        start_time=task.start_time, recurrence=task.recurrence,
        list_id=task.list_id, tags=task.tags, notes=task.notes,
        source=task.source, reminders=task.reminders,
        subtasks=task.subtasks,
    )


@router.post("/items/smart")
async def create_task_smart(req: SmartCreate):
    return await todo_service.create_task_smart(text=req.text, source=req.source)


@router.post("/items/parse")
async def parse_smart_text(req: SmartCreate):
    return todo_service.parse_smart_text(req.text)


@router.get("/items")
async def list_tasks(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    list_id: Optional[int] = Query(None),
    tag: Optional[str] = Query(None),
    due_before: Optional[str] = Query(None),
    due_after: Optional[str] = Query(None),
    importance: Optional[str] = Query(None),
    urgency: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("DESC"),
    limit: int = Query(200),
    offset: int = Query(0),
):
    tasks = await todo_service.list_tasks(
        status=status, priority=priority, list_id=list_id,
        tag=tag, due_before=due_before, due_after=due_after,
        importance=importance, urgency=urgency,
        sort_by=sort_by, sort_order=sort_order,
        limit=limit, offset=offset,
    )
    return {"tasks": tasks}


@router.get("/items/{task_id}")
async def get_task(task_id: int):
    task = await todo_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/items/{task_id}")
async def update_task(task_id: int, update: TaskUpdate):
    updates = {k: v for k, v in update.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = await todo_service.update_task(task_id, **updates)
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return result


@router.put("/items/{task_id}/complete")
async def complete_task(task_id: int):
    result = await todo_service.complete_task(task_id)
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    if result.get("kanban_card_id"):
        await _sync_todo_complete_to_kanban(result)
    return result


@router.put("/items/{task_id}/reopen")
async def reopen_task(task_id: int):
    result = await todo_service.reopen_task(task_id)
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    if result.get("kanban_card_id"):
        await _sync_todo_reopen_to_kanban(result)
    return result


@router.delete("/items/{task_id}")
async def delete_task(task_id: int):
    deleted = await todo_service.delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "deleted"}


@router.get("/stats")
async def get_task_stats():
    return await todo_service.get_task_stats()


@router.get("/overdue")
async def get_overdue_tasks():
    tasks = await todo_service.get_overdue()
    return {"tasks": tasks}


@router.get("/calendar/{date}")
async def get_tasks_by_date(date: str):
    tasks = await todo_service.get_tasks_by_date(date)
    return {"tasks": tasks}


@router.get("/calendar/{start}/{end}")
async def get_tasks_by_date_range(start: str, end: str):
    tasks = await todo_service.get_tasks_by_date_range(start, end)
    return {"tasks": tasks}


@router.get("/quadrant")
async def get_quadrant_tasks():
    return await todo_service.get_quadrant_tasks()


# ── Subtasks ──────────────────────────────────────────────────

@router.post("/items/{task_id}/subtasks")
async def add_subtask(task_id: int, req: SubtaskCreate):
    task = await todo_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    result = await todo_service.add_subtask(task_id, title=req.title, sort_order=req.sort_order)
    return result


@router.put("/subtasks/{subtask_id}")
async def update_subtask(subtask_id: int, req: SubtaskUpdate):
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = await todo_service.update_subtask(subtask_id, **updates)
    if not result:
        raise HTTPException(status_code=404, detail="Subtask not found")
    return result


@router.delete("/subtasks/{subtask_id}")
async def delete_subtask(subtask_id: int):
    deleted = await todo_service.delete_subtask(subtask_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Subtask not found")
    return {"status": "deleted"}


# ── Reminders ─────────────────────────────────────────────────

@router.post("/items/{task_id}/reminders")
async def add_reminder(task_id: int, req: ReminderCreate):
    task = await todo_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    result = await todo_service.add_reminder(
        task_id=task_id, remind_at=req.remind_at,
        repeat_type=req.repeat_type, repeat_interval=req.repeat_interval,
        repeat_days=req.repeat_days, repeat_end_date=req.repeat_end_date,
    )
    return result


@router.delete("/reminders/{reminder_id}")
async def delete_reminder(reminder_id: int):
    deleted = await todo_service.delete_reminder(reminder_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return {"status": "deleted"}


@router.get("/reminders/pending")
async def get_pending_reminders():
    reminders = await todo_service.get_pending_reminders()
    return {"reminders": reminders}


@router.put("/reminders/{reminder_id}/triggered")
async def mark_reminder_triggered(reminder_id: int):
    ok = await todo_service.mark_reminder_triggered(reminder_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return {"status": "triggered"}


# ── Attachments ───────────────────────────────────────────────

@router.post("/items/{task_id}/attachments")
async def add_attachment(task_id: int, file: UploadFile = File(...)):
    task = await todo_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    import os
    import uuid
    upload_dir = os.path.join("data", "uploads", "tasks", str(task_id))
    os.makedirs(upload_dir, exist_ok=True)
    file_ext = os.path.splitext(file.filename or "file")[1]
    file_name = file.filename or "file"
    stored_name = f"{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(upload_dir, stored_name)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    file_type = file_ext.lstrip(".").lower()
    if file_type in ("jpg", "jpeg", "png", "gif", "webp", "svg", "bmp"):
        file_type = "image"
    elif file_type in ("mp3", "wav", "ogg", "m4a", "flac"):
        file_type = "audio"
    elif file_type in ("pdf",):
        file_type = "pdf"
    elif file_type in ("doc", "docx", "xls", "xlsx", "ppt", "pptx"):
        file_type = "document"
    else:
        file_type = "other"
    result = await todo_service.add_attachment(
        task_id=task_id, file_name=file_name,
        file_path=file_path, file_type=file_type,
        file_size=len(content),
    )
    return result


@router.delete("/attachments/{attachment_id}")
async def delete_attachment(attachment_id: int):
    deleted = await todo_service.delete_attachment(attachment_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Attachment not found")
    return {"status": "deleted"}


# ── Habits ────────────────────────────────────────────────────

@router.post("/habits")
async def create_habit(req: HabitCreate):
    return await todo_service.create_habit(
        title=req.title, description=req.description,
        frequency=req.frequency, target_days=req.target_days,
        color=req.color, icon=req.icon,
        reminder_time=req.reminder_time, sort_order=req.sort_order,
    )


@router.get("/habits")
async def list_habits():
    return {"habits": await todo_service.list_habits()}


@router.get("/habits/{habit_id}")
async def get_habit(habit_id: int):
    habit = await todo_service.get_habit(habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    return habit


@router.put("/habits/{habit_id}")
async def update_habit(habit_id: int, req: HabitUpdate):
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = await todo_service.update_habit(habit_id, **updates)
    if not result:
        raise HTTPException(status_code=404, detail="Habit not found")
    return result


@router.delete("/habits/{habit_id}")
async def delete_habit(habit_id: int):
    deleted = await todo_service.delete_habit(habit_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Habit not found")
    return {"status": "deleted"}


@router.post("/habits/{habit_id}/checkin")
async def checkin_habit(habit_id: int, req: HabitCheckin):
    habit = await todo_service.get_habit(habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    return await todo_service.checkin_habit(habit_id, date=req.date, note=req.note)


@router.delete("/habits/{habit_id}/checkin/{date}")
async def uncheckin_habit(habit_id: int, date: str):
    ok = await todo_service.uncheckin_habit(habit_id, date)
    if not ok:
        raise HTTPException(status_code=404, detail="Checkin not found")
    return {"status": "deleted"}


# ── Pomodoro ──────────────────────────────────────────────────

@router.get("/pomodoro/settings")
async def get_pomodoro_settings():
    return await todo_service.get_pomodoro_settings()


@router.put("/pomodoro/settings")
async def update_pomodoro_settings(req: PomodoroSettingsUpdate):
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    return await todo_service.update_pomodoro_settings(**updates)


@router.post("/pomodoro/start")
async def start_pomodoro(req: PomodoroStart):
    return await todo_service.create_pomodoro_session(
        task_id=req.task_id, habit_id=req.habit_id,
        focus_duration=req.focus_duration, break_duration=req.break_duration,
        long_break_duration=req.long_break_duration,
        sessions_before_long_break=req.sessions_before_long_break,
    )


@router.put("/pomodoro/{session_id}/complete")
async def complete_pomodoro(session_id: int):
    result = await todo_service.complete_pomodoro_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    return result


@router.put("/pomodoro/{session_id}/cancel")
async def cancel_pomodoro(session_id: int):
    result = await todo_service.cancel_pomodoro_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    return result


@router.get("/pomodoro/sessions")
async def list_pomodoro_sessions(task_id: Optional[int] = Query(None), limit: int = Query(50)):
    sessions = await todo_service.list_pomodoro_sessions(task_id=task_id, limit=limit)
    return {"sessions": sessions}


# ── Kanban Bridge ─────────────────────────────────────────────

@router.post("/kanban-bridge/to-kanban")
async def todo_to_kanban(req: TodoToKanbanRequest):
    todo = await todo_service.get_task(req.todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    board = await kanban_service.get_board(req.board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Kanban board not found")

    target_column_id = req.column_id
    if not target_column_id:
        for col in board.get("columns", []):
            if col["name"].lower() in ("to do", "todo", "待办"):
                target_column_id = col["id"]
                break
        if not target_column_id and board.get("columns"):
            target_column_id = board["columns"][0]["id"]
    if not target_column_id:
        raise HTTPException(status_code=400, detail="No suitable column found in board")

    tags_str = ",".join(todo.get("tags", []))
    card_id = await kanban_service.add_card(
        column_id=target_column_id,
        title=todo["title"],
        description=todo.get("description", ""),
        priority=todo.get("priority", "none"),
        tags=tags_str,
        due_date=todo.get("due_date", "") or "",
    )

    await todo_service.update_task(
        req.todo_id,
        kanban_card_id=card_id,
        kanban_board_id=req.board_id,
    )

    if todo["status"] == "completed":
        done_col = None
        for col in board.get("columns", []):
            if col["name"].lower() in ("done", "完成"):
                done_col = col["id"]
                break
        if done_col:
            await kanban_service.move_card(card_id, done_col, 0)

    return {"card_id": card_id, "todo_id": req.todo_id, "board_id": req.board_id, "column_id": target_column_id}


@router.post("/kanban-bridge/to-todo")
async def kanban_to_todo(req: KanbanToTodoRequest):
    board = await kanban_service.get_board(req.board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Kanban board not found")

    card = None
    for col in board.get("columns", []):
        for c in col.get("cards", []):
            if c["id"] == req.card_id:
                card = c
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

    col_name = ""
    for col in board.get("columns", []):
        for c in col.get("cards", []):
            if c["id"] == req.card_id:
                col_name = col["name"]
                break

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


@router.post("/kanban-bridge/sync-status")
async def sync_todo_kanban_status(req: SyncStatusRequest):
    todo = await todo_service.get_task(req.todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    card_id = todo.get("kanban_card_id")
    board_id = todo.get("kanban_board_id")
    if not card_id or not board_id:
        raise HTTPException(status_code=400, detail="Todo is not linked to a kanban card")

    board = await kanban_service.get_board(board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Linked kanban board not found")

    if req.new_status == "completed":
        await todo_service.complete_task(req.todo_id)
        done_col = None
        for col in board.get("columns", []):
            if col["name"].lower() in ("done", "完成"):
                done_col = col["id"]
                break
        if done_col:
            await kanban_service.move_card(card_id, done_col, 0)
    elif req.new_status == "pending":
        await todo_service.reopen_task(req.todo_id)
        todo_col = None
        for col in board.get("columns", []):
            if col["name"].lower() in ("to do", "todo", "待办"):
                todo_col = col["id"]
                break
        if not todo_col and board.get("columns"):
            todo_col = board["columns"][0]["id"]
        if todo_col:
            await kanban_service.move_card(card_id, todo_col, 0)
    else:
        await todo_service.update_task(req.todo_id, status=req.new_status)

    return {"status": "synced", "todo_id": req.todo_id, "new_status": req.new_status}


@router.get("/kanban-bridge/linked/{card_id}")
async def get_linked_todos(card_id: int):
    todos = await todo_service.get_linked_todos(card_id)
    return {"todos": todos}


async def _sync_todo_complete_to_kanban(todo: dict):
    card_id = todo.get("kanban_card_id")
    board_id = todo.get("kanban_board_id")
    if not card_id or not board_id:
        return
    try:
        board = await kanban_service.get_board(board_id)
        if not board:
            return
        done_col = None
        for col in board.get("columns", []):
            if col["name"].lower() in ("done", "完成"):
                done_col = col["id"]
                break
        if done_col:
            await kanban_service.move_card(card_id, done_col, 0)
    except Exception:
        pass


async def _sync_todo_reopen_to_kanban(todo: dict):
    card_id = todo.get("kanban_card_id")
    board_id = todo.get("kanban_board_id")
    if not card_id or not board_id:
        return
    try:
        board = await kanban_service.get_board(board_id)
        if not board:
            return
        todo_col = None
        for col in board.get("columns", []):
            if col["name"].lower() in ("to do", "todo", "待办"):
                todo_col = col["id"]
                break
        if not todo_col and board.get("columns"):
            todo_col = board["columns"][0]["id"]
        if todo_col:
            await kanban_service.move_card(card_id, todo_col, 0)
    except Exception:
        pass
