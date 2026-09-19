import logging
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

import app as app_module
import carpark_service
from logging_service import request_logs, log_request


client = TestClient(app_module.app)


# ---------------------------------------------------------
# RESET SHARED STATE BEFORE EVERY TEST
# ---------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_state():
    request_logs.clear()
    carpark_service.carpark_cache.clear()

    yield

    request_logs.clear()
    carpark_service.carpark_cache.clear()


# ---------------------------------------------------------
# BASIC API
# ---------------------------------------------------------

def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["Message"] == "SmartPark API running"


# ---------------------------------------------------------
# FIND CARPARKS - SUCCESS
# ---------------------------------------------------------

def test_find_carparks_success(monkeypatch):

    fake_results = [
        {
            "carpark_id": "CBD_001",
            "name": "CBD Car Park 1",
            "available_parking": 20,
            "occupied_parking": 10,
            "total_parking": 30,
            "occupied_percentage": 0.90,
            "cached": False
        },
        {
            "carpark_id": "CBD_002",
            "name": "CBD Car Park 2",
            "available_parking": 15,
            "occupied_parking": 15,
            "total_parking": 30,
            "occupied_percentage": 0.88,
            "cached": False
        }
    ]

    monkeypatch.setattr(
        app_module,
        "find_best_carparks",
        lambda n: fake_results
    )

    response = client.get(
        "/api/find-carparks",
        params={
            "uuid": "test-user-1",
            "n": 2
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["uuid"] == "test-user-1"
    assert data["status"] == "success"
    assert data["requested_n"] == 2
    assert len(data["results"]) == 2


# ---------------------------------------------------------
# FIND CARPARKS - n MUST BE > 0
# ---------------------------------------------------------

def test_find_carparks_rejects_zero():

    response = client.get(
        "/api/find-carparks",
        params={
            "uuid": "test-user",
            "n": 0
        }
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "n must be greater than 0"
    )


# ---------------------------------------------------------
# FIND CARPARKS - 2*n VALIDATION
# ---------------------------------------------------------

def test_find_carparks_rejects_too_large_n():

    # 10 carparks currently exist.
    # n=6 requires inspection of 12 carparks.
    response = client.get(
        "/api/find-carparks",
        params={
            "uuid": "test-user",
            "n": 6
        }
    )

    assert response.status_code == 400

    assert "Not enough car parks" in response.json()["detail"]


# ---------------------------------------------------------
# FIND CARPARKS - INTERNAL FAILURE RETURNS 500
# ---------------------------------------------------------

def test_find_carparks_handles_internal_error(monkeypatch):

    def fake_failure(n):
        raise RuntimeError("Fake YOLO failure")

    monkeypatch.setattr(
        app_module,
        "find_best_carparks",
        fake_failure
    )

    response = client.get(
        "/api/find-carparks",
        params={
            "uuid": "failure-user",
            "n": 2
        }
    )

    assert response.status_code == 500

    assert response.json()["detail"] == (
        "Failed to find car parks. Please try again later."
    )


# ---------------------------------------------------------
# CACHE MISS -> CACHE HIT
# ---------------------------------------------------------

def test_carpark_cache(monkeypatch):

    inference_counter = {
        "count": 0
    }

    def fake_find_parking(image_path):

        inference_counter["count"] += 1

        return {
            "available_parking": 20,
            "occupied_parking": 10,
            "total_parking": 30,
            "occupied_percentage": 0.91
        }

    monkeypatch.setattr(
        carpark_service,
        "find_parking",
        fake_find_parking
    )

    test_carpark = carpark_service.carparks[0]

    first_result = carpark_service.analyse_carpark(
        test_carpark
    )

    second_result = carpark_service.analyse_carpark(
        test_carpark
    )

    assert first_result["cached"] is False
    assert second_result["cached"] is True

    # YOLO should only have been called once
    assert inference_counter["count"] == 1


# ---------------------------------------------------------
# CACHE EXPIRY
# ---------------------------------------------------------

def test_cache_expiry(monkeypatch):

    inference_counter = {
        "count": 0
    }

    def fake_find_parking(image_path):

        inference_counter["count"] += 1

        return {
            "available_parking": 20,
            "occupied_parking": 10,
            "total_parking": 30,
            "occupied_percentage": 0.91
        }

    monkeypatch.setattr(
        carpark_service,
        "find_parking",
        fake_find_parking
    )

    # Force immediate expiry
    monkeypatch.setattr(
        carpark_service,
        "CACHE_TTL_secs",
        0
    )

    test_carpark = carpark_service.carparks[0]

    first_result = carpark_service.analyse_carpark(
        test_carpark
    )

    second_result = carpark_service.analyse_carpark(
        test_carpark
    )

    assert first_result["cached"] is False
    assert second_result["cached"] is False

    assert inference_counter["count"] == 2


# ---------------------------------------------------------
# ALL CARPARK STATUS
# ---------------------------------------------------------

def test_operator_carpark_status(monkeypatch):

    def fake_analyse(carpark):

        return {
            "carpark_id": carpark["carpark_id"],
            "name": carpark["name"],
            "available_parking": 10,
            "occupied_parking": 20,
            "total_parking": 30,
            "occupied_percentage": 0.90,
            "cached": False
        }

    monkeypatch.setattr(
        carpark_service,
        "analyse_carpark",
        fake_analyse
    )

    response = client.get(
        "/api/operator/carpark-status"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "success"

    # Current configuration = 10 carparks
    assert len(data["carpark_status"]) == 10


# ---------------------------------------------------------
# USERS DURING LAST 30 SECONDS
# ---------------------------------------------------------

def test_users_last_30_seconds():

    log_request(
        uuid="user1",
        endpoint="/api/find-carparks",
        requested_n=2
    )

    log_request(
        uuid="user2",
        endpoint="/api/find-carparks",
        requested_n=2
    )

    # duplicate UUID must not increase count
    log_request(
        uuid="user1",
        endpoint="/api/find-carparks",
        requested_n=3
    )

    response = client.get(
        "/api/operator/users-last-30-seconds"
    )

    assert response.status_code == 200

    assert (
        response.json()["user_last_30_seconds"]
        == 2
    )


# ---------------------------------------------------------
# ANNOTATE CARPARK - VALID CARPARK
# ---------------------------------------------------------

def test_annotate_carpark_success(monkeypatch):

    monkeypatch.setattr(
        app_module,
        "take_photo",
        lambda: "./images/fake.jpg"
    )

    monkeypatch.setattr(
        app_module,
        "annotate_parking",
        lambda path: "FAKE_BASE64_IMAGE"
    )

    response = client.get(
        "/api/annotate-carpark",
        params={
            "carpark_id": "CBD_001"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["carpark_id"] == "CBD_001"
    assert data["status"] == "success"
    assert data["image_base64"] == "FAKE_BASE64_IMAGE"


# ---------------------------------------------------------
# ANNOTATE CARPARK - INVALID CARPARK
# ---------------------------------------------------------

def test_annotate_invalid_carpark():

    response = client.get(
        "/api/annotate-carpark",
        params={
            "carpark_id": "DOES_NOT_EXIST"
        }
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Car park not found"
    )


# ---------------------------------------------------------
# DASHBOARD RETURNS PNG
# ---------------------------------------------------------

def test_dashboard(monkeypatch):

    fake_status = [
        {
            "carpark_id": "CBD_001",
            "name": "CBD Car Park 1",
            "available_parking": 20,
            "occupied_parking": 10,
            "total_parking": 30,
            "occupied_percentage": 0.9,
            "cached": False
        }
    ]

    monkeypatch.setattr(
        app_module,
        "get_all_carpark_status",
        lambda: fake_status
    )

    response = client.get(
        "/api/operator/dashboard"
    )

    assert response.status_code == 200

    assert response.headers[
        "content-type"
    ].startswith("image/png")

    assert len(response.content) > 0


# ---------------------------------------------------------
# REQUEST LOGGING
# ---------------------------------------------------------

def test_request_log_created(monkeypatch):

    monkeypatch.setattr(
        app_module,
        "find_best_carparks",
        lambda n: []
    )

    response = client.get(
        "/api/find-carparks",
        params={
            "uuid": "logging-user",
            "n": 1
        }
    )

    assert response.status_code == 200

    assert len(request_logs) == 1

    log = request_logs[0]

    assert log["uuid"] == "logging-user"
    assert log["severity"] == "INFO"
    assert log["service_name"] == "smartpark-api"
    assert log["status"] == "success"


# ---------------------------------------------------------
# STRUCTURED CONSOLE LOGGING
# ---------------------------------------------------------

def test_structured_logging(monkeypatch, caplog):

    monkeypatch.setattr(
        app_module,
        "find_best_carparks",
        lambda n: []
    )

    with caplog.at_level(
        logging.INFO,
        logger="smartpark-api"
    ):

        response = client.get(
            "/api/find-carparks",
            params={
                "uuid": "log-test-user",
                "n": 1
            }
        )

    assert response.status_code == 200

    messages = [
        record.getMessage()
        for record in caplog.records
    ]

    assert any(
        "request_started" in message
        for message in messages
    )

    assert any(
        "request_success" in message
        for message in messages
    )


# ---------------------------------------------------------
# BASIC CONCURRENT REQUEST TEST
# ---------------------------------------------------------

def test_concurrent_requests(monkeypatch):

    def fake_find_best_carparks(n):

        time.sleep(0.1)

        return [
            {
                "carpark_id": "CBD_001",
                "name": "CBD Car Park 1",
                "available_parking": 20,
                "occupied_parking": 10,
                "total_parking": 30,
                "occupied_percentage": 0.9,
                "cached": False
            }
        ]

    monkeypatch.setattr(
        app_module,
        "find_best_carparks",
        fake_find_best_carparks
    )

    def send_request(user_number):

        return client.get(
            "/api/find-carparks",
            params={
                "uuid": f"user{user_number}",
                "n": 1
            }
        )

    with ThreadPoolExecutor(
        max_workers=4
    ) as executor:

        responses = list(
            executor.map(
                send_request,
                range(1, 5)
            )
        )

    assert len(responses) == 4

    for response in responses:
        assert response.status_code == 200

    returned_users = {
        response.json()["uuid"]
        for response in responses
    }

    assert returned_users == {
        "user1",
        "user2",
        "user3",
        "user4"
    }