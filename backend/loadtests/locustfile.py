import os
import uuid

from locust import HttpUser, between, task


def _sample_record():
    return {
        "Name of Child ": "Load Test Student",
        "Age": 12,
        "Class (बच्चे की कक्षा)": 6,
        "Background of the Child ": "Urban",
        "Problems in Home ": "None",
        "Behavioral Impact": "Low",
        "Academic Performance ": 75,
        "Family Income ": 16000,
        "Role models": "Teacher",
        "Reason for such role model ": "Guidance",
    }


class AnalyticsUser(HttpUser):
    wait_time = between(0.2, 1.0)
    token = os.getenv("LOADTEST_AUTH_TOKEN", "")

    @property
    def _headers(self):
        headers = {}
        if self.token:
            headers["X-Auth-Token"] = self.token
        return headers

    @task(5)
    def analysis_complete_summary(self):
        self.client.get(
            "/api/analysis/complete-summary",
            headers=self._headers,
            name="/api/analysis/complete-summary",
        )

    @task(4)
    def analysis_background(self):
        self.client.get(
            "/api/analysis/background?include_details=false",
            headers=self._headers,
            name="/api/analysis/background",
        )

    @task(3)
    def monitoring_read(self):
        self.client.get(
            "/api/data-quality/monitoring?page=1&pageSize=25",
            headers=self._headers,
            name="/api/data-quality/monitoring",
        )

    @task(1)
    def ingest_batch(self):
        if not self.token:
            return
        payload = {
            "records": [_sample_record()],
            "batchId": f"load-{uuid.uuid4().hex[:10]}",
            "schemaVersion": "v1",
            "source": "load_test",
        }
        self.client.post(
            "/api/data-quality/ingest-surveys-batch",
            headers=self._headers,
            json=payload,
            name="/api/data-quality/ingest-surveys-batch",
        )
