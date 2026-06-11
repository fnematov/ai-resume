from fastapi import APIRouter

from app.api.v1 import (
    analytics,
    applications,
    auth,
    automation,
    organizations,
    scheduling,
    templates,
    telegram,
    vacancies,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(vacancies.router, prefix="/vacancies", tags=["vacancies"])
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])
api_router.include_router(scheduling.router, prefix="/scheduling", tags=["scheduling"])
api_router.include_router(automation.router, prefix="/automation-rules", tags=["automation"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(telegram.router, prefix="/telegram", tags=["telegram"])
