import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

# Patch redis.Redis before importing the app
# so the app never tries to connect to a real Redis during tests
with patch("redis.Redis") as mock_redis_class:
    mock_redis_class.return_value = MagicMock()
    from main import app, r

client = TestClient(app)


# ── Test 1: Health endpoint ───────────────────────────────────────
def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ── Test 2: Create job returns a job_id ──────────────────────────
def test_create_job_returns_job_id():
    r.lpush = MagicMock(return_value=1)
    r.hset = MagicMock(return_value=1)

    response = client.post("/jobs")

    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert len(data["job_id"]) == 36  # UUID4 length


# ── Test 3: Create job calls Redis with correct key ───────────────
def test_create_job_pushes_to_correct_queue():
    r.lpush = MagicMock(return_value=1)
    r.hset = MagicMock(return_value=1)

    client.post("/jobs")

    # Confirm it pushed to "jobs" not "job"
    call_args = r.lpush.call_args
    assert call_args[0][0] == "jobs", \
        f"Expected queue 'jobs' but got '{call_args[0][0]}'"


# ── Test 4: Get job status returns correct shape ──────────────────
def test_get_job_status_returns_status():
    r.hget = MagicMock(return_value=b"queued")

    response = client.get("/jobs/test-job-id-123")

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == "test-job-id-123"
    assert data["status"] == "queued"


# ── Test 5: Job not found returns 404 ────────────────────────────
def test_get_missing_job_returns_404():
    r.hget = MagicMock(return_value=None)

    response = client.get("/jobs/nonexistent-id")

    assert response.status_code == 404
    assert "detail" in response.json()


# ── Test 6: Redis down on POST returns 503 ───────────────────────
def test_create_job_redis_down_returns_503():
    from redis.exceptions import ConnectionError as RedisConnectionError
    r.lpush = MagicMock(side_effect=RedisConnectionError("Redis is down"))

    response = client.post("/jobs")

    assert response.status_code == 503
    assert response.json()["detail"] == "Queue unavailable"


# ── Test 7: Redis down on GET returns 503 ────────────────────────
def test_get_job_redis_down_returns_503():
    from redis.exceptions import ConnectionError as RedisConnectionError
    r.hget = MagicMock(side_effect=RedisConnectionError("Redis is down"))

    response = client.get("/jobs/some-id")

    assert response.status_code == 503
    assert response.json()["detail"] == "Queue unavailable"
