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

class ProjectCreate(BaseModel):
    project_name: str = Field(..., min_length=2, max_length=200, description="Project Name")
    project_code: str = Field(..., min_length=2, max_length=50, description="Unique Project Code, e.g. PRJ-ABC-01")
    description: str = Field(..., description="Project Description")
    jurisdiction: str = Field("UK / EU", description="Jurisdiction")
    regulatory_scope: str = Field("Anti-Bribery and Corruption (ABC)", description="Regulatory Scope")
    objectives: str = Field("Establish defensible source-traceable compliance and advisor governance", description="Project Objectives")

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

class DashboardSummary(BaseModel):
    total_projects: int
    active_projects: int
    archived_projects: int
    total_requirements: int
    total_members: int
    open_requirements: int
    completed_requirements: int
