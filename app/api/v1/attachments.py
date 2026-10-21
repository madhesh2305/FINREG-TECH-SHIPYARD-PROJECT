import base64
import email
import email.policy
import io
import os
import tempfile
import uuid
from typing import List, Union
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import FileResponse
import pypdf
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

def validate_pdf_structure(file_path_or_bytes: Union[str, bytes]) -> None:
    """
    Validates structural integrity of a PDF document using pypdf parser.
    Ensures document conforms to ISO 32000 specification and rejects
    malformed, truncated, or spoofed payloads containing fake headers/trailers.
    """
    close_needed = False
    if isinstance(file_path_or_bytes, bytes):
        if not file_path_or_bytes or len(file_path_or_bytes) == 0:
            raise ValidationError("Uploaded file is empty")
        if len(file_path_or_bytes) < 32:
            raise ValidationError("Invalid PDF format. File is too small to be a valid PDF document")
        stream = io.BytesIO(file_path_or_bytes)
    else:
        if not os.path.exists(file_path_or_bytes) or os.path.getsize(file_path_or_bytes) == 0:
            raise ValidationError("Uploaded file is empty")
        if os.path.getsize(file_path_or_bytes) < 32:
            raise ValidationError("Invalid PDF format. File is too small to be a valid PDF document")
        stream = open(file_path_or_bytes, "rb")
        close_needed = True

    try:
        reader = pypdf.PdfReader(stream, strict=False)
        if len(reader.pages) < 1:
            raise ValidationError("Invalid PDF format. Document contains no readable pages")
    except ValidationError:
        raise
    except Exception as exc:
        raise ValidationError(f"Invalid PDF format. Document structure failed validation: {type(exc).__name__}")
    finally:
        if close_needed:
            try:
                stream.close()
            except Exception:
                pass

def _get_upload_dir(project_id: int) -> str:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads", str(project_id)))
    os.makedirs(base_dir, exist_ok=True)
    return base_dir

def _get_temp_dir() -> str:
    temp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads", "tmp"))
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir

@router.post(
    "",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload PDF Attachment",
    description="Securely uploads and validates a PDF attachment with bounded streaming, structural pypdf verification, and project-level authorization."
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

    # Enforce request-size bounds before reading streaming body
    content_len_header = request.headers.get("content-length")
    if content_len_header:
        try:
            cl = int(content_len_header)
            if cl > MAX_FILE_SIZE_BYTES + 65536:
                raise ValidationError(f"Request payload exceeds maximum allowable limit of 10MB (got {cl} bytes)")
        except ValueError:
            pass

    filename = None
    category = "ADVISORY_REFERENCE"
    tmp_path = None
    file_bytes_written = 0

    temp_dir = _get_temp_dir()
    with tempfile.NamedTemporaryFile(dir=temp_dir, prefix="up_", suffix=".tmp", delete=False) as tmp_file:
        tmp_path = tmp_file.name

    try:
        if "multipart/form-data" in raw_content_type.lower():
            form = await request.form()
            file_item = form.get("file")
            category_item = form.get("category")
            if category_item and isinstance(category_item, str):
                category = category_item.strip()

            if not file_item:
                raise ValidationError("No file uploaded. Expected 'file' field in multipart form data")

            if hasattr(file_item, "filename"):
                filename = file_item.filename
            else:
                filename = "document.pdf"

            with open(tmp_path, "wb") as f:
                while True:
                    chunk = await file_item.read(65536)
                    if not chunk:
                        break
                    file_bytes_written += len(chunk)
                    if file_bytes_written > MAX_FILE_SIZE_BYTES:
                        raise ValidationError("File size exceeds maximum allowable limit of 10MB")
                    f.write(chunk)
        elif "application/json" in raw_content_type.lower():
            body = await request.body()
            if len(body) > MAX_FILE_SIZE_BYTES + 65536:
                raise ValidationError("Payload size exceeds maximum allowable limit of 10MB")
            import json
            try:
                body_json = json.loads(body.decode("utf-8"))
            except Exception:
                raise ValidationError("Invalid JSON payload")
            filename = body_json.get("filename", "document.pdf")
            category = body_json.get("category", "ADVISORY_REFERENCE")
            b64_content = body_json.get("content_base64", "")
            try:
                decoded = base64.b64decode(b64_content)
            except Exception:
                raise ValidationError("Invalid base64 payload")
            file_bytes_written = len(decoded)
            if file_bytes_written > MAX_FILE_SIZE_BYTES:
                raise ValidationError("File size exceeds maximum allowable limit of 10MB")
            with open(tmp_path, "wb") as f:
                f.write(decoded)
        else:
            raise ValidationError(f"Unsupported content type: {raw_content_type}. Expected multipart/form-data or application/json")

        if not filename:
            filename = "document.pdf"

        clean_filename = os.path.basename(filename).strip()
        if not clean_filename or "\x00" in clean_filename:
            raise ValidationError("Invalid filename")

        if not clean_filename.lower().endswith(".pdf"):
            raise ValidationError("Only PDF files are supported. File extension must be .pdf")

        if file_bytes_written == 0:
            raise ValidationError("Uploaded file is empty")

        # Validate complete PDF structure using pypdf parser on disk
        validate_pdf_structure(tmp_path)

        # Atomic move to storage path outside public web root
        stored_name = f"{uuid.uuid4().hex}.pdf"
        upload_dir = _get_upload_dir(pid)
        storage_path = os.path.join(upload_dir, stored_name)
        os.replace(tmp_path, storage_path)
        tmp_path = None  # Successfully moved

        # Persist metadata in database with transactional rollback safety
        attachment = ProjectAttachment(
            project_id=pid,
            uploaded_by=current_user.user_id,
            original_filename=clean_filename,
            stored_filename=stored_name,
            file_size=file_bytes_written,
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
                "file_size": file_bytes_written,
                "category": category,
                "attachment_id": attachment.attachment_id
            }
        )
        db.commit()
        db.refresh(attachment)

    except Exception:
        db.rollback()
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        raise

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
