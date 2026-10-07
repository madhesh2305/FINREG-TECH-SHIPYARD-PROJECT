from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.projects import router as projects_router
from app.api.v1.project_members import router as project_members_router
from app.api.v1.advisors import router as advisors_router
from app.api.v1.regulatory import router as regulatory_router
from app.api.v1.audit import router as audit_router
from app.api.v1.ai import router as ai_router
from app.api.v1.advice import router as advice_router
from app.api.v1.decisions import router as decisions_router

api_v1_router = APIRouter()

api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(projects_router)
api_v1_router.include_router(project_members_router)
api_v1_router.include_router(advisors_router)
api_v1_router.include_router(regulatory_router)
api_v1_router.include_router(audit_router)
api_v1_router.include_router(ai_router)
api_v1_router.include_router(advice_router)
api_v1_router.include_router(decisions_router)

