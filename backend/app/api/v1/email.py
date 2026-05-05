from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...services.email.models import SendMessageInput
from ...services.email.service import get_email_service
from ...services.email.templates import get_template_manager

router = APIRouter(tags=["email"])


class AccountCreate(BaseModel):
    name: str
    email_address: str
    imap_host: str
    smtp_host: str
    username: str
    password: str
    imap_port: int = 993
    smtp_port: int = 587
    use_ssl: bool = True
    provider: str = "imap_smtp"


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    imap_host: Optional[str] = None
    imap_port: Optional[int] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    use_ssl: Optional[bool] = None
    handle_aliases: Optional[str] = None


class EmailSend(BaseModel):
    account_id: int
    to: str | list[str]
    subject: str
    body: str = ""
    html: str = ""
    cc: str | list[str] | None = None
    bcc: str | list[str] | None = None
    in_reply_to: str = ""
    thread_id: str = ""


class DraftCreate(BaseModel):
    account_id: int
    subject: str
    to: str
    body: str = ""
    cc: str = ""
    bcc: str = ""
    body_html: str = ""
    thread_id: str = ""
    in_reply_to: str = ""


class DraftUpdate(BaseModel):
    subject: Optional[str] = None
    to: Optional[str] = None
    cc: Optional[str] = None
    bcc: Optional[str] = None
    body: Optional[str] = None
    body_html: Optional[str] = None
    thread_id: Optional[str] = None
    in_reply_to: Optional[str] = None


class ReadRequest(BaseModel):
    is_read: bool = True


class StarRequest(BaseModel):
    is_starred: bool = True


class BatchReadRequest(BaseModel):
    email_ids: list[int]
    is_read: bool = True


class BatchDeleteRequest(BaseModel):
    email_ids: list[int]


class MoveEmailRequest(BaseModel):
    folder: str


class TemplateCreate(BaseModel):
    name: str
    subject: str
    body_text: str
    body_html: str = ""


class TemplateRenderRequest(BaseModel):
    name: str
    context: dict[str, str]


@router.post("/accounts")
async def create_account(account: AccountCreate):
    svc = get_email_service()
    account_id = await svc.add_account(
        name=account.name,
        email_address=account.email_address,
        imap_host=account.imap_host,
        smtp_host=account.smtp_host,
        username=account.username,
        password=account.password,
        imap_port=account.imap_port,
        smtp_port=account.smtp_port,
        use_ssl=account.use_ssl,
        provider=account.provider,
    )
    return {"id": account_id}


@router.get("/accounts")
async def list_accounts():
    svc = get_email_service()
    accounts = await svc.list_accounts()
    return {"accounts": accounts}


@router.get("/accounts/{account_id}")
async def get_account(account_id: int):
    svc = get_email_service()
    account = await svc.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"account": account}


@router.patch("/accounts/{account_id}")
async def update_account(account_id: int, update: AccountUpdate):
    svc = get_email_service()
    updates = {k: v for k, v in update.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    success = await svc.update_account(account_id, **updates)
    if not success:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"status": "updated"}


@router.delete("/accounts/{account_id}")
async def delete_account(account_id: int):
    svc = get_email_service()
    await svc.delete_account(account_id)
    return {"status": "deleted"}


@router.get("/accounts/{account_id}/emails")
async def get_emails(account_id: int, folder: str = "INBOX",
                     limit: int = 50, offset: int = 0, search: str = ""):
    svc = get_email_service()
    emails = await svc.fetch_emails(account_id, folder, limit, offset, search)
    return {"emails": emails}


@router.get("/accounts/{account_id}/stats")
async def get_email_stats(account_id: int):
    svc = get_email_service()
    stats = await svc.get_email_stats(account_id)
    return stats


@router.post("/accounts/{account_id}/sync")
async def sync_emails(account_id: int, folder: str = "INBOX", limit: int = 50):
    svc = get_email_service()
    synced = await svc.sync_emails(account_id, folder, limit)
    return {"synced": synced}


@router.get("/accounts/{account_id}/folders")
async def list_folders(account_id: int):
    svc = get_email_service()
    folders = await svc.list_folders(account_id)
    return {"folders": folders}


