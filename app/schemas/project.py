from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field

class ProjectProfileBase(BaseModel):
    description: str = Field(..., min_length=1, description="Detailed project description")
    jurisdiction: str = Field(..., description="Regulatory jurisdiction, e.g. UK / EU")
    regulatory_scope: str = Field(..., description="Applicable regulatory domains, e.g. Anti-Bribery & Corruption (ABC)")
    objectives: str = Field(..., description="Key compliance and business objectives")

class ProjectProfileCreate(ProjectProfileBase):
    pass

class ProjectProfileResponse(ProjectProfileBase):
    model_config = ConfigDict(from_attributes=True)

    project_profile_id: int
    project_id: int
    created_at: datetime
    updated_at: datetime

import uuid
from pydantic import model_validator, computed_field

class ProjectCreate(BaseModel):
    project_name: Optional[str] = Field(None, min_length=2, max_length=200, description="Project Name")
    name: Optional[str] = Field(None, description="Project Name alias")
    project_code: Optional[str] = Field(None, max_length=50, description="Unique Project Code, e.g. PRJ-ABC-01")
    code: Optional[str] = Field(None, description="Project Code alias")
    type: Optional[str] = Field(None, description="Project Type alias")
    description: Optional[str] = Field("Compliance infrastructure project", description="Project Description")
    jurisdiction: str = Field("UK / EU", description="Jurisdiction")
    regulatory_scope: str = Field("Anti-Bribery and Corruption (ABC)", description="Regulatory Scope")
    objectives: str = Field("Establish defensible source-traceable compliance and advisor governance", description="Project Objectives")

    @model_validator(mode="before")
    @classmethod
    def populate_aliases(cls, data):
        if isinstance(data, dict):
            # Resolve project_name
            if not data.get("project_name") and data.get("name"):
                data["project_name"] = data["name"]
            if not data.get("project_name"):
                data["project_name"] = "Untitled Compliance Project"
            # Resolve project_code
            if not data.get("project_code") and data.get("code"):
                data["project_code"] = data["code"]
            if not data.get("project_code"):
                data["project_code"] = f"PRJ-{uuid.uuid4().hex[:6].upper()}"
            # Resolve regulatory_scope from type
            if data.get("type") and data.get("regulatory_scope") in (None, "Anti-Bribery and Corruption (ABC)"):
                data["regulatory_scope"] = data["type"]
            # Ensure description
            if not data.get("description"):
                data["description"] = f"{data.get('project_name')} setup."
        return data

class ProjectUpdate(BaseModel):
    project_name: Optional[str] = Field(None, min_length=2, max_length=200)
    status: Optional[str] = Field(None, pattern="^(ACTIVE|ARCHIVED)$")
    description: Optional[str] = None
    jurisdiction: Optional[str] = None
    regulatory_scope: Optional[str] = None
    objectives: Optional[str] = None

class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    project_id: int
    project_name: str
    project_code: str
    status: str
    created_by: int
    owner_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    profile: Optional[ProjectProfileResponse] = None

    @computed_field
    @property
    def id(self) -> int:
        return self.project_id

    @computed_field
    @property
    def name(self) -> str:
        return self.project_name

    @computed_field
    @property
    def type(self) -> str:
        if self.profile and self.profile.regulatory_scope:
            return self.profile.regulatory_scope
        return "Anti-Bribery & Corruption (ABC)"

class DashboardSummary(BaseModel):
    total_projects: int
    active_projects: int
    archived_projects: int
    total_requirements: int
    total_members: int
    open_requirements: int
    completed_requirements: int
