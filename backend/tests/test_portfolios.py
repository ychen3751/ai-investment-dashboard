"""Tests for portfolio CRUD endpoints."""
import pytest
from httpx import AsyncClient


class TestCreatePortfolio:
    async def test_create_success(self, client: AsyncClient, auth_headers: dict):
        res = await client.post("/api/portfolios", json={"name": "My Test Portfolio"}, headers=auth_headers)
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "My Test Portfolio"
        assert "id" in data

    async def test_create_with_description(self, client: AsyncClient, auth_headers: dict):
        res = await client.post(
            "/api/portfolios",
            json={"name": "Tech Stocks", "description": "Long-term tech holdings"},
            headers=auth_headers,
        )
        assert res.status_code == 201
        assert res.json()["description"] == "Long-term tech holdings"

    async def test_create_empty_name(self, client: AsyncClient, auth_headers: dict):
        res = await client.post("/api/portfolios", json={"name": ""}, headers=auth_headers)
        assert res.status_code == 422

    async def test_create_unauthenticated(self, client: AsyncClient):
        res = await client.post("/api/portfolios", json={"name": "Should Fail"})
        assert res.status_code == 401


class TestListPortfolios:
    async def test_list_empty(self, client: AsyncClient, auth_headers: dict):
        res = await client.get("/api/portfolios", headers=auth_headers)
        assert res.status_code == 200
        assert res.json() == []

    async def test_list_with_portfolios(self, client: AsyncClient, auth_headers: dict):
        await client.post("/api/portfolios", json={"name": "Portfolio A"}, headers=auth_headers)
        await client.post("/api/portfolios", json={"name": "Portfolio B"}, headers=auth_headers)
        res = await client.get("/api/portfolios", headers=auth_headers)
        assert res.status_code == 200
        assert len(res.json()) == 2


class TestGetPortfolio:
    async def test_get_success(self, client: AsyncClient, auth_headers: dict):
        create = await client.post("/api/portfolios", json={"name": "My Portfolio"}, headers=auth_headers)
        pid = create.json()["id"]
        res = await client.get(f"/api/portfolios/{pid}", headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["name"] == "My Portfolio"

    async def test_get_not_found(self, client: AsyncClient, auth_headers: dict):
        import uuid
        res = await client.get(f"/api/portfolios/{uuid.uuid4()}", headers=auth_headers)
        assert res.status_code == 404

    async def test_get_other_users_portfolio(self, client: AsyncClient, auth_headers: dict):
        create = await client.post("/api/portfolios", json={"name": "Secret"}, headers=auth_headers)
        pid = create.json()["id"]

        # Register a second user
        await client.post(
            "/api/auth/register",
            json={"email": "other@test.com", "username": "other", "password": "secure123"},
        )
        login = await client.post(
            "/api/auth/login",
            json={"email": "other@test.com", "password": "secure123"},
        )
        other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        res = await client.get(f"/api/portfolios/{pid}", headers=other_headers)
        assert res.status_code == 404


class TestDeletePortfolio:
    async def test_delete_success(self, client: AsyncClient, auth_headers: dict):
        create = await client.post("/api/portfolios", json={"name": "Delete Me"}, headers=auth_headers)
        pid = create.json()["id"]
        res = await client.delete(f"/api/portfolios/{pid}", headers=auth_headers)
        assert res.status_code == 204


class TestHoldings:
    async def test_add_holding(self, client: AsyncClient, auth_headers: dict):
        create = await client.post("/api/portfolios", json={"name": "Holdings Test"}, headers=auth_headers)
        pid = create.json()["id"]

        res = await client.post(
            f"/api/portfolios/{pid}/holdings",
            json={"symbol": "AAPL", "quantity": 10, "average_cost_basis": 150.00},
            headers=auth_headers,
        )
        assert res.status_code == 201
        data = res.json()
        assert data["symbol"] == "AAPL"
        assert data["quantity"] == "10.00000000"

    async def test_add_duplicate_symbol_merges(self, client: AsyncClient, auth_headers: dict):
        create = await client.post("/api/portfolios", json={"name": "Merge Test"}, headers=auth_headers)
        pid = create.json()["id"]

        await client.post(
            f"/api/portfolios/{pid}/holdings",
            json={"symbol": "AAPL", "quantity": 10, "average_cost_basis": 100.00},
            headers=auth_headers,
        )
        res = await client.post(
            f"/api/portfolios/{pid}/holdings",
            json={"symbol": "AAPL", "quantity": 5, "average_cost_basis": 120.00},
            headers=auth_headers,
        )
        assert res.status_code == 201
        data = res.json()
        # Weighted avg: (10*100 + 5*120) / 15 = (1000 + 600) / 15 = 1600 / 15 = 106.6667
        assert data["quantity"] == "15.00000000"
        assert float(data["average_cost_basis"]) == pytest.approx(106.6667, rel=0.01)

    async def test_add_holding_invalid_symbol(self, client: AsyncClient, auth_headers: dict):
        create = await client.post("/api/portfolios", json={"name": "Invalid"}, headers=auth_headers)
        pid = create.json()["id"]
        res = await client.post(
            f"/api/portfolios/{pid}/holdings",
            json={"symbol": "", "quantity": 10, "average_cost_basis": 150.00},
            headers=auth_headers,
        )
        assert res.status_code == 422

    async def test_edit_holding(self, client: AsyncClient, auth_headers: dict):
        create = await client.post("/api/portfolios", json={"name": "Edit Test"}, headers=auth_headers)
        pid = create.json()["id"]
        add = await client.post(
            f"/api/portfolios/{pid}/holdings",
            json={"symbol": "AAPL", "quantity": 10, "average_cost_basis": 150.00},
            headers=auth_headers,
        )
        hid = add.json()["id"]

        res = await client.put(
            f"/api/portfolios/{pid}/holdings/{hid}",
            json={"quantity": 25, "average_cost_basis": 140.00},
            headers=auth_headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["quantity"] == "25.00000000"
        assert float(data["average_cost_basis"]) == 140.00

    async def test_delete_holding(self, client: AsyncClient, auth_headers: dict):
        create = await client.post("/api/portfolios", json={"name": "Delete Hld"}, headers=auth_headers)
        pid = create.json()["id"]
        add = await client.post(
            f"/api/portfolios/{pid}/holdings",
            json={"symbol": "AAPL", "quantity": 10, "average_cost_basis": 150.00},
            headers=auth_headers,
        )
        hid = add.json()["id"]

        res = await client.delete(f"/api/portfolios/{pid}/holdings/{hid}", headers=auth_headers)
        assert res.status_code == 204

        # Verify empty
        holdings = await client.get(f"/api/portfolios/{pid}/holdings", headers=auth_headers)
        assert holdings.json() == []