@router.get("/emails/{email_id}")
async def get_email(email_id: int):
    svc = get_email_service()
    email = await svc.get_email(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return {"email": email}


@router.get("/threads/{thread_id}")
async def get_thread(thread_id: str):
    svc = get_email_service()
    emails = await svc.get_thread_emails(thread_id)
    return {"emails": emails}


@router.post("/send")
async def send_email(email: EmailSend):
    svc = get_email_service()
    send_input = SendMessageInput(
        to=email.to,
        subject=email.subject,
        body=email.body,
        html=email.html,
        cc=email.cc,
        bcc=email.bcc,
        in_reply_to=email.in_reply_to,
        thread_id=email.thread_id,
    )
    success = await svc.send_email(email.account_id, send_input)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send email")
    return {"status": "sent"}


@router.post("/drafts")
async def save_draft(draft: DraftCreate):
    svc = get_email_service()
    draft_id = await svc.save_draft(
        account_id=draft.account_id,
        subject=draft.subject,
        to=draft.to,
        body=draft.body,
        cc=draft.cc,
        bcc=draft.bcc,
        body_html=draft.body_html,
        thread_id=draft.thread_id,
        in_reply_to=draft.in_reply_to,
    )
    return {"id": draft_id}


@router.get("/drafts/{account_id}")
async def list_drafts(account_id: int):
    svc = get_email_service()
    drafts = await svc.list_drafts(account_id)
    return {"drafts": drafts}


@router.patch("/drafts/{draft_id}")
async def update_draft(draft_id: int, update: DraftUpdate):
    svc = get_email_service()
    updates = {}
    if update.subject is not None:
        updates["subject"] = update.subject
    if update.to is not None:
        updates["to_addresses"] = update.to
    if update.cc is not None:
        updates["cc"] = update.cc
    if update.bcc is not None:
        updates["bcc"] = update.bcc
    if update.body is not None:
        updates["body_text"] = update.body
    if update.body_html is not None:
        updates["body_html"] = update.body_html
    if update.thread_id is not None:
        updates["thread_id"] = update.thread_id
    if update.in_reply_to is not None:
        updates["in_reply_to"] = update.in_reply_to
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    success = await svc.update_draft(draft_id, **updates)
    if not success:
        raise HTTPException(status_code=404, detail="Draft not found")
    return {"status": "updated"}


@router.delete("/drafts/{draft_id}")
async def delete_draft(draft_id: int):
    svc = get_email_service()
    await svc.delete_draft(draft_id)
    return {"status": "deleted"}


@router.put("/emails/{email_id}/read")
async def mark_read(email_id: int, req: ReadRequest):
    svc = get_email_service()
    await svc.mark_read(email_id, req.is_read)
    return {"status": "updated"}


@router.put("/emails/{email_id}/star")
async def mark_starred(email_id: int, req: StarRequest):
    svc = get_email_service()
    await svc.mark_starred(email_id, req.is_starred)
    return {"status": "updated"}


@router.delete("/emails/{email_id}")
async def delete_email(email_id: int):
    svc = get_email_service()
    await svc.delete_email(email_id)
    return {"status": "deleted"}


@router.put("/emails/{email_id}/move")
async def move_email(email_id: int, req: MoveEmailRequest):
    svc = get_email_service()
    await svc.move_email(email_id, req.folder)
    return {"status": "moved"}


@router.put("/emails/batch/read")
async def batch_mark_read(req: BatchReadRequest):
    svc = get_email_service()
    await svc.batch_mark_read(req.email_ids, req.is_read)
    return {"status": "updated"}


@router.delete("/emails/batch")
async def batch_delete(req: BatchDeleteRequest):
    svc = get_email_service()
    await svc.batch_delete(req.email_ids)
    return {"status": "deleted"}


@router.get("/templates")
async def list_templates():
    mgr = get_template_manager()
    templates = mgr.list_templates()
    return {"templates": templates}


@router.post("/templates")
async def create_template(template: TemplateCreate):
    from ...services.email.templates import EmailTemplate
    mgr = get_template_manager()
    t = EmailTemplate(
        name=template.name,
        subject=template.subject,
        body_text=template.body_text,
        body_html=template.body_html,
    )
    success = mgr.save_template(t)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save template")
    return {"status": "created"}


@router.delete("/templates/{name}")
async def delete_template(name: str):
    mgr = get_template_manager()
    success = mgr.delete_template(name)
    if not success:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"status": "deleted"}


@router.post("/templates/render")
async def render_template(req: TemplateRenderRequest):
    mgr = get_template_manager()
    result = mgr.render_template(req.name, req.context)
    if not result:
        raise HTTPException(status_code=404, detail="Template not found")
    subject, body_text, body_html = result
    return {"subject": subject, "body_text": body_text, "body_html": body_html}
