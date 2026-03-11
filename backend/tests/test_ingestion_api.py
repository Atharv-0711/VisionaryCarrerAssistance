import pandas as pd


def _sample_record(name_suffix="1"):
    return {
        "Name of Child ": f"Student {name_suffix}",
        "Age": 13,
        "Class (बच्चे की कक्षा)": 7,
        "Background of the Child ": "Urban",
        "Problems in Home ": "None",
        "Behavioral Impact": "Low",
        "Academic Performance ": 82,
        "Family Income ": 18000,
        "Role models": "Doctor",
        "Reason for such role model ": "Service",
        "timestamp": "2026-03-06T12:00:00",
    }


def test_ingest_requires_authentication(client):
    response = client.post(
        "/api/data-quality/ingest-surveys-batch",
        json={"records": [_sample_record()]},
    )
    assert response.status_code == 401


def test_ingest_and_monitoring_pagination_cap(client, auth_token):
    headers = {"X-Auth-Token": auth_token}
    for index in range(3):
        payload = {
            "records": [_sample_record(str(index))],
            "batchId": f"batch-{index}",
            "schemaVersion": "v1",
            "source": "test-suite",
        }
        ingest_response = client.post(
            "/api/data-quality/ingest-surveys-batch",
            headers=headers,
            json=payload,
        )
        assert ingest_response.status_code == 201

    monitoring_response = client.get(
        "/api/data-quality/monitoring?page=1&pageSize=100",
        headers=headers,
    )
    body = monitoring_response.get_json()

    assert monitoring_response.status_code == 200
    assert body["pagination"]["page"] == 1
    assert body["pagination"]["pageSize"] == 2
    assert body["pagination"]["total"] >= 3
    assert len(body["batches"]) <= 2


def test_batch_details_paginated_alerts(client, auth_token):
    headers = {"X-Auth-Token": auth_token}
    ingest_response = client.post(
        "/api/data-quality/ingest-surveys-batch",
        headers=headers,
        json={
            "records": [_sample_record("detail")],
            "batchId": "batch-detail",
            "schemaVersion": "v1",
            "source": "test-suite",
        },
    )
    assert ingest_response.status_code == 201
    batch_id = ingest_response.get_json()["batchId"]

    details_response = client.get(
        f"/api/data-quality/batches/{batch_id}?page=1&pageSize=500",
        headers=headers,
    )
    body = details_response.get_json()

    assert details_response.status_code == 200
    assert body["pagination"]["pageSize"] == 2
    assert "alerts" in body


def test_submit_survey_creates_excel_and_normalizes_assessment_payload(
    client, app_module, auth_token, tmp_path
):
    workbook_path = tmp_path / "Childsurvey.xlsx"
    app_module.SURVEY_EXCEL_PATH = str(workbook_path)
    app_module.data = None
    app_module.survey_processor.process_and_save_survey = lambda payload: {
        "timestamp": "2026-03-06T12:34:56",
        "background": {"analysis": {"average_score": 3.4}},
        "roleModel": {"analysis": {"topTraits": {"Leadership": 1}}},
        "behavioral": {"analysis": {"average_score": 3.1}},
        "income": {"analysis": {"average": 2.9}},
    }

    payload = {
        "Timestamp": "2026-03-06T12:34:56",
        "Name of Child": "Student Submit",
        "Age": 14,
        "Date of Birth": "2012-01-15",
        "Class (बच्चे की कक्षा)": 8,
        "Background of the Child": "Farmer family",
        "Problems in Home": "Financial pressure",
        "Behavioral Impact": "Stress but still motivated",
        "Academic Performance": 78,
        "Family Income": 15000,
        "Role Models": "Teacher",
        "Reason for Such Role Model": "Guides the community",
    }

    response = client.post(
        "/api/submit-survey",
        headers={"X-Auth-Token": auth_token},
        json=payload,
    )
    body = response.get_json()

    assert response.status_code == 200
    assert body["success"] is True
    assert workbook_path.exists()

    workbook_df = pd.read_excel(workbook_path)
    latest_row = workbook_df.iloc[-1].to_dict()
    assert latest_row["Name of Child "] == "Student Submit"
    assert latest_row["Background of the Child "] == "Farmer family"
    assert latest_row["Problems in Home "] == "Financial pressure"
    assert latest_row["Role models"] == "Teacher"
    assert latest_row["Reason for such role model "] == "Guides the community"

    assessment_response = client.get(
        f"/api/assessments/{body['assessmentId']}",
        headers={"X-Auth-Token": auth_token},
    )
    assessment_body = assessment_response.get_json()

    assert assessment_response.status_code == 200
    assert assessment_body["survey_data"]["Background of the Child "] == "Farmer family"
    assert assessment_body["survey_data"]["Problems in Home "] == "Financial pressure"
    assert assessment_body["survey_data"]["Role models"] == "Teacher"
    assert (
        assessment_body["survey_data"]["Reason for such role model "]
        == "Guides the community"
    )
