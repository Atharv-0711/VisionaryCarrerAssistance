import json
import os
import sys
import uuid
from urllib import request, error


def _http_json(method: str, url: str, body=None, headers=None):
    headers = headers or {}
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = request.Request(url=url, method=method, data=data, headers=headers)
    with request.urlopen(req, timeout=20) as response:
        payload = response.read().decode("utf-8")
        return response.status, json.loads(payload) if payload else {}


def main():
    base_url = os.getenv("STAGING_BASE_URL", "").rstrip("/")
    auth_token = os.getenv("STAGING_AUTH_TOKEN", "").strip()

    if not base_url:
        print("STAGING_BASE_URL is required.")
        return 2
    if not auth_token:
        print("STAGING_AUTH_TOKEN is required.")
        return 2

    headers = {"X-Auth-Token": auth_token}
    batch_id = f"smoke-{uuid.uuid4().hex[:12]}"
    ingest_payload = {
        "records": [
            {
                "Name of Child ": "Smoke Test Student",
                "Age": 12,
                "Class (बच्चे की कक्षा)": 6,
                "Background of the Child ": "Urban",
                "Problems in Home ": "None",
                "Behavioral Impact": "Low",
                "Academic Performance ": 78,
                "Family Income ": 21000,
                "Role models": "Teacher",
                "Reason for such role model ": "Support",
            }
        ],
        "batchId": batch_id,
        "schemaVersion": "v1",
        "source": "staging_smoke",
    }

    try:
        ingest_status, ingest_body = _http_json(
            "POST",
            f"{base_url}/api/data-quality/ingest-surveys-batch",
            body=ingest_payload,
            headers=headers,
        )
        if ingest_status != 201 or not ingest_body.get("success"):
            print(f"Ingest failed: status={ingest_status} body={ingest_body}")
            return 1

        monitor_status, monitor_body = _http_json(
            "GET",
            f"{base_url}/api/data-quality/monitoring?page=1&pageSize=20",
            headers=headers,
        )
        if monitor_status != 200:
            print(f"Monitoring read failed: status={monitor_status} body={monitor_body}")
            return 1

        batches = monitor_body.get("batches", [])
        batch_ids = {item.get("batchId") for item in batches}
        if batch_id not in batch_ids:
            print("Ingested batch not visible in monitoring read path.")
            return 1

        detail_status, detail_body = _http_json(
            "GET",
            f"{base_url}/api/data-quality/batches/{batch_id}?page=1&pageSize=10",
            headers=headers,
        )
        if detail_status != 200:
            print(f"Batch detail read failed: status={detail_status} body={detail_body}")
            return 1

        print("Smoke test passed: ingest -> monitoring -> batch details.")
        return 0

    except error.HTTPError as exc:
        body = exc.read().decode("utf-8") if exc.fp else ""
        print(f"HTTPError {exc.code}: {body}")
        return 1
    except Exception as exc:
        print(f"Smoke test execution failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
