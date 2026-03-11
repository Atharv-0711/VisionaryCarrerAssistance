import importlib
import sqlite3
import sys
import types
from pathlib import Path

import pandas as pd
import pytest


def _install_stub_modules():
    # Lightweight stubs so CI can run tests without GPU/ML dependencies.
    sys.modules["torch"] = types.ModuleType("torch")

    matplotlib_mod = types.ModuleType("matplotlib")
    matplotlib_mod.use = lambda *_args, **_kwargs: None
    sys.modules["matplotlib"] = matplotlib_mod

    class DummyJsonFormatter:  # pragma: no cover - trivial stub
        def __init__(self, *args, **kwargs):
            pass

    pythonjsonlogger_mod = types.ModuleType("pythonjsonlogger")
    pythonjsonlogger_mod.jsonlogger = types.SimpleNamespace(JsonFormatter=DummyJsonFormatter)
    sys.modules["pythonjsonlogger"] = pythonjsonlogger_mod

    class DummyCelery:
        class Task:
            def __call__(self, *args, **kwargs):
                return self.run(*args, **kwargs)

        def __init__(self, *_args, **_kwargs):
            self.conf = {}

        def task(self, *_args, **_kwargs):
            def decorator(func):
                return func

            return decorator

        def connection(self):
            class Conn:
                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc, tb):
                    return False

                def ensure_connection(self, max_retries=1):
                    return True

            return Conn()

    celery_mod = types.ModuleType("celery")
    celery_mod.Celery = DummyCelery
    sys.modules["celery"] = celery_mod

    class DummyRedisClient:
        def __init__(self):
            self._store = {}

        def get(self, key):
            return self._store.get(key)

        def setex(self, key, _ttl, value):
            self._store[key] = value

        def incr(self, key):
            current = int(self._store.get(key, 0)) + 1
            self._store[key] = current
            return current

        def expire(self, _key, _ttl):
            return True

        def ping(self):
            return True

    class DummyRedis:
        @staticmethod
        def from_url(*_args, **_kwargs):
            return DummyRedisClient()

    redis_mod = types.ModuleType("redis")
    redis_mod.Redis = DummyRedis
    sys.modules["redis"] = redis_mod

    class DummyPsycopgConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def cursor(self):
            class Cursor:
                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc, tb):
                    return False

                def execute(self, *_args, **_kwargs):
                    return None

            return Cursor()

    psycopg_mod = types.ModuleType("psycopg")
    psycopg_mod.connect = lambda *_args, **_kwargs: DummyPsycopgConnection()
    sys.modules["psycopg"] = psycopg_mod

    class DummyTwilioClient:
        def __init__(self, *_args, **_kwargs):
            self.messages = types.SimpleNamespace(create=lambda **_kwargs: None)

    twilio_mod = types.ModuleType("twilio")
    twilio_rest_mod = types.ModuleType("twilio.rest")
    twilio_rest_mod.Client = DummyTwilioClient
    twilio_mod.rest = twilio_rest_mod
    sys.modules["twilio"] = twilio_mod
    sys.modules["twilio.rest"] = twilio_rest_mod

    class DummySocketIO:
        def __init__(self, *_args, **_kwargs):
            pass

        def emit(self, *_args, **_kwargs):
            return None

        def run(self, *_args, **_kwargs):
            return None

    flask_socketio_mod = types.ModuleType("flask_socketio")
    flask_socketio_mod.SocketIO = DummySocketIO
    flask_socketio_mod.emit = lambda *_args, **_kwargs: None
    sys.modules["flask_socketio"] = flask_socketio_mod

    flasgger_mod = types.ModuleType("flasgger")
    flasgger_mod.Swagger = lambda *_args, **_kwargs: None
    sys.modules["flasgger"] = flasgger_mod

    survey_processor_mod = types.ModuleType("survey_processor")
    survey_processor_mod.process_survey = lambda _record: {"score": 0.6}
    survey_processor_mod.generate_combined_dashboard = lambda _analysis: {}
    sys.modules["survey_processor"] = survey_processor_mod

    role_mod = types.ModuleType("sentiment_analysis_rolemodels")
    role_mod.analyze_role_model = lambda _df: {"rolemodel_score": 0.5}
    sys.modules["sentiment_analysis_rolemodels"] = role_mod

    background_mod = types.ModuleType("sentiment_analysis_background")
    background_mod.get_background_sentiment = (
        lambda _df: {"background_score": 0.7, "background_details": [1, 2, 3]}
    )
    sys.modules["sentiment_analysis_background"] = background_mod

    behavioral_mod = types.ModuleType("sentiment_analysis_behavoralimpact")
    behavioral_mod.analyze_behavioral_impact = (
        lambda _df, **_kwargs: {"behavioral_score": 0.65}
    )
    sys.modules["sentiment_analysis_behavoralimpact"] = behavioral_mod

    income_mod = types.ModuleType("sentiment_analysis_family_income")
    income_mod.get_income_sentiment = lambda _df: {"income_score": 0.61}
    sys.modules["sentiment_analysis_family_income"] = income_mod

    home_mod = types.ModuleType("sentiment_analysis_problems_in_home")
    home_mod.analyze_problems_in_home = lambda _df: {"home_score": 0.59}
    sys.modules["sentiment_analysis_problems_in_home"] = home_mod

    vector_store_mod = types.ModuleType("vector_store")

    class DummyPgVectorStore:
        def __init__(self, *_args, **_kwargs):
            pass

        def ensure_schema(self):
            return None

    vector_store_mod.PgVectorStore = DummyPgVectorStore
    sys.modules["vector_store"] = vector_store_mod

    pdf_utils_mod = types.ModuleType("pdf_utils")
    pdf_utils_mod.pdf_bytesio = lambda *_args, **_kwargs: b""
    pdf_utils_mod.generate_pdf_bytes = lambda *_args, **_kwargs: b""
    sys.modules["pdf_utils"] = pdf_utils_mod

    reg_mod = types.ModuleType("hierarchical_regression")
    reg_mod.run_career_confidence_models = lambda _rows: {"models": []}
    sys.modules["hierarchical_regression"] = reg_mod


