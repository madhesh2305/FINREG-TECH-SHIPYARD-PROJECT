from datetime import datetime
from pydantic import BaseModel, Field

class AttachmentResponse(BaseModel):
    attachment_id: int
    project_id: int
    uploaded_by: int
    original_filename: str
    file_size: int
    content_type: str
    category: str
    created_at: datetime
