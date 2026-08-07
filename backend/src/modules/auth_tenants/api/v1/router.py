from fastapi import APIRouter

from src.modules.auth_tenants.api.v1.admin_router import router as admin_router
from src.modules.auth_tenants.api.v1.auth_router import router as auth_router
from src.modules.auth_tenants.api.v1.roles_router import router as roles_router
from src.modules.auth_tenants.api.v1.tenants_router import router as tenants_router
from src.modules.auth_tenants.api.v1.users_router import router as users_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(tenants_router)
router.include_router(users_router)
router.include_router(roles_router)
router.include_router(admin_router)
