from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict

class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    audit_event_id: int
    project_id: int
    actor_user_id: int
    actor_name: Optional[str] = None
    event_type: str
    entity_type: str
    entity_id: int
    old_values: Dict[str, Any]
    new_values: Dict[str, Any]
    event_description: str
    created_at: datetime
