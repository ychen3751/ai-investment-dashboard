"""Tests for the auth API endpoints."""
import pytest
from httpx import AsyncClient


class TestRegister:
    async def test_register_success(self, client: AsyncClient):
        res = await client.post(
            "/api/auth/register",
            json={"email": "new@test.com", "username": "newuser", "password": "secure123"},
        )
        assert res.status_code == 201
        data = res.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_register_duplicate_email(self, client: AsyncClient):
        await client.post(
            "/api/auth/register",
            json={"email": "dup@test.com", "username": "user1", "password": "secure123"},
        )
        res = await client.post(
            "/api/auth/register",
            json={"email": "dup@test.com", "username": "user2", "password": "secure123"},
        )
        assert res.status_code == 409

    async def test_register_short_password(self, client: AsyncClient):
        res = await client.post(
            "/api/auth/register",
            json={"email": "short@test.com", "username": "shortpw", "password": "123"},
        )
        assert res.status_code == 422

    async def test_register_invalid_email(self, client: AsyncClient):
        res = await client.post(
            "/api/auth/register",
            json={"email": "not-an-email", "username": "bad", "password": "secure123"},
        )
        assert res.status_code == 422

    async def test_register_empty_body(self, client: AsyncClient):
        res = await client.post("/api/auth/register", json={})
        assert res.status_code == 422


class TestLogin:
    async def test_login_success(self, client: AsyncClient):
        await client.post(
            "/api/auth/register",
            json={"email": "login@test.com", "username": "loginuser", "password": "secure123"},
        )
        res = await client.post(
            "/api/auth/login",
            json={"email": "login@test.com", "password": "secure123"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_login_wrong_password(self, client: AsyncClient):
        await client.post(
            "/api/auth/register",
            json={"email": "wrongpw@test.com", "username": "wrongpw", "password": "secure123"},
        )
        res = await client.post(
            "/api/auth/login",
            json={"email": "wrongpw@test.com", "password": "wrongpassword"},
        )
        assert res.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        res = await client.post(
            "/api/auth/login",
            json={"email": "nobody@test.com", "password": "secure123"},
        )
        assert res.status_code == 401


class TestMe:
    async def test_me_authenticated(self, client: AsyncClient, auth_headers: dict):
        res = await client.get("/api/auth/me", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["is_active"] is True
        assert "@example.com" in data["email"]
        assert data["id"] is not None

    async def test_me_unauthenticated(self, client: AsyncClient):
        res = await client.get("/api/auth/me")
        assert res.status_code == 401

    async def test_me_invalid_token(self, client: AsyncClient):
        res = await client.get("/api/auth/me", headers={"Authorization": "Bearer invalidtoken"})
        assert res.status_code == 401


class TestRefresh:
    async def test_refresh_success(self, client: AsyncClient):
        reg = await client.post(
            "/api/auth/register",
            json={"email": "refresh@test.com", "username": "refreshuser", "password": "secure123"},
        )
        refresh_token = reg.json()["refresh_token"]

        res = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_revoked(self, client: AsyncClient):
        reg = await client.post(
            "/api/auth/register",
            json={"email": "revoke@test.com", "username": "revokeuser", "password": "secure123"},
        )
        refresh_token = reg.json()["refresh_token"]

        await client.post("/api/auth/logout", json={"refresh_token": refresh_token})
        res = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
        assert res.status_code == 401


class TestLogout:
    async def test_logout_success(self, client: AsyncClient):
        # Register a user to get a refresh token
        reg = await client.post(
            "/api/auth/register",
            json={"email": "logout_test@example.com", "username": "logout_user", "password": "testpass123"},
        )
        assert reg.status_code == 201
        rt = reg.json()["refresh_token"]

        res = await client.post("/api/auth/logout", json={"refresh_token": rt})
        assert res.status_code == 200
        assert res.json()["message"] == "Logged out successfully"
