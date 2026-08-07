from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.modules.auth_tenants.api.v1.router import router as auth_tenants_router
from src.modules.succursales.api.v1.succursales_router import router as succursales_router
from src.shared_kernel.exceptions import DomainError


def create_app() -> FastAPI:
    app = FastAPI(
        title="RestauHub Africa API",
        description=(
            "Module 1 : Authentification & gestion des tenants — "
            "Module 2 : Restaurants & succursales"
        ),
        version="0.1.0",
    )

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        """Traduit les exceptions métier en réponses HTTP au format défini par
        docs/modules/01-auth-tenants/06-api-specification.md#66-codes-derreur-communs."""
        return JSONResponse(
            status_code=exc.http_status,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    app.include_router(auth_tenants_router, prefix="/api/v1")
    app.include_router(succursales_router, prefix="/api/v1")

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
