def test_analysis_endpoint_uses_cache(client, app_module):
    calls = {"count": 0}

    def counting_background(_df, **_kwargs):
        calls["count"] += 1
        return {"background_score": 0.9, "background_details": ["a", "b"]}

    app_module.background.get_background_sentiment = counting_background

    headers = {"Authorization": "Bearer analytics-cache-test"}
    first = client.get("/api/analysis/background?include_details=false", headers=headers)
    second = client.get("/api/analysis/background?include_details=false", headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.headers.get("X-Cache") == "MISS"
    assert second.headers.get("X-Cache") == "HIT"
    assert calls["count"] == 1


def test_rate_limit_returns_429_with_retry_headers(client):
    from app import settings

    settings.analytics_rate_limit_requests = 2
    settings.analytics_rate_limit_window_seconds = 60
    headers = {"Authorization": "Bearer analytics-rate-limit-test"}
    first = client.get("/api/analysis/income", headers=headers)
    second = client.get("/api/analysis/income", headers=headers)
    third = client.get("/api/analysis/income", headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429
    assert third.headers.get("Retry-After") is not None
    assert third.headers.get("X-RateLimit-Limit") == "2"
    assert third.headers.get("X-RateLimit-Remaining") == "0"


def test_metrics_endpoint_exposes_operational_signals(client):
    response = client.get("/metrics")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "visionary_requests_total" in body
    assert "visionary_request_errors_total" in body


def test_background_analysis_returns_empty_payload_when_data_missing(client, app_module, auth_token):
    app_module.data = None
    app_module._load_from_known_locations = lambda: None
    app_module.load_initial_data = lambda: None

    response = client.get("/api/analysis/background?include_details=true", headers={"X-Auth-Token": auth_token})
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["average_score"] == 0
    assert payload["background_details"] == []
    assert payload["scoring_model"] == "fallback"
    assert payload["error"] == "Data not loaded"
