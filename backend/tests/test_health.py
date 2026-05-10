"""Health endpoint test."""
from httpx import AsyncClient


class TestHealth:
    async def test_health(self, client: AsyncClient):
        res = await client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert "app" in data
