import base64
import email
import email.policy
import os
import uuid
from typing import List, Union
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.exceptions import NotFoundError, ValidationError, ForbiddenError
from app.db.session import get_db
from app.models.attachment import ProjectAttachment
from app.models.identity import User
from app.models.project import ProjectMember
from app.schemas.attachment import AttachmentResponse
from app.security.authentication import get_current_user
from app.security.authorization import require_project_member
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/projects/{projectId}/attachments", tags=["Project Attachments"])

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

def _get_upload_dir(project_id: int) -> str:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads", str(project_id)))
    os.makedirs(base_dir, exist_ok=True)
    return base_dir

@router.post(
    "",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload PDF Attachment",
    description="Securely uploads and validates a PDF attachment with magic-byte verification and project-level authorization."
)
async def upload_attachment(
    projectId: Union[int, str],
    request: Request,
    membership: ProjectMember = Depends(require_project_member),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pid = membership.project_id
    raw_content_type = request.headers.get("content-type", "")
    
    filename = None
    file_bytes = None
    category = "ADVISORY_REFERENCE"

    if "multipart/form-data" in raw_content_type.lower():
        body = await request.body()
        msg_data = f"Content-Type: {raw_content_type}\r\n\r\n".encode("utf-8") + body
        msg = email.message_from_bytes(msg_data, policy=email.policy.default)
        
        for part in msg.iter_parts():
            part_name = part.get_param("name", header="content-disposition")
            part_filename = part.get_filename()
            
            if part_name == "category":
                payload = part.get_payload(decode=True)
                if payload:
                    category = payload.decode("utf-8", errors="ignore").strip()
            elif part_filename or part_name == "file":
                filename = part_filename or "document.pdf"
                file_bytes = part.get_payload(decode=True)
    elif "application/json" in raw_content_type.lower():
        body_json = await request.json()
        filename = body_json.get("filename", "document.pdf")
        category = body_json.get("category", "ADVISORY_REFERENCE")
        b64_content = body_json.get("content_base64", "")
        try:
            file_bytes = base64.b64decode(b64_content)
        except Exception:
            raise ValidationError("Invalid base64 payload")
    else:
        raise ValidationError(f"Unsupported content type: {raw_content_type}. Expected multipart/form-data or application/json")

    if not filename:
        filename = "document.pdf"

    if not filename.lower().endswith(".pdf"):
        raise ValidationError("Only PDF files are supported. File extension must be .pdf")

    if not file_bytes or len(file_bytes) == 0:
        raise ValidationError("Uploaded file is empty")

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise ValidationError(f"File size exceeds maximum allowable limit of 10MB (got {len(file_bytes)} bytes)")

    # Validate PDF magic bytes: %PDF-
    if not file_bytes.startswith(b"%PDF-"):
        raise ValidationError("Invalid PDF format. File magic bytes do not match standard PDF header (%PDF-)")

    # Safe stored filename
    stored_name = f"{uuid.uuid4().hex}.pdf"
    upload_dir = _get_upload_dir(pid)
    storage_path = os.path.join(upload_dir, stored_name)

    with open(storage_path, "wb") as f:
        f.write(file_bytes)

    clean_filename = os.path.basename(filename)
    attachment = ProjectAttachment(
        project_id=pid,
        uploaded_by=current_user.user_id,
        original_filename=clean_filename,
        stored_filename=stored_name,
        file_size=len(file_bytes),
        content_type="application/pdf",
        category=category[:50],
        storage_path=storage_path
    )
    db.add(attachment)
    db.flush()

    log_audit_event(
        db=db,
        project_id=pid,
        actor_user_id=current_user.user_id,
        event_type="ATTACHMENT_UPLOADED",
        entity_type="ATTACHMENT",
        entity_id=attachment.attachment_id,
        event_description=f"PDF document '{clean_filename}' uploaded to Project {pid} by {current_user.full_name}",
        new_values={
            "filename": clean_filename,
            "file_size": len(file_bytes),
            "category": category,
            "attachment_id": attachment.attachment_id
        }
    )
    db.commit()
    db.refresh(attachment)

    return AttachmentResponse(
        attachment_id=attachment.attachment_id,
        project_id=attachment.project_id,
        uploaded_by=attachment.uploaded_by,
        original_filename=attachment.original_filename,
        file_size=attachment.file_size,
        content_type=attachment.content_type,
        category=attachment.category,
        created_at=attachment.created_at
    )

@router.get(
    "",
    response_model=List[AttachmentResponse],
    status_code=status.HTTP_200_OK,
    summary="List Project Attachments",
    description="Returns all verified document attachments linked to the authorized project."
)
def list_attachments(
    projectId: Union[int, str],
    membership: ProjectMember = Depends(require_project_member),
    db: Session = Depends(get_db)
):
    pid = membership.project_id
    records = db.query(ProjectAttachment).filter(ProjectAttachment.project_id == pid).order_by(ProjectAttachment.created_at.desc()).all()
    return [
        AttachmentResponse(
            attachment_id=r.attachment_id,
            project_id=r.project_id,
            uploaded_by=r.uploaded_by,
            original_filename=r.original_filename,
            file_size=r.file_size,
            content_type=r.content_type,
            category=r.category,
            created_at=r.created_at
        )
        for r in records
    ]

@router.get(
    "/{attachmentId}",
    status_code=status.HTTP_200_OK,
    summary="Download Project Attachment",
    description="Securely streams the requested PDF attachment after checking project membership."
)
def download_attachment(
    projectId: Union[int, str],
    attachmentId: int,
    membership: ProjectMember = Depends(require_project_member),
    db: Session = Depends(get_db)
):
    pid = membership.project_id
    attachment = db.query(ProjectAttachment).filter(
        ProjectAttachment.attachment_id == attachmentId,
        ProjectAttachment.project_id == pid
    ).first()

    if not attachment:
        raise NotFoundError("Attachment not found in this project")

    if not os.path.exists(attachment.storage_path):
        raise NotFoundError("Stored file not found on disk")

    return FileResponse(
        path=attachment.storage_path,
        media_type="application/pdf",
        filename=attachment.original_filename
    )
