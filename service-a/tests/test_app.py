from unittest.mock import patch, Mock

import app as app_module


@patch("app.requests.get")
def test_health_endpoint_reports_dependencies(mock_get):
    mock_get.return_value = Mock(status_code=200)

    client = app_module.app.test_client()
    resp = client.get("/health")

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["service"] == "ground-station-api"
    assert body["dependencies"]["telemetry_parser"] == "reachable"
    assert body["dependencies"]["anomaly_detector"] == "reachable"


@patch("app.requests.get", side_effect=Exception("connection refused"))
def test_health_endpoint_reports_unreachable_dependencies(mock_get):
    client = app_module.app.test_client()
    resp = client.get("/health")

    assert resp.status_code == 200
    body = resp.get_json()
    assert "unreachable" in body["dependencies"]["telemetry_parser"]


@patch("app.requests.post")
def test_telemetry_endpoint_accepts_valid_frame(mock_post):
    mock_post.return_value = Mock(status_code=200, json=lambda: {"status": "parsed"})

    client = app_module.app.test_client()
    resp = client.post(
        "/telemetry",
        json={
            "satellite_id": "SAT-001",
            "mission_id": "MISSION-ALPHA-7",
            "timestamp": "2026-06-18T09:30:00Z",
            "telemetry_frame": {"battery_voltage": 14.2},
        },
    )

    assert resp.status_code == 202
    body = resp.get_json()
    assert body["status"] == "accepted"
    assert body["processing_request_id"].startswith("req-")


@patch("app.requests.post", side_effect=app_module.requests.exceptions.RequestException("boom"))
def test_telemetry_endpoint_returns_502_when_parser_unreachable(mock_post):
    client = app_module.app.test_client()
    resp = client.post(
        "/telemetry",
        json={
            "satellite_id": "SAT-001",
            "mission_id": "MISSION-ALPHA-7",
            "telemetry_frame": {},
        },
    )

    assert resp.status_code == 502


def test_telemetry_endpoint_rejects_empty_payload():
    client = app_module.app.test_client()
    resp = client.post("/telemetry", json={})

    assert resp.status_code == 400


def test_callback_endpoint_requires_processing_request_id():
    client = app_module.app.test_client()
    resp = client.post("/callback", json={"satellite_id": "SAT-001"})

    assert resp.status_code == 400


@patch("app.requests.post")
def test_status_endpoint_tracks_request_lifecycle(mock_post):
    mock_post.return_value = Mock(status_code=200, json=lambda: {"status": "parsed"})

    client = app_module.app.test_client()
    telemetry_resp = client.post(
        "/telemetry",
        json={
            "satellite_id": "SAT-001",
            "mission_id": "MISSION-ALPHA-7",
            "telemetry_frame": {"battery_voltage": 14.2},
        },
    )
    request_id = telemetry_resp.get_json()["processing_request_id"]

    status_resp = client.get(f"/status/{request_id}")

    assert status_resp.status_code == 200
    assert status_resp.get_json()["status"] == "awaiting_callback"


def test_status_endpoint_returns_404_for_unknown_request():
    client = app_module.app.test_client()
    resp = client.get("/status/does-not-exist")

    assert resp.status_code == 404