@pytest.fixture()
def app_module(tmp_path, monkeypatch):
    backend_dir = Path(__file__).resolve().parents[1]
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    _install_stub_modules()
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test_surveys.db"))
    monkeypatch.setenv("ANALYTICS_CACHE_TTL_SECONDS", "300")
    monkeypatch.setenv("ANALYTICS_RATE_LIMIT_REQUESTS", "50")
    monkeypatch.setenv("ANALYTICS_RATE_LIMIT_WINDOW_SECONDS", "60")
    monkeypatch.setenv("ANALYTICS_MAX_PAGE_SIZE", "2")
    monkeypatch.setenv("ANALYTICS_DEFAULT_PAGE_SIZE", "1")
    monkeypatch.setenv("FLASK_DEBUG", "0")

    if "config" in sys.modules:
        del sys.modules["config"]
    if "app" in sys.modules:
        del sys.modules["app"]
    module = importlib.import_module("app")
    module.app.config["TESTING"] = True
    module.data = pd.DataFrame(
        [
            {
                "Name of Child ": "Test Child",
                "Age": 12,
                "Class (बच्चे की कक्षा)": 6,
                "Background of the Child ": "Rural",
                "Problems in Home ": "none",
                "Behavioral Impact": "low",
                "Academic Performance ": 71,
                "Family Income ": 15000,
                "Role models": "Teacher",
                "Reason for such role model ": "Inspiration",
            }
        ]
    )
    return module


@pytest.fixture()
def client(app_module):
    return app_module.app.test_client()


@pytest.fixture()
def auth_token(app_module):
    token = "test-token-school-admin"
    with app_module.get_db_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO users (email, password_hash, role, is_verified, verification_token, created_at, api_token)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "admin@example.com",
                "hashed",
                "school_admin",
                1,
                None,
                "2026-03-06T00:00:00",
                token,
            ),
        )
        conn.commit()
    return token
