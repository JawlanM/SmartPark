import concurrent.futures
import requests


BASE_URL = "http://127.0.0.1:8000"


def test_root():
    response = requests.get(
        f"{BASE_URL}/",
        timeout=10
    )

    assert response.status_code == 200
    assert response.json()["Message"] == "SmartPark API running"


def test_find_carparks_success():
    response = requests.get(
        f"{BASE_URL}/api/find-carparks",
        params={
            "uuid": "docker-test-user",
            "n": 2
        },
        timeout=30
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "success"
    assert data["uuid"] == "docker-test-user"
    assert data["requested_n"] == 2
    assert len(data["results"]) == 2

    for carpark in data["results"]:
        assert "carpark_id" in carpark
        assert "available_parking" in carpark
        assert "occupied_parking" in carpark
        assert "total_parking" in carpark
        assert "cached" in carpark


def test_find_carparks_invalid_zero():
    response = requests.get(
        f"{BASE_URL}/api/find-carparks",
        params={
            "uuid": "docker-test-user",
            "n": 0
        },
        timeout=10
    )

    assert response.status_code == 400


def test_find_carparks_invalid_large_n():
    response = requests.get(
        f"{BASE_URL}/api/find-carparks",
        params={
            "uuid": "docker-test-user",
            "n": 6
        },
        timeout=10
    )

    assert response.status_code == 400


def test_invalid_carpark_annotation():
    response = requests.get(
        f"{BASE_URL}/api/annotate-carpark",
        params={
            "carpark_id": "INVALID"
        },
        timeout=10
    )

    assert response.status_code == 404


def test_valid_carpark_annotation():
    response = requests.get(
        f"{BASE_URL}/api/annotate-carpark",
        params={
            "carpark_id": "CBD_001"
        },
        timeout=30
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "success"
    assert data["carpark_id"] == "CBD_001"
    assert len(data["image_base64"]) > 100


def test_operator_carpark_status():
    response = requests.get(
        f"{BASE_URL}/api/operator/carpark-status",
        timeout=60
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "success"
    assert len(data["carpark_status"]) == 10


def test_users_last_30_seconds():
    requests.get(
        f"{BASE_URL}/api/find-carparks",
        params={
            "uuid": "user-a",
            "n": 1
        },
        timeout=30
    )

    requests.get(
        f"{BASE_URL}/api/find-carparks",
        params={
            "uuid": "user-b",
            "n": 1
        },
        timeout=30
    )

    response = requests.get(
        f"{BASE_URL}/api/operator/users-last-30-seconds",
        timeout=10
    )

    assert response.status_code == 200

    count = response.json()["user_last_30_seconds"]

    assert count >= 2


def test_dashboard():
    response = requests.get(
        f"{BASE_URL}/api/operator/dashboard",
        timeout=60
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/png")
    assert len(response.content) > 100


def test_cache_behavior():
    first = requests.get(
        f"{BASE_URL}/api/find-carparks",
        params={
            "uuid": "cache-user",
            "n": 2
        },
        timeout=30
    )

    second = requests.get(
        f"{BASE_URL}/api/find-carparks",
        params={
            "uuid": "cache-user",
            "n": 2
        },
        timeout=30
    )

    assert first.status_code == 200
    assert second.status_code == 200

    second_results = second.json()["results"]

    assert any(
        carpark["cached"] is True
        for carpark in second_results
    )


def send_concurrent_request(user_id):
    response = requests.get(
        f"{BASE_URL}/api/find-carparks",
        params={
            "uuid": f"concurrent-{user_id}",
            "n": 1
        },
        timeout=60
    )

    return response


def test_concurrent_requests():
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=4
    ) as executor:

        responses = list(
            executor.map(
                send_concurrent_request,
                range(1, 5)
            )
        )

    assert len(responses) == 4

    for response in responses:
        assert response.status_code == 200

    uuids = {
        response.json()["uuid"]
        for response in responses
    }

    assert uuids == {
        "concurrent-1",
        "concurrent-2",
        "concurrent-3",
        "concurrent-4"
    }