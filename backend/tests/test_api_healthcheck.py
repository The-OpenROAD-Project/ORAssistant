import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.api.routers.healthcheck import router, HealthCheckResponse


class TestHealthCheckAPI:
    """Test suite for healthcheck API endpoints."""

    @pytest.fixture
    def app(self):
        """Create FastAPI application with healthcheck router."""
        app = FastAPI()
        app.include_router(router)
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def test_healthcheck_endpoint_success(self, client):
        """Test healthcheck endpoint returns success response."""
        response = client.get("/healthcheck")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_healthcheck_response_model(self):
        """Test HealthCheckResponse model."""
        response = HealthCheckResponse(status="ok")

        assert response.status == "ok"
        assert response.model_dump() == {"status": "ok"}

    def test_healthcheck_response_model_validation(self):
        """Test HealthCheckResponse model validation."""
        # Test with valid status
        response = HealthCheckResponse(status="healthy")
        assert response.status == "healthy"

        # Test with empty status
        response = HealthCheckResponse(status="")
        assert response.status == ""

    @pytest.mark.integration
    def test_healthcheck_endpoint_headers(self, client):
        """Test healthcheck endpoint response headers."""
        response = client.get("/healthcheck")

        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_healthcheck_endpoint_multiple_requests(self, client):
        """Test healthcheck endpoint handles multiple requests."""
        for _ in range(5):
            response = client.get("/healthcheck")
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_healthcheck_function_direct_call(self):
        """Test healthcheck function can be called directly."""
        from src.api.routers.healthcheck import healthcheck

        result = await healthcheck()

        assert isinstance(result, HealthCheckResponse)
        assert result.status == "ok"
