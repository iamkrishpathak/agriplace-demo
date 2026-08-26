import os
import sys
import tempfile
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

TEST_DATABASE = Path(tempfile.gettempdir()) / "agriplace_api_test.sqlite3"
TEST_DATABASE.unlink(missing_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DATABASE}"

from fastapi.testclient import TestClient  # noqa: E402

from backend.app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client
    TEST_DATABASE.unlink(missing_ok=True)


def login(client: TestClient, email: str) -> dict[str, str]:
    response = client.post(
        "/auth/login",
        json={"email": email, "password": "AgriPlace@123"},
    )
    assert response.status_code == 200
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_seeded_marketplace_flow(client: TestClient):
    assert client.get("/health").json()["success"] is True

    farmer_headers = login(client, "farmer@agriplace.demo")
    farmer_home = client.get("/farmer/home?lang=hi", headers=farmer_headers)
    assert farmer_home.status_code == 200
    assert farmer_home.json()["data"]["text"]["sell_button"] == "फसल बेचें"

    estimate = client.post(
        "/farmer/sale-estimate",
        headers=farmer_headers,
        json={
            "crop": "Tomato",
            "quantity_kg": 500,
            "grade": "Grade A",
            "available_date": "2026-08-29",
        },
    )
    assert estimate.status_code == 200
    assert estimate.json()["data"]["estimated_net"] > 0

    buyer_headers = login(client, "buyer@agriplace.demo")
    orders = client.get("/buyer/orders", headers=buyer_headers)
    assert orders.status_code == 200
    order = orders.json()["data"][0]
    assert order["total_quantity_kg"] == 2000
    assert order["payment"]["status"] == "HELD"

    transporter_headers = login(client, "transporter@agriplace.demo")
    trips = client.get("/transporter/trips/available", headers=transporter_headers)
    assert trips.status_code == 200
    assert trips.json()["data"][0]["cargo_kg"] == 2000


def test_roles_and_route_capacity_errors(client: TestClient):
    buyer_headers = login(client, "buyer@agriplace.demo")
    denied = client.get("/admin/dashboard", headers=buyer_headers)
    assert denied.status_code == 403
    assert denied.json()["success"] is False

    transporter_headers = login(client, "transporter@agriplace.demo")
    route_payload = {
        "depot": {"label": "Depot", "latitude": 20.0, "longitude": 73.8, "stop_type": "DEPOT"},
        "pickups": [
            {
                "label": "Farm", "latitude": 20.1, "longitude": 73.9,
                "quantity_kg": 2200, "stop_type": "PICKUP",
            }
        ],
        "buyer": {"label": "Buyer", "latitude": 19.1, "longitude": 73.0, "stop_type": "BUYER"},
        "vehicles": [{"label": "Mini truck", "capacity_kg": 1200}],
    }
    capacity = client.post("/routes/optimize", headers=transporter_headers, json=route_payload)
    assert capacity.status_code == 200
    assert capacity.json()["data"]["feasible"] is False
    assert capacity.json()["data"]["split_required"] is True

    route_payload["vehicles"] = []
    no_vehicle = client.post("/routes/optimize", headers=transporter_headers, json=route_payload)
    assert no_vehicle.status_code == 200
    assert no_vehicle.json()["data"]["reason"] == "At least one vehicle is required to optimize a route."
