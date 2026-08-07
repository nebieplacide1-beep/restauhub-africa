"""Bout-en-bout : inscription -> mot de passe oublié -> réinitialisation ->
connexion avec le nouveau mot de passe uniquement. Le mailer est remplacé par
une doublure capturante (override de dépendance FastAPI) pour récupérer le
token envoyé "par email" sans dépendre d'un vrai service de messagerie."""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app
from src.modules.auth_tenants.api.deps import get_mailer
from src.tests.fakes import FakeMailer


@pytest.mark.asyncio
async def test_forgot_then_reset_password_flow() -> None:
    email = f"e2e-reset-{uuid4()}@test.ci"
    fake_mailer = FakeMailer()
    app.dependency_overrides[get_mailer] = lambda: fake_mailer
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://test/api/v1") as client:
            await client.post(
                "/tenants",
                json={
                    "tenant_name": f"E2E Reset Tenant {uuid4()}",
                    "country": "CI",
                    "default_currency": "XOF",
                    "default_locale": "fr",
                    "admin_email": email,
                    "admin_password": "Str0ng!Passw0rd",
                },
            )

            forgot_response = await client.post("/auth/password/forgot", json={"identifier": email})
            assert forgot_response.status_code == 202

            assert len(fake_mailer.password_resets) == 1
            raw_token = fake_mailer.password_resets[0]["reset_link"].rsplit("/", 1)[-1]

            reset_response = await client.post(
                "/auth/password/reset",
                json={"token": raw_token, "new_password": "N3wStr0ng!Passw0rd"},
            )
            assert reset_response.status_code == 204

            old_password_login = await client.post(
                "/auth/login", json={"identifier": email, "password": "Str0ng!Passw0rd"}
            )
            assert old_password_login.status_code == 401

            new_password_login = await client.post(
                "/auth/login", json={"identifier": email, "password": "N3wStr0ng!Passw0rd"}
            )
            assert new_password_login.status_code == 200

            reuse_response = await client.post(
                "/auth/password/reset",
                json={"token": raw_token, "new_password": "AnotherStr0ng!Pass"},
            )
            assert reuse_response.status_code == 401
    finally:
        app.dependency_overrides.pop(get_mailer, None)


@pytest.mark.asyncio
async def test_forgot_password_is_silent_for_unknown_identifier() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as client:
        response = await client.post(
            "/auth/password/forgot", json={"identifier": f"nobody-{uuid4()}@nowhere.ci"}
        )
    assert response.status_code == 202
