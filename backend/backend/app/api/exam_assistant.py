from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.exam_assistant import ExamAssistantChatRequest, ExamAssistantExportRequest, ExamAssistantSessionCreate
from app.services.exam_assistant import add_document, chat, remove_document, store
from app.services.exam_documents import build_exam_docx, build_exam_pdf, validate_and_extract, MAX_UPLOAD_BYTES


router = APIRouter(prefix="/admin/exam-assistant", tags=["Admin Exam Assistant"])


def _admin(user: User):
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")


@router.post("/sessions")
def create_session(payload: ExamAssistantSessionCreate, current_user: User = Depends(get_current_user)):
    _admin(current_user)
    return {"success": True, **store.create(current_user.user_id, payload.session_id)}


@router.get("/sessions/{session_id}")
def get_session(session_id: str, current_user: User = Depends(get_current_user)):
    _admin(current_user)
    try:
        value = store.get(session_id, current_user.user_id)
    except KeyError as error:
        raise HTTPException(404, str(error)) from error
    return {"success": True, **store._public(value), "date_sheet": value["date_sheet"],
            "seating_plan": value["seating_plan"], "scope": value["scope"], "warnings": value["warnings"]}


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str, current_user: User = Depends(get_current_user)):
    _admin(current_user)
    if not store.delete(session_id, current_user.user_id):
        raise HTTPException(404, "Exam assistant session was not found or has expired")
    return {"success": True, "message": "Temporary chat, vectors, and uploaded context were removed"}


@router.post("/chat")
def assistant_chat(payload: ExamAssistantChatRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _admin(current_user)
    try:
        session = store.get(payload.session_id, current_user.user_id)
        return chat(db, session, payload.message)
    except KeyError as error:
        raise HTTPException(404, str(error)) from error
    except ValueError as error:
        raise HTTPException(422, str(error)) from error


@router.post("/documents")
async def upload_document(
    session_id: str = Form(...),
    document: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    _admin(current_user)
    try:
        session = store.get(session_id, current_user.user_id)
    except KeyError as error:
        raise HTTPException(404, str(error)) from error
    filename = (document.filename or "").replace("\\", "/").split("/")[-1].strip()
    content = await document.read(MAX_UPLOAD_BYTES + 1)
    try:
        text, metadata = await run_in_threadpool(validate_and_extract, filename, content)
        indexed = await run_in_threadpool(add_document, session, filename, text, metadata)
    except OverflowError as error:
        raise HTTPException(413, str(error)) from error
    except FileExistsError as error:
        raise HTTPException(409, str(error)) from error
    except Exception as error:
        raise HTTPException(422, f"Could not process {filename or 'the uploaded file'}: {error}") from error
    return {"success": True, "document": indexed, "rag": {"temporary": True, "embedding_provider": session["knowledge"].get("provider"), "retrievable_chunks": indexed["chunks"]}}


@router.delete("/sessions/{session_id}/documents/{document_id}")
def delete_document(session_id: str, document_id: str, current_user: User = Depends(get_current_user)):
    _admin(current_user)
    try:
        session = store.get(session_id, current_user.user_id)
    except KeyError as error:
        raise HTTPException(404, str(error)) from error
    if not remove_document(session, document_id):
        raise HTTPException(404, "Temporary document was not found")
    return {"success": True, "message": "Temporary document vectors were removed"}


@router.post("/export")
def export_proposal(payload: ExamAssistantExportRequest, current_user: User = Depends(get_current_user)):
    _admin(current_user)
    try:
        session = store.get(payload.session_id, current_user.user_id)
    except KeyError as error:
        raise HTTPException(404, str(error)) from error
    rows = session[payload.document_type]
    if not rows:
        raise HTTPException(422, f"No current {payload.document_type.replace('_', ' ')} proposal is available")
    title = "Exam Date Sheet" if payload.document_type == "date_sheet" else "Exam Seating Plan"
    if payload.format == "pdf":
        output = build_exam_pdf(title, rows, session["scope"])
        media_type, extension = "application/pdf", "pdf"
    else:
        output = build_exam_docx(title, rows, session["scope"])
        media_type, extension = "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "docx"
    filename = f"{payload.document_type.replace('_', '-')}.{extension}"
    return StreamingResponse(output, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="{filename}"'})
