from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, computed_field

class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    audit_event_id: int
    project_id: Optional[int] = None
    actor_user_id: Optional[int] = None
    actor_name: Optional[str] = None
    actor_role: Optional[str] = None
    project_code: Optional[str] = None
    event_type: str
    entity_type: str
    entity_id: int
    old_values: Dict[str, Any]
    new_values: Dict[str, Any]
    event_description: str
    created_at: datetime

    @computed_field
    @property
    def id(self) -> str:
        return f"AUD-{str(self.audit_event_id).zfill(4)}"

    @computed_field
    @property
    def dateTime(self) -> str:
        if self.created_at:
            return self.created_at.strftime("%d %b %Y, %H:%M UTC")
        return "Recently"

    @computed_field
    @property
    def timestamp(self) -> str:
        if self.created_at:
            return self.created_at.strftime("%d %b %Y, %H:%M UTC")
        return "Recently"

    @computed_field
    @property
    def user(self) -> str:
        return self.actor_name or "System"

    @computed_field
    @property
    def role(self) -> str:
        return self.actor_role or "Platform"

    @computed_field
    @property
    def action(self) -> str:
        return self.event_type.replace("_", " ").title()

    @computed_field
    @property
    def eventType(self) -> str:
        return self.event_type

    @computed_field
    @property
    def relatedProject(self) -> str:
        if self.project_code:
            return self.project_code
        if self.project_id:
            return f"PRJ-{str(self.project_id).zfill(3)}"
        return "Platform System"

    @computed_field
    @property
    def affectedResource(self) -> str:
        if self.project_code:
            return f"{self.project_code} ({self.entity_type})"
        return f"{self.entity_type} #{self.entity_id}"

    @computed_field
    @property
    def result(self) -> str:
        return "Success"

    @computed_field
    @property
    def resultType(self) -> str:
        return "success"

    @computed_field
    @property
    def resultBadgeClass(self) -> str:
        return "border-emerald-800/80 bg-emerald-950/40 text-emerald-300"

    @computed_field
    @property
    def resultDotClass(self) -> str:
        return "bg-emerald-400"

    @computed_field
    @property
    def relevantDetails(self) -> str:
        return self.event_description

    @computed_field
    @property
    def eventCategory(self) -> str:
        if self.project_id:
            return "Project Management"
        if "USER" in self.event_type or "ROLE" in self.event_type:
            return "Identity & Access"
        return "System Audit"
