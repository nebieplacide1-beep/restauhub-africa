"""Bout-en-bout : inscription -> création de deux succursales -> invitation et
rattachement d'un Gérant à une seule d'entre elles -> vérifie que le Gérant ne
voit que sa succursale (BR2-14) alors que l'Administrateur (tenant-wide, BR2-08)
voit les deux."""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app
from src.modules.auth_tenants.api.deps import get_mailer
from src.tests.fakes import FakeMailer


@pytest.mark.asyncio
async def test_gerant_only_sees_assigned_succursale() -> None:
    admin_email = f"admin-{uuid4()}@test.ci"
    gerant_email = f"gerant-{uuid4()}@test.ci"
    fake_mailer = FakeMailer()
    app.dependency_overrides[get_mailer] = lambda: fake_mailer
    transport = ASGITransport(app=app)

    try:
        async with AsyncClient(transport=transport, base_url="http://test/api/v1") as client:
            await client.post(
                "/tenants",
                json={
                    "tenant_name": f"E2E Succursales {uuid4()}",
                    "country": "CI",
                    "default_currency": "XOF",
                    "default_locale": "fr",
                    "admin_email": admin_email,
                    "admin_password": "Str0ng!Passw0rd",
                },
            )
            login = await client.post(
                "/auth/login", json={"identifier": admin_email, "password": "Str0ng!Passw0rd"}
            )
            admin_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

            succ_a = await client.post(
                "/succursales",
                json={
                    "name": "Chez Awa - Plateau",
                    "address_line": "12 rue X",
                    "city": "Abidjan",
                    "country": "CI",
                    "default_currency": "XOF",
                    "default_locale": "fr",
                },
                headers=admin_headers,
            )
            assert succ_a.status_code == 201, succ_a.text
            succ_b = await client.post(
                "/succursales",
                json={
                    "name": "Chez Awa - Cocody",
                    "address_line": "5 rue Y",
                    "city": "Abidjan",
                    "country": "CI",
                    "default_currency": "XOF",
                    "default_locale": "fr",
                },
                headers=admin_headers,
            )
            assert succ_b.status_code == 201, succ_b.text
            succ_a_id = succ_a.json()["id"]

            admin_list = await client.get("/succursales", headers=admin_headers)
            assert len(admin_list.json()) == 2

            invite = await client.post(
                "/users/invitations",
                json={"email": gerant_email, "role_code": "gerant"},
                headers=admin_headers,
            )
            assert invite.status_code == 201, invite.text
            raw_invitation_token = fake_mailer.invitations[0]["activation_link"].rsplit("/", 1)[-1]

            accept = await client.post(
                f"/invitations/{raw_invitation_token}/accept", json={"password": "Str0ng!Passw0rd"}
            )
            assert accept.status_code == 201, accept.text
            gerant_user_id = accept.json()["id"]

            assign = await client.post(
                f"/succursales/{succ_a_id}/staff",
                json={"user_id": gerant_user_id, "role_code": "gerant"},
                headers=admin_headers,
            )
            assert assign.status_code == 204, assign.text

            gerant_login = await client.post(
                "/auth/login", json={"identifier": gerant_email, "password": "Str0ng!Passw0rd"}
            )
            gerant_headers = {"Authorization": f"Bearer {gerant_login.json()['access_token']}"}

            gerant_list = await client.get("/succursales", headers=gerant_headers)
            assert gerant_list.status_code == 200, gerant_list.text
            assert [s["id"] for s in gerant_list.json()] == [succ_a_id]

            staff = await client.get(f"/succursales/{succ_a_id}/staff", headers=admin_headers)
            assert staff.status_code == 200, staff.text
            assert len(staff.json()) == 1
            assert staff.json()[0]["role_codes"] == ["gerant"]

            forbidden_update = await client.patch(
                f"/succursales/{succ_b.json()['id']}",
                json={"name": "Piraté"},
                headers=gerant_headers,
            )
            assert forbidden_update.status_code == 403
    finally:
        app.dependency_overrides.pop(get_mailer, None)
