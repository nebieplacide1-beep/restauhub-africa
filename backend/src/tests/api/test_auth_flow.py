"""Bout-en-bout : inscription -> connexion -> /auth/me -> refresh -> logout.
Exécuté contre une vraie base (voir tests/api/conftest.py) via ASGI, sans
serveur HTTP réel (httpx.ASGITransport)."""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.mark.asyncio
async def test_register_login_me_refresh_logout() -> None:
    email = f"e2e-{uuid4()}@test.ci"
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as client:
        register_response = await client.post(
            "/tenants",
            json={
                "tenant_name": f"E2E Tenant {uuid4()}",
                "country": "CI",
                "default_currency": "XOF",
                "default_locale": "fr",
                "admin_email": email,
                "admin_password": "Str0ng!Passw0rd",
            },
        )
        assert register_response.status_code == 201, register_response.text

        login_response = await client.post(
            "/auth/login", json={"identifier": email, "password": "Str0ng!Passw0rd"}
        )
        assert login_response.status_code == 200, login_response.text
        tokens = login_response.json()
        assert "access_token" in tokens and "refresh_token" in tokens

        me_response = await client.get(
            "/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert me_response.status_code == 200, me_response.text
        assert me_response.json()["email"] == email
        assert "users:manage" in me_response.json()["permissions"]

        refresh_response = await client.post(
            "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        assert refresh_response.status_code == 200, refresh_response.text
        new_tokens = refresh_response.json()
        assert new_tokens["refresh_token"] != tokens["refresh_token"]

        logout_response = await client.post(
            "/auth/logout",
            json={"refresh_token": new_tokens["refresh_token"]},
            headers={"Authorization": f"Bearer {new_tokens['access_token']}"},
        )
        assert logout_response.status_code == 204

        reuse_response = await client.post(
            "/auth/refresh", json={"refresh_token": new_tokens["refresh_token"]}
        )
        assert reuse_response.status_code == 401


@pytest.mark.asyncio
async def test_wrong_password_returns_401_with_error_code() -> None:
    email = f"e2e-{uuid4()}@test.ci"
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as client:
        await client.post(
            "/tenants",
            json={
                "tenant_name": f"E2E Tenant {uuid4()}",
                "country": "CI",
                "default_currency": "XOF",
                "default_locale": "fr",
                "admin_email": email,
                "admin_password": "Str0ng!Passw0rd",
            },
        )
        response = await client.post("/auth/login", json={"identifier": email, "password": "wrong"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"
