import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Point DATABASE_URL to an isolated temporary SQLite database before importing app.main.
_TEST_DB_DIR = tempfile.mkdtemp(prefix="quorum_pytest_")
_TEST_DB_PATH = Path(_TEST_DB_DIR) / "test_quorum.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB_PATH.as_posix()}"
os.environ["ENABLE_SCHEDULER"] = "false"

from app.core.config import get_settings  # noqa: E402

get_settings.cache_clear()

from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_and_seeded_houses(client: TestClient):
    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert health_res.json() == {"status": "ok", "service": "quorum-backend"}

    houses_res = client.get("/api/v1/houses")
    assert houses_res.status_code == 200
    houses = houses_res.json()
    assert len(houses) == 5

    by_slug = {h["slug"]: h for h in houses}
    assert by_slug["congresso-nacional"]["is_followed_by_default"] is True
    assert by_slug["senado-federal"]["is_followed_by_default"] is True
    assert by_slug["alesp"]["is_followed_by_default"] is False
    assert by_slug["cmsp"]["is_followed_by_default"] is False
    assert by_slug["alerj"]["is_followed_by_default"] is False

    senate_res = client.get("/api/v1/houses/senado-federal")
    assert senate_res.status_code == 200
    senate = senate_res.json()
    assert senate["total_seats"] == 81
    assert len(senate["party_composition"]) > 0
    assert all("percentage" in item for item in senate["party_composition"])


def test_politicians_read_only_and_filters(client: TestClient):
    all_res = client.get("/api/v1/politicians")
    assert all_res.status_code == 200
    politicians = all_res.json()
    assert len(politicians) >= 6

    filtered_res = client.get("/api/v1/politicians?house_slug=congresso-nacional&party_acronym=PSB")
    assert filtered_res.status_code == 200
    filtered = filtered_res.json()
    assert len(filtered) == 1
    assert filtered[0]["name"] == "Dep. Helena Vasconcelos"

    search_res = client.get("/api/v1/politicians?search=Lucas")
    assert search_res.status_code == 200
    assert any(p["name"] == "Ver. Lucas Moura Lima" for p in search_res.json())

    detail_res = client.get(f"/api/v1/politicians/{filtered[0]['id']}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert "authored_bills" in detail
    assert "voting_history" in detail
    assert "followers_count" not in detail
    assert "likes_count" not in detail


def test_citizen_vote_and_duplicate_conflict(client: TestClient):
    bills_res = client.get("/api/v1/bills")
    assert bills_res.status_code == 200
    bills = bills_res.json()
    assert len(bills) >= 7
    target = bills[0]
    assert len(target["desjuridiques_summary"]) == 3

    initial_favor = target["votes_favor"]
    vote_res = client.post(
        f"/api/v1/bills/{target['id']}/vote",
        json={"citizen_identifier": "cpf-demo-9988776655", "choice": "favor"},
    )
    assert vote_res.status_code == 200
    vote_data = vote_res.json()
    assert vote_data["votes_favor"] == initial_favor + 1
    assert vote_data["source"] == "web"

    duplicate_res = client.post(
        f"/api/v1/bills/{target['id']}/vote",
        json={"citizen_identifier": "cpf-demo-9988776655", "choice": "against"},
    )
    assert duplicate_res.status_code == 409

    like_res = client.post(f"/api/v1/bills/{target['id']}/like")
    assert like_res.status_code == 200
    assert like_res.json()["likes_count"] == target["likes_count"] + 1


def test_iot_totem_vote_ingestion(client: TestClient):
    bills = client.get("/api/v1/bills").json()
    target = bills[1]
    initial_against = target["votes_against"]

    iot_res = client.post(
        "/api/v1/iot/vote",
        json={
            "totem_id": "totem-metro-se-01",
            "bill_id": target["id"],
            "choice": "against",
        },
    )
    assert iot_res.status_code == 200
    body = iot_res.json()
    assert body["source"] == "iot_totem"
    assert body["votes_against"] == initial_against + 1


def test_dashboard_gold_overview(client: TestClient):
    res = client.get("/api/v1/dashboard/overview")
    assert res.status_code == 200
    data = res.json()
    assert data["total_monitored_bills"] >= 7
    assert data["web_votes"] >= 1
    assert data["iot_totem_votes"] >= 1
    assert data["total_citizen_votes"] > 0
    assert len(data["party_seat_distribution"]) > 0
    assert len(data["bill_comparisons"]) == data["total_monitored_bills"]


def test_auth_and_private_settings(client: TestClient):
    reg_res = client.post(
        "/api/v1/auth/register",
        json={"email": "cidadao.teste@quorum.org.br", "password": "secret123"},
    )
    assert reg_res.status_code == 201
    reg_body = reg_res.json()
    token = reg_body["access_token"]
    assert reg_body["user"]["followed_house_slugs"] == ["congresso-nacional", "senado-federal"]

    headers = {"Authorization": f"Bearer {token}"}
    patch_res = client.patch(
        "/api/v1/users/me",
        headers=headers,
        json={
            "email": "cidadao.atualizado@quorum.org.br",
            "current_password": "secret123",
            "new_password": "newpassword456",
            "urgent_vote_alerts": False,
        },
    )
    assert patch_res.status_code == 200
    updated_user = patch_res.json()
    assert updated_user["email"] == "cidadao.atualizado@quorum.org.br"
    assert updated_user["urgent_vote_alerts"] is False

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "cidadao.atualizado@quorum.org.br", "password": "newpassword456"},
    )
    assert login_res.status_code == 200
    assert login_res.json()["user"]["email"] == "cidadao.atualizado@quorum.org.br"


def test_admin_sync_and_mocked_ingestion(client: TestClient):
    unauthorized = client.post("/api/v1/admin/sync/bills")
    assert unauthorized.status_code == 401

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "dados": [
            {
                "id": 999888,
                "siglaTipo": "PL",
                "numero": 4501,
                "ano": 2026,
                "ementa": "Institui programa nacional de energia solar comunitária e dados abertos de iluminação pública.",
            }
        ]
    }

    with patch("app.workers.ingestion.httpx.Client.get", return_value=mock_response):
        sync_res = client.post(
            "/api/v1/admin/sync/bills",
            headers={"X-Admin-Key": "quorum-admin-secret"},
        )

    assert sync_res.status_code == 200
    sync_body = sync_res.json()
    assert sync_body["bronze_events_recorded"] == 1
    assert sync_body["records_upserted"] == 1

    bills = client.get("/api/v1/bills").json()
    ingested = [b for b in bills if b["external_id"] == "camara-pl-999888"]
    assert len(ingested) == 1
    assert len(ingested[0]["desjuridiques_summary"]) == 3
