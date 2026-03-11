import base64
import importlib
import json
import hashlib
import logging
from logging.config import dictConfig
import os
import smtplib
import sqlite3
import sys
import time
import traceback
from datetime import datetime
from email.message import EmailMessage
from io import BytesIO
from uuid import uuid4
from typing import List, Optional, Tuple, Set
from collections import defaultdict
from functools import wraps
from urllib import request as urllib_request
from urllib.error import URLError, HTTPError

from celery import Celery
from flask import Flask, request, jsonify, send_from_directory, send_file, g, make_response
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from flasgger import Swagger
import torch
import pandas as pd
from pythonjsonlogger import jsonlogger
import redis
import psycopg
from twilio.rest import Client
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import HTTPException
import matplotlib

matplotlib.use("Agg")

# Import analysis modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import sentiment_analysis_rolemodels as rolemodels
import sentiment_analysis_background as background
import sentiment_analysis_behavoralimpact as behavioral
import sentiment_analysis_family_income as income
import sentiment_analysis_problems_in_home as home_problems
import survey_processor
from config import settings
from vector_store import PgVectorStore
from pdf_utils import pdf_bytesio, generate_pdf_bytes
from hierarchical_regression import run_career_confidence_models

VALID_ROLES = {"school_admin", "mentor"}

SURVEY_COLUMNS = [
    "Name of Child ",
    "Age",
    "Class (बच्चे की कक्षा)",
    "Background of the Child ",
    "Problems in Home ",
    "Behavioral Impact",
    "Academic Performance ",
    "Family Income ",
    "Role models",
    "Reason for such role model "
]
SURVEY_COLUMN_ALIASES = {
    "Name of Child ": ["Name of Child ", "Name of Child"],
    "Age": ["Age"],
    "Class (बच्चे की कक्षा)": ["Class (बच्चे की कक्षा)"],
    "Background of the Child ": ["Background of the Child ", "Background of the Child"],
    "Problems in Home ": ["Problems in Home ", "Problems in Home"],
    "Behavioral Impact": ["Behavioral Impact"],
    "Academic Performance ": ["Academic Performance ", "Academic Performance"],
    "Family Income ": ["Family Income ", "Family Income"],
    "Role models": ["Role models", "Role Models"],
    "Reason for such role model ": [
        "Reason for such role model ",
        "Reason for such role model",
        "Reason for Such Role Model",
        "Reason for role model ",
    ],
}
SURVEY_EXCEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Childsurvey.xlsx")


def _empty_background_analysis_result(error_message: Optional[str] = None):
    payload = {
        "positive_count": 0,
        "negative_count": 0,
        "neutral_count": 0,
        "average_score": 0,
        "highly_positive": 0,
        "positive": 0,
        "neutral": 0,
        "negative": 0,
        "highly_negative": 0,
        "background_details": [],
        "academic_correlation": 0,
        "training_samples": 0,
        "model_updated": False,
        "scoring_model": "fallback",
    }
    if error_message:
        payload["error"] = error_message
    return payload


def _normalize_background_analysis_result(payload, error_message: Optional[str] = None):
    required_keys = {
        "positive_count",
        "negative_count",
        "neutral_count",
        "average_score",
        "highly_positive",
        "positive",
        "neutral",
        "negative",
        "highly_negative",
    }
    if isinstance(payload, dict) and required_keys.issubset(payload.keys()):
        return payload
    return _empty_background_analysis_result(error_message)


def _run_background_analysis(include_details: bool):
    global background

    last_error = None
    for should_reload in (False, True):
        try:
            if should_reload:
                background = importlib.reload(background)
            results = background.get_background_sentiment(data, persist_artifacts=False)
            normalized = _normalize_background_analysis_result(results)
            if not include_details and "background_details" in normalized:
                del normalized["background_details"]
            return normalized, None
        except Exception as exc:
            last_error = exc
            logger.exception(
                "background_analysis_failed",
                extra={"reloaded_module": should_reload},
            )

    error_message = str(last_error) if last_error else "Background analysis failed"
    return _empty_background_analysis_result(error_message), error_message

vector_store = PgVectorStore(settings.pg_dsn, settings.pg_vector_dim)
_vector_schema_ready = False


# Structured JSON logging
dictConfig(
    {
        "version": 1,
        "formatters": {
            "json": {
                "()": jsonlogger.JsonFormatter,
                "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "level": "INFO",
            }
        },
        "root": {"handlers": ["console"], "level": "INFO"},
    }
)
logger = logging.getLogger(__name__)


def make_celery(flask_app: Flask) -> Celery:
    celery = Celery(
        flask_app.import_name,
        broker=settings.celery_broker_url,
        backend=settings.celery_backend_url,
    )
    celery.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


def get_redis_client() -> redis.Redis:
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)


def get_twilio_client() -> Client:
    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        raise RuntimeError("Twilio credentials are not configured.")
    return Client(settings.twilio_account_sid, settings.twilio_auth_token)


app = Flask(__name__)
app.config["SWAGGER"] = {
    "title": "Visionary Career Assistance API",
    "uiversion": 3,
}
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    supports_credentials=True,
    allow_headers=["Content-Type", "X-Auth-Token", "Authorization"],
)  # Enable CORS for all routes with custom auth header support
socketio = SocketIO(app, cors_allowed_origins="*")
swagger = Swagger(app)
celery_app = make_celery(app)
redis_client = get_redis_client()
_in_memory_cache_store = {}
_in_memory_rate_store = {}
_request_metrics = {
    "total_requests": 0,
    "error_responses": 0,
    "total_latency_ms": 0.0,
    "endpoint_stats": defaultdict(lambda: {"count": 0, "errors": 0, "latency_ms": 0.0}),
}

# Global variable declaration
global data
data = None


def _cache_get(key: str):
    if not settings.analytics_cache_enabled:
        return None

    try:
        raw = redis_client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception:
        # Fallback keeps local/dev behavior predictable when Redis is unavailable.
        entry = _in_memory_cache_store.get(key)
        if not entry:
            return None
        expires_at, payload = entry
        if expires_at <= time.time():
            _in_memory_cache_store.pop(key, None)
            return None
        return payload


def _cache_set(key: str, payload, ttl_seconds: int):
    if not settings.analytics_cache_enabled:
        return

    if ttl_seconds <= 0:
        ttl_seconds = settings.analytics_cache_ttl_seconds

    try:
        redis_client.setex(key, ttl_seconds, json.dumps(payload))
    except Exception:
        _in_memory_cache_store[key] = (time.time() + ttl_seconds, payload)


def _get_cache_version() -> int:
    try:
        raw_version = redis_client.get("analytics:cache:version")
        return int(raw_version or 0)
    except Exception:
        return 0


def _bump_cache_version():
    try:
        redis_client.incr("analytics:cache:version")
    except Exception:
        _in_memory_cache_store.clear()


def _is_valid_analysis_cache_payload(cache_namespace: str, payload) -> bool:
    """
    Guard against serving/storing stale partial analytics payloads.
    """
    if not isinstance(payload, dict):
        return False

    if cache_namespace not in {"analysis_complete", "analysis_complete_summary"}:
        return True

    # If an analysis stage failed earlier, don't keep poisoning cache with that snapshot.
    if payload.get("analysis_errors"):
        return False

    background_payload = payload.get("background")
    if not isinstance(background_payload, dict):
        return False

    # A healthy background payload should contain core counters.
    required_background_keys = {
        "positive_count",
        "negative_count",
        "neutral_count",
        "average_score",
    }
    return required_background_keys.issubset(background_payload.keys())


def cached_json_response(cache_namespace: str, ttl_seconds: Optional[int] = None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            ttl = ttl_seconds or settings.analytics_cache_ttl_seconds
            version = _get_cache_version()
            key_payload = (
                f"{cache_namespace}|v={version}|method={request.method}|path={request.full_path}"
            )
            cache_key = "analytics:cache:" + hashlib.sha256(
                key_payload.encode("utf-8")
            ).hexdigest()

            cached_payload = _cache_get(cache_key)
            if cached_payload is not None and _is_valid_analysis_cache_payload(cache_namespace, cached_payload):
                response = jsonify(cached_payload)
                response.headers["X-Cache"] = "HIT"
                return response

            result = func(*args, **kwargs)
            response = make_response(result)
            if response.status_code == 200 and response.is_json:
                body = response.get_json(silent=True)
                if body is not None and _is_valid_analysis_cache_payload(cache_namespace, body):
                    _cache_set(cache_key, body, ttl)
            response.headers["X-Cache"] = "MISS"
            return response

        return wrapper

    return decorator


def rate_limited(scope: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            limit = max(1, settings.analytics_rate_limit_requests)
            window = max(1, settings.analytics_rate_limit_window_seconds)
            now = int(time.time())
            window_start = now - (now % window)
            window_end = window_start + window
            retry_after = max(1, window_end - now)

            identity = (
                request.headers.get("X-Auth-Token")
                or request.headers.get("Authorization")
                or request.remote_addr
                or "anonymous"
            )
            bucket = f"ratelimit:{scope}:{identity}:{window_start}"

            try:
                current_count = redis_client.incr(bucket)
                if current_count == 1:
                    redis_client.expire(bucket, window + 1)
            except Exception:
                in_memory = _in_memory_rate_store.get(bucket)
                if not in_memory or in_memory["window_end"] <= now:
                    in_memory = {"count": 0, "window_end": window_end}
                in_memory["count"] += 1
                _in_memory_rate_store[bucket] = in_memory
                current_count = in_memory["count"]

            remaining = max(0, limit - current_count)
            rate_headers = {
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(window_end),
            }

            if current_count > limit:
                response = jsonify(
                    {"error": "Rate limit exceeded. Please retry after a short delay."}
                )
                response.status_code = 429
                response.headers["Retry-After"] = str(retry_after)
                for key, value in rate_headers.items():
                    response.headers[key] = value
                return response

            result = func(*args, **kwargs)
            response = make_response(result)
            for key, value in rate_headers.items():
                response.headers[key] = value
            return response

        return wrapper

    return decorator


def parse_pagination_args(
    *,
    default_page_size: Optional[int] = None,
    max_page_size: Optional[int] = None,
) -> Tuple[int, int, int]:
    raw_page = request.args.get("page", "1")
    raw_page_size = request.args.get(
        "pageSize",
        request.args.get(
            "limit",
            str(default_page_size or settings.analytics_default_page_size),
        ),
    )

    try:
        page = int(raw_page)
        page_size = int(raw_page_size)
    except (TypeError, ValueError):
        raise ValueError("Pagination parameters must be integers.")

    if page < 1:
        raise ValueError("page must be >= 1.")
    if page_size < 1:
        raise ValueError("pageSize must be >= 1.")

    page_cap = max_page_size or settings.analytics_max_page_size
    page_size = min(page_size, page_cap)
    offset = (page - 1) * page_size
    return page, page_size, offset


@app.before_request
def track_request_start():
    g.request_started_at = time.perf_counter()
    g.request_id = request.headers.get("X-Request-Id") or uuid4().hex


@app.after_request
def add_request_observability(response):
    started_at = getattr(g, "request_started_at", None)
    latency_ms = 0.0
    if started_at is not None:
        latency_ms = (time.perf_counter() - started_at) * 1000.0

    endpoint_key = request.path
    _request_metrics["total_requests"] += 1
    _request_metrics["total_latency_ms"] += latency_ms
    endpoint_entry = _request_metrics["endpoint_stats"][endpoint_key]
    endpoint_entry["count"] += 1
    endpoint_entry["latency_ms"] += latency_ms

    if response.status_code >= 400:
        _request_metrics["error_responses"] += 1
        endpoint_entry["errors"] += 1

    response.headers["X-Request-Id"] = getattr(g, "request_id", uuid4().hex)
    response.headers["X-Response-Time-Ms"] = f"{latency_ms:.2f}"

    logger.info(
        "request_complete",
        extra={
            "request_id": response.headers["X-Request-Id"],
            "method": request.method,
            "path": request.path,
            "status": response.status_code,
            "latency_ms": round(latency_ms, 2),
        },
    )

    if latency_ms >= settings.monitoring_slow_request_ms:
        logger.warning(
            "slow_request_detected",
            extra={
                "request_id": response.headers["X-Request-Id"],
                "path": request.path,
                "latency_ms": round(latency_ms, 2),
                "threshold_ms": settings.monitoring_slow_request_ms,
            },
        )

    return response


@app.route('/metrics', methods=['GET'])
@app.route('/api/metrics', methods=['GET'])
def metrics():
    total_requests = _request_metrics["total_requests"]
    total_errors = _request_metrics["error_responses"]
    avg_latency = (
        _request_metrics["total_latency_ms"] / total_requests if total_requests else 0.0
    )
    error_ratio = (total_errors / total_requests) if total_requests else 0.0

    lines = [
        "# HELP visionary_requests_total Total API requests",
        "# TYPE visionary_requests_total counter",
        f"visionary_requests_total {total_requests}",
        "# HELP visionary_request_errors_total Total non-2xx responses",
        "# TYPE visionary_request_errors_total counter",
        f"visionary_request_errors_total {total_errors}",
        "# HELP visionary_request_error_ratio Request error ratio",
        "# TYPE visionary_request_error_ratio gauge",
        f"visionary_request_error_ratio {error_ratio:.6f}",
        "# HELP visionary_request_latency_ms_avg Average request latency in ms",
        "# TYPE visionary_request_latency_ms_avg gauge",
        f"visionary_request_latency_ms_avg {avg_latency:.3f}",
    ]

    for endpoint, stats in _request_metrics["endpoint_stats"].items():
        safe_label = endpoint.replace("\\", "_").replace('"', "").replace(" ", "_")
        endpoint_avg = stats["latency_ms"] / stats["count"] if stats["count"] else 0.0
        lines.append(
            f'visionary_endpoint_requests_total{{path="{safe_label}"}} {stats["count"]}'
        )
        lines.append(
            f'visionary_endpoint_request_errors_total{{path="{safe_label}"}} {stats["errors"]}'
        )
        lines.append(
            f'visionary_endpoint_request_latency_ms_avg{{path="{safe_label}"}} {endpoint_avg:.3f}'
        )

    return ("\n".join(lines) + "\n", 200, {"Content-Type": "text/plain; version=0.0.4"})


def get_db_connection():
    """Create a new SQLite connection for the authentication store."""
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_auth_db():
    """Ensure the users table required for authentication exists."""
    try:
        with get_db_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('school_admin', 'mentor')),
                    is_verified INTEGER NOT NULL DEFAULT 0,
                    verification_token TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            try:
                conn.execute(
                    "ALTER TABLE users ADD COLUMN api_token TEXT"
                )
            except sqlite3.OperationalError:
                # Column already exists
                pass
            conn.commit()
    except Exception as exc:
        print(f"Error initializing auth database: {exc}")
        raise


def init_assessments_db():
    """Ensure the assessments table exists for storing survey outcomes."""
    try:
        with get_db_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    school_number TEXT,
                    full_name TEXT NOT NULL,
                    unique_code TEXT NOT NULL UNIQUE,
                    age INTEGER,
                    date_of_birth TEXT,
                    class_level TEXT,
                    guardian_contact TEXT,
                    additional_info TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS assessments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    survey_data TEXT NOT NULL,
                    scores TEXT NOT NULL,
                    recommendations TEXT,
                    career_suggestions TEXT,
                    student_id INTEGER,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE SET NULL
                )
                """
            )
            try:
                conn.execute(
                    "ALTER TABLE assessments ADD COLUMN student_id INTEGER"
                )
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute(
                    "ALTER TABLE students ADD COLUMN school_number TEXT"
                )
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute(
                    "ALTER TABLE students ADD COLUMN date_of_birth TEXT"
                )
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute(
                    """
                    UPDATE students
                    SET school_number = printf('SCH-%04d', user_id)
                    WHERE school_number IS NULL OR TRIM(COALESCE(school_number, '')) = ''
                    """
                )
            except sqlite3.OperationalError:
                pass
            conn.commit()
    except Exception as exc:
        print(f"Error initializing assessments table: {exc}")
        raise


def init_surveys_table():
    """Ensure the surveys table exists for storing raw survey responses."""
    try:
        with get_db_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS surveys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    "Name of Child " TEXT,
                    "Age" REAL,
                    "Class (बच्चे की कक्षा)" REAL,
                    "Background of the Child " TEXT,
                    "Problems in Home " TEXT,
                    "Behavioral Impact" TEXT,
                    "Academic Performance " REAL,
                    "Family Income " REAL,
                    "Role models" TEXT,
                    "Reason for such role model " TEXT,
                    "timestamp" TEXT,
                    unique_hash TEXT UNIQUE,
                    source TEXT DEFAULT 'legacy'
                )
                """
            )
            # Backfill legacy schema columns when running against an older database.
            try:
                conn.execute("ALTER TABLE surveys ADD COLUMN unique_hash TEXT")
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute(
                    "ALTER TABLE surveys ADD COLUMN source TEXT DEFAULT 'legacy'"
                )
            except sqlite3.OperationalError:
                pass

            # Ensure legacy records receive a deterministic unique hash so the
            # uniqueness constraint below can be applied safely.
            placeholder_columns = ",".join(f'"{col}"' for col in SURVEY_COLUMNS)
            legacy_rows = conn.execute(
                f"""
                SELECT rowid AS internal_id, {placeholder_columns}
                FROM surveys
                WHERE unique_hash IS NULL OR TRIM(COALESCE(unique_hash, '')) = ''
                """
            ).fetchall()

            for row in legacy_rows:
                row_payload = {column: row[column] for column in SURVEY_COLUMNS}
                survey_hash = compute_survey_row_hash(row_payload)
                conn.execute(
                    """
                    UPDATE surveys
                    SET unique_hash = ?, source = COALESCE(source, 'legacy')
                    WHERE rowid = ?
                    """,
                    (survey_hash, row["internal_id"]),
                )

            # Remove any duplicate legacy records that would violate the unique index.
            duplicate_hashes = conn.execute(
                """
                SELECT unique_hash
                FROM surveys
                WHERE unique_hash IS NOT NULL AND TRIM(unique_hash) <> ''
                GROUP BY unique_hash
                HAVING COUNT(*) > 1
                """
            ).fetchall()

            for duplicate in duplicate_hashes:
                hash_value = duplicate["unique_hash"]
                duplicate_rows = conn.execute(
                    """
                    SELECT rowid AS internal_id
                    FROM surveys
                    WHERE unique_hash = ?
                    ORDER BY rowid
                    """,
                    (hash_value,),
                ).fetchall()
                # Keep the earliest record, remove the rest.
                if len(duplicate_rows) > 1:
                    for row in duplicate_rows[1:]:
                        conn.execute(
                            "DELETE FROM surveys WHERE rowid = ?", (row["internal_id"],)
                        )

            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_surveys_hash ON surveys(unique_hash)"
            )
            conn.commit()
    except Exception as exc:
        print(f"Error initializing surveys table: {exc}")
        raise


def _normalize_survey_value(value):
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass

    if isinstance(value, str):
        trimmed = value.strip()
        return trimmed if trimmed else None
    return value


def _extract_survey_value(payload: dict, canonical_column: str):
    for key in SURVEY_COLUMN_ALIASES.get(canonical_column, [canonical_column]):
        if key in payload:
            return _normalize_survey_value(payload.get(key))
    return None


def _lookup_payload_value(row_payload: dict, column_name: str):
    if column_name in row_payload:
        return row_payload.get(column_name)
    normalized_target = str(column_name).strip().lower()
    for key, value in row_payload.items():
        if str(key).strip().lower() == normalized_target:
            return value
    return None


def normalize_submission_payload(
    payload: dict, *, fallback_timestamp: Optional[str] = None
):
    normalized_payload = {
        column: _extract_survey_value(payload, column) for column in SURVEY_COLUMNS
    }
    normalized_payload["Date of Birth"] = _normalize_survey_value(
        payload.get("Date of Birth") or payload.get("Date of birth")
    )
    normalized_payload["Timestamp"] = _normalize_survey_value(
        payload.get("Timestamp")
        or payload.get("timestamp")
        or payload.get("created_at")
        or fallback_timestamp
    )
    return normalized_payload


def compute_survey_row_hash(row: dict) -> str:
    serializable = {column: row.get(column) for column in SURVEY_COLUMNS}
    payload = json.dumps(serializable, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def seed_surveys_from_dataframe(df: Optional[pd.DataFrame]):
    """Populate the surveys table with surveys sourced from the legacy Excel file."""
    if df is None or df.empty:
        return

    records = df.to_dict("records")
    inserted = 0

    try:
        with get_db_connection() as conn:
            for record in records:
                normalized_row = {
                    column: _normalize_survey_value(record.get(column))
                    for column in SURVEY_COLUMNS
                }
                survey_hash = compute_survey_row_hash(normalized_row)
                timestamp_value = (
                    _normalize_survey_value(record.get("timestamp"))
                    or datetime.utcnow().isoformat()
                )

                placeholders = ",".join(["?"] * (len(SURVEY_COLUMNS) + 3))
                columns_sql = ",".join(f'"{col}"' for col in SURVEY_COLUMNS)

                cursor = conn.execute(
                    f"""
                    INSERT OR IGNORE INTO surveys ({columns_sql}, "timestamp", unique_hash, source)
                    VALUES ({placeholders})
                    """,
                    [
                        *(normalized_row.get(col) for col in SURVEY_COLUMNS),
                        timestamp_value,
                        survey_hash,
                        "legacy",
                    ],
                )
                inserted += cursor.rowcount or 0

            conn.commit()
            if inserted:
                print(f"Seeded {inserted} survey records into SQLite.")
    except sqlite3.Error as exc:
        print(f"Error seeding surveys: {exc}")
    except Exception as exc:
        print(f"Unexpected error while seeding surveys: {exc}")


DATA_QUALITY_NUMERIC_COLUMNS = {
    "Age": {"min": 3, "max": 25},
    "Class (बच्चे की कक्षा)": {"min": 1, "max": 16},
    "Academic Performance ": {"min": 0, "max": 100},
    "Family Income ": {"min": 0, "max": 1_000_000},
}


def init_data_quality_tables():
    """Create tables for data quality monitoring and alerting."""
    try:
        with get_db_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS data_quality_batches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id TEXT UNIQUE NOT NULL,
                    schema_version TEXT NOT NULL,
                    source TEXT NOT NULL,
                    ingested_at TEXT NOT NULL,
                    total_rows INTEGER NOT NULL,
                    inserted_rows INTEGER NOT NULL,
                    duplicate_rows INTEGER NOT NULL,
                    outlier_rows INTEGER NOT NULL,
                    completeness_score REAL NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS data_quality_field_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id TEXT NOT NULL,
                    field_name TEXT NOT NULL,
                    total_count INTEGER NOT NULL,
                    missing_count INTEGER NOT NULL,
                    completeness_ratio REAL NOT NULL,
                    outlier_count INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY(batch_id) REFERENCES data_quality_batches(batch_id) ON DELETE CASCADE
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS data_quality_alert_config (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    completeness_min REAL NOT NULL,
                    duplicates_max INTEGER NOT NULL,
                    outliers_max INTEGER NOT NULL,
                    email_recipients TEXT,
                    webhook_urls TEXT,
                    slack_webhook_url TEXT,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS data_quality_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    threshold_value REAL NOT NULL,
                    comparator TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    channels TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(batch_id) REFERENCES data_quality_batches(batch_id) ON DELETE CASCADE
                )
                """
            )

            default_config = (
                1,
                settings.dq_threshold_completeness_min,
                settings.dq_threshold_duplicates_max,
                settings.dq_threshold_outliers_max,
                json.dumps(settings.dq_alert_email_to),
                json.dumps(settings.dq_alert_webhook_urls),
                settings.dq_alert_slack_webhook,
                datetime.utcnow().isoformat(),
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO data_quality_alert_config (
                    id,
                    completeness_min,
                    duplicates_max,
                    outliers_max,
                    email_recipients,
                    webhook_urls,
                    slack_webhook_url,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                default_config,
            )

            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_data_quality_batches_ingested_at ON data_quality_batches(ingested_at)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_data_quality_alerts_batch_id ON data_quality_alerts(batch_id)"
            )
            conn.commit()
    except Exception as exc:
        print(f"Error initializing data quality tables: {exc}")
        raise


def _safe_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _calculate_outlier_counts(normalized_rows: List[dict]):
    field_outlier_counts = {field: 0 for field in DATA_QUALITY_NUMERIC_COLUMNS.keys()}
    row_outlier_count = 0

    if not normalized_rows:
        return row_outlier_count, field_outlier_counts

    value_buckets = {field: [] for field in DATA_QUALITY_NUMERIC_COLUMNS.keys()}
    row_numeric_values = []

    for row in normalized_rows:
        numeric_snapshot = {}
        for field in DATA_QUALITY_NUMERIC_COLUMNS.keys():
            parsed = _safe_float(row.get(field))
            numeric_snapshot[field] = parsed
            if parsed is not None:
                value_buckets[field].append(parsed)
        row_numeric_values.append(numeric_snapshot)

    iqr_bounds = {}
    for field, values in value_buckets.items():
        if len(values) >= 4:
            series = pd.Series(values, dtype=float)
            q1 = float(series.quantile(0.25))
            q3 = float(series.quantile(0.75))
            iqr = q3 - q1
            iqr_bounds[field] = (q1 - 1.5 * iqr, q3 + 1.5 * iqr)

    for numeric_snapshot in row_numeric_values:
        row_has_outlier = False
        for field, limits in DATA_QUALITY_NUMERIC_COLUMNS.items():
            value = numeric_snapshot.get(field)
            if value is None:
                continue

            static_outlier = value < limits["min"] or value > limits["max"]
            iqr_outlier = False
            if field in iqr_bounds:
                lower, upper = iqr_bounds[field]
                iqr_outlier = value < lower or value > upper

            if static_outlier or iqr_outlier:
                field_outlier_counts[field] += 1
                row_has_outlier = True

        if row_has_outlier:
            row_outlier_count += 1

    return row_outlier_count, field_outlier_counts


def compute_batch_quality_metrics(normalized_rows: List[dict], inserted_rows: int):
    total_rows = len(normalized_rows)
    total_cells = total_rows * len(SURVEY_COLUMNS)
    missing_cells = 0
    field_metrics = []

    outlier_rows, field_outlier_counts = _calculate_outlier_counts(normalized_rows)

    for field in SURVEY_COLUMNS:
        missing_count = 0
        for row in normalized_rows:
            if _normalize_survey_value(row.get(field)) is None:
                missing_count += 1
        missing_cells += missing_count
        total_count = total_rows
        completeness_ratio = (
            (total_count - missing_count) / total_count if total_count else 1.0
        )
        field_metrics.append(
            {
                "field_name": field,
                "total_count": total_count,
                "missing_count": missing_count,
                "completeness_ratio": round(completeness_ratio, 4),
                "outlier_count": int(field_outlier_counts.get(field, 0)),
            }
        )

    completeness_score = (
        (total_cells - missing_cells) / total_cells if total_cells else 1.0
    )
    duplicate_rows = max(total_rows - inserted_rows, 0)

    return {
        "total_rows": total_rows,
        "inserted_rows": inserted_rows,
        "duplicate_rows": duplicate_rows,
        "outlier_rows": outlier_rows,
        "completeness_score": round(completeness_score, 4),
        "field_metrics": field_metrics,
    }


def get_data_quality_alert_config(conn: sqlite3.Connection):
    row = conn.execute(
        """
        SELECT
            completeness_min,
            duplicates_max,
            outliers_max,
            email_recipients,
            webhook_urls,
            slack_webhook_url,
            updated_at
        FROM data_quality_alert_config
        WHERE id = 1
        """
    ).fetchone()

    if row is None:
        return {
            "completeness_min": settings.dq_threshold_completeness_min,
            "duplicates_max": settings.dq_threshold_duplicates_max,
            "outliers_max": settings.dq_threshold_outliers_max,
            "email_recipients": settings.dq_alert_email_to,
            "webhook_urls": settings.dq_alert_webhook_urls,
            "slack_webhook_url": settings.dq_alert_slack_webhook,
            "updated_at": None,
        }

    return {
        "completeness_min": float(row["completeness_min"]),
        "duplicates_max": int(row["duplicates_max"]),
        "outliers_max": int(row["outliers_max"]),
        "email_recipients": _parse_json_column(row["email_recipients"]) or [],
        "webhook_urls": _parse_json_column(row["webhook_urls"]) or [],
        "slack_webhook_url": row["slack_webhook_url"],
        "updated_at": row["updated_at"],
    }


def save_data_quality_batch(
    conn: sqlite3.Connection,
    batch_id: str,
    schema_version: str,
    source: str,
    ingested_at: str,
    metrics: dict,
):
    conn.execute(
        """
        INSERT INTO data_quality_batches (
            batch_id,
            schema_version,
            source,
            ingested_at,
            total_rows,
            inserted_rows,
            duplicate_rows,
            outlier_rows,
            completeness_score,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            batch_id,
            schema_version,
            source,
            ingested_at,
            metrics["total_rows"],
            metrics["inserted_rows"],
            metrics["duplicate_rows"],
            metrics["outlier_rows"],
            metrics["completeness_score"],
            datetime.utcnow().isoformat(),
        ),
    )

    for item in metrics["field_metrics"]:
        conn.execute(
            """
            INSERT INTO data_quality_field_metrics (
                batch_id,
                field_name,
                total_count,
                missing_count,
                completeness_ratio,
                outlier_count
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                batch_id,
                item["field_name"],
                item["total_count"],
                item["missing_count"],
                item["completeness_ratio"],
                item["outlier_count"],
            ),
        )


def backfill_data_quality_from_surveys():
    """
    Create an initial data-quality batch from existing surveys when no batch
    records are present yet.
    """
    try:
        with get_db_connection() as conn:
            existing_batches = conn.execute(
                "SELECT COUNT(*) AS total FROM data_quality_batches"
            ).fetchone()
            if existing_batches and int(existing_batches["total"]) > 0:
                return

            columns_sql = ",".join(f'"{column}"' for column in SURVEY_COLUMNS)
            survey_rows = conn.execute(
                f"""
                SELECT {columns_sql}, "timestamp"
                FROM surveys
                ORDER BY rowid
                """
            ).fetchall()
            if not survey_rows:
                return

            normalized_rows = []
            latest_timestamp = datetime.utcnow().isoformat()
            for row in survey_rows:
                normalized_rows.append(
                    {
                        column: _normalize_survey_value(row[column])
                        for column in SURVEY_COLUMNS
                    }
                )
                row_timestamp = _normalize_survey_value(row["timestamp"])
                if row_timestamp:
                    latest_timestamp = str(row_timestamp)

            metrics = compute_batch_quality_metrics(
                normalized_rows=normalized_rows,
                inserted_rows=len(normalized_rows),
            )
            save_data_quality_batch(
                conn=conn,
                batch_id="legacy_backfill_initial",
                schema_version=settings.data_quality_default_schema_version or "v1",
                source="legacy_backfill",
                ingested_at=latest_timestamp,
                metrics=metrics,
            )
            conn.commit()
            print(
                f"Backfilled data quality metrics for {len(normalized_rows)} existing surveys."
            )
    except Exception as exc:
        print(f"Error backfilling data quality data: {exc}")


def evaluate_data_quality_alerts(metrics: dict, config: dict):
    fired = []

    if metrics["completeness_score"] < config["completeness_min"]:
        fired.append(
            {
                "metric_name": "completeness_score",
                "metric_value": metrics["completeness_score"],
                "threshold_value": config["completeness_min"],
                "comparator": "<",
                "severity": "high",
                "message": (
                    f"Completeness dropped to {metrics['completeness_score']:.2%} "
                    f"(threshold: {config['completeness_min']:.2%})."
                ),
            }
        )

    if metrics["duplicate_rows"] > config["duplicates_max"]:
        fired.append(
            {
                "metric_name": "duplicate_rows",
                "metric_value": float(metrics["duplicate_rows"]),
                "threshold_value": float(config["duplicates_max"]),
                "comparator": ">",
                "severity": "medium",
                "message": (
                    f"Duplicate rows reached {metrics['duplicate_rows']} "
                    f"(threshold: {config['duplicates_max']})."
                ),
            }
        )

    if metrics["outlier_rows"] > config["outliers_max"]:
        fired.append(
            {
                "metric_name": "outlier_rows",
                "metric_value": float(metrics["outlier_rows"]),
                "threshold_value": float(config["outliers_max"]),
                "comparator": ">",
                "severity": "medium",
                "message": (
                    f"Outlier rows reached {metrics['outlier_rows']} "
                    f"(threshold: {config['outliers_max']})."
                ),
            }
        )

    return fired


def _post_json(url: str, payload: dict):
    if not url:
        return False, "Missing URL."
    body = json.dumps(payload).encode("utf-8")
    req = urllib_request.Request(
        url=url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib_request.urlopen(req, timeout=8) as response:
            code = response.getcode()
        if 200 <= code < 300:
            return True, None
        return False, f"Unexpected status code: {code}"
    except (HTTPError, URLError, TimeoutError) as exc:
        return False, str(exc)
    except Exception as exc:
        return False, str(exc)


def dispatch_data_quality_alerts(batch_id: str, alerts: List[dict], config: dict):
    if not alerts:
        return {"email": [], "webhook": [], "slack": []}

    batch_link = f"{settings.frontend_base_url.rstrip('/')}/monitoring?batchId={batch_id}"
    alert_lines = "\n".join(f"- {item['message']}" for item in alerts)
    plain_message = (
        f"Data quality alert for batch {batch_id}\n"
        f"Review batch: {batch_link}\n\n"
        f"{alert_lines}"
    )

    delivery = {"email": [], "webhook": [], "slack": []}

    for email in config.get("email_recipients", []):
        success, error = send_generic_email(
            email,
            f"Data Quality Alert - Batch {batch_id}",
            plain_message,
        )
        delivery["email"].append(
            {"target": email, "success": bool(success), "error": error}
        )

    webhook_payload = {
        "event": "data_quality_alert",
        "batchId": batch_id,
        "batchUrl": batch_link,
        "alerts": alerts,
    }
    for url in config.get("webhook_urls", []):
        success, error = _post_json(url, webhook_payload)
        delivery["webhook"].append(
            {"target": url, "success": bool(success), "error": error}
        )

    slack_url = config.get("slack_webhook_url")
    if slack_url:
        success, error = _post_json(
            slack_url,
            {
                "text": (
                    f":warning: Data quality threshold breached for batch `{batch_id}`.\n"
                    f"{alert_lines}\n"
                    f"Review: {batch_link}"
                )
            },
        )
        delivery["slack"].append(
            {"target": slack_url, "success": bool(success), "error": error}
        )

    return delivery


def persist_data_quality_alerts(
    conn: sqlite3.Connection,
    batch_id: str,
    alerts: List[dict],
    channels: dict,
):
    serialized_channels = json.dumps(channels)
    now = datetime.utcnow().isoformat()
    for item in alerts:
        conn.execute(
            """
            INSERT INTO data_quality_alerts (
                batch_id,
                metric_name,
                metric_value,
                threshold_value,
                comparator,
                severity,
                message,
                channels,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                batch_id,
                item["metric_name"],
                item["metric_value"],
                item["threshold_value"],
                item["comparator"],
                item["severity"],
                item["message"],
                serialized_channels,
                now,
            ),
        )


def send_verification_email(
    recipient_email: str, verification_token: str
) -> Tuple[bool, str, Optional[str]]:
    """Send the account verification email to the user.

    Returns:
        tuple[bool, str, str | None]: A tuple containing:
            - success flag
            - verification link
            - optional error message when delivery fails
    """
    if not recipient_email:
        raise ValueError("Recipient email is required.")

    verification_link = (
        f"{settings.frontend_base_url.rstrip('/')}/verify?token={verification_token}"
    )

    subject = "Verify your Visionary Career Assistance account"
    body = (
        "Hello,\n\n"
        "Thank you for registering with Visionary Career Assistance. "
        "Please verify your email address to activate your account.\n\n"
        f"Verification link: {verification_link}\n\n"
        "If you did not create this account, you can safely ignore this email.\n\n"
        "Best regards,\n"
        "Visionary Career Assistance Team"
    )

    if not settings.smtp_server or not settings.smtp_username or not settings.smtp_password:
        print(
            "[Auth] SMTP settings are not fully configured. "
            f"Use this token to verify manually: {verification_token}"
        )
        return (
            False,
            verification_link,
            "SMTP configuration is missing; email delivery skipped.",
        )

    sender = settings.default_sender or settings.smtp_username
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient_email
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_username and settings.smtp_password:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)
    except Exception as exc:
        print(f"Failed to send verification email: {exc}")
        return (
            False,
            verification_link,
            f"Email delivery failed: {exc}",
        )

    return True, verification_link, None


def send_generic_email(recipient_email: str, subject: str, body: str) -> Tuple[bool, Optional[str]]:
    """Send a simple text email; returns success flag and optional error."""
    if not recipient_email:
        return False, "Recipient email is required."

    sender = settings.default_sender or settings.smtp_username
    if not sender:
        return False, "SMTP sender not configured."

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient_email
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_username and settings.smtp_password:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)
        return True, None
    except Exception as exc:
        logger.error("email_send_failed", extra={"error": str(exc)})
        return False, str(exc)


def send_sms_message(to_number: str, body: str) -> Tuple[bool, Optional[str]]:
    """Send SMS via Twilio when configured."""
    if not to_number:
        return False, "Destination number is required."
    if not settings.twilio_from_number:
        return False, "Twilio from number not configured."
    try:
        client = get_twilio_client()
        client.messages.create(
            to=to_number,
            from_=settings.twilio_from_number,
            body=body,
        )
        return True, None
    except Exception as exc:
        logger.error("sms_send_failed", extra={"error": str(exc)})
        return False, str(exc)


def generate_api_token() -> str:
    return uuid4().hex


def generate_student_code() -> str:
    return uuid4().hex[:8].upper()


def generate_school_number(user_id: int) -> str:
    return f"SCH-{int(user_id):04d}"


def require_role(user: sqlite3.Row, allowed_roles: Set[str]) -> Optional[Tuple[dict, int]]:
    if user["role"] not in allowed_roles:
        return {"error": "Forbidden."}, 403
    return None


def get_user_by_token(token: str) -> Optional[sqlite3.Row]:
    if not token:
        return None
    with get_db_connection() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE api_token = ?",
            (token,),
        ).fetchone()


def authenticate_request() -> Tuple[Optional[sqlite3.Row], Optional[Tuple[dict, int]]]:
    token = request.headers.get("X-Auth-Token")
    if not token:
        return None, ({"error": "Authentication token missing."}, 401)

    user = get_user_by_token(token)
    if user is None:
        return None, ({"error": "Invalid or expired session token."}, 401)

    if not user["is_verified"]:
        return None, ({"error": "Account not verified."}, 403)

    return user, None


def _get_vector_store():
    """Get initialized pgvector store or raise helpful error."""
    global _vector_schema_ready
    if not settings.pg_dsn:
        raise RuntimeError("PG_DSN is not configured; vector features are disabled.")

    if not _vector_schema_ready:
        vector_store.ensure_schema()
        _vector_schema_ready = True
    return vector_store


def _coerce_embedding(raw_value, *, field: str, expected_dim: int) -> List[float]:
    if raw_value is None:
        raise ValueError(f"'{field}' is required.")
    if not isinstance(raw_value, (list, tuple)):
        raise ValueError(f"'{field}' must be a list of numbers.")

    try:
        embedding = [float(x) for x in raw_value]
    except (TypeError, ValueError):
        raise ValueError(f"'{field}' must contain only numbers.")

    if len(embedding) != expected_dim:
        raise ValueError(
            f"'{field}' length is {len(embedding)} but expected {expected_dim}."
        )
    return embedding


def _coerce_dict(raw_value, *, field: str) -> Optional[dict]:
    if raw_value is None:
        return None
    if not isinstance(raw_value, dict):
        raise ValueError(f"'{field}' must be an object.")
    return raw_value


@celery_app.task(name="tasks.send_email")
def send_email_task(recipient_email: str, subject: str, body: str):
    success, error = send_generic_email(recipient_email, subject, body)
    return {"success": success, "error": error}


@celery_app.task(name="tasks.send_sms")
def send_sms_task(to_number: str, body: str):
    success, error = send_sms_message(to_number, body)
    return {"success": success, "error": error}


@celery_app.task(name="tasks.generate_pdf")
def generate_pdf_task(title: str, sections: Optional[List[dict]] = None):
    pdf_bytes = generate_pdf_bytes(title, sections)
    return {
        "success": True,
        "pdf_base64": base64.b64encode(pdf_bytes).decode("utf-8"),
    }


@app.errorhandler(HTTPException)
def handle_http_exception(exc: HTTPException):
    response = exc.get_response()
    payload = {"error": exc.description or exc.name, "status": exc.code}
    logger.warning("http_error", extra={"status": exc.code, "error": exc.description})
    response.data = json.dumps(payload)
    response.content_type = "application/json"
    return response


@app.errorhandler(Exception)
def handle_generic_exception(exc: Exception):
    logger.exception("unhandled_exception")
    return jsonify({"error": "Internal server error"}), 500


def serialize_student(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "school_number": row["school_number"],
        "full_name": row["full_name"],
        "unique_code": row["unique_code"],
        "age": row["age"],
        "date_of_birth": row["date_of_birth"],
        "class_level": row["class_level"],
        "guardian_contact": row["guardian_contact"],
        "additional_info": row["additional_info"],
        "created_at": row["created_at"],
    }


def get_student_for_user(student_id: int, user_id: int) -> Optional[sqlite3.Row]:
    with get_db_connection() as conn:
        return conn.execute(
            "SELECT * FROM students WHERE id = ? AND user_id = ?",
            (student_id, user_id),
        ).fetchone()


def normalize_date_of_birth(date_value) -> Optional[str]:
    normalized_value = _normalize_survey_value(date_value)
    if not normalized_value:
        return None

    try:
        return datetime.strptime(normalized_value, "%Y-%m-%d").date().isoformat()
    except (TypeError, ValueError):
        raise ValueError("Date of Birth must be in YYYY-MM-DD format.")


def ingest_survey_batch_records(
    records: List[dict],
    schema_version: Optional[str] = None,
    source: str = "api_batch",
    batch_id: Optional[str] = None,
):
    if not isinstance(records, list) or not records:
        raise ValueError("Records must be a non-empty array.")

    normalized_rows = []
    inserted_rows = 0
    batch_identifier = str(batch_id).strip() if batch_id is not None else ""
    if not batch_identifier:
        batch_identifier = f"batch_{uuid4().hex[:12]}"
    schema = (
        schema_version
        or settings.data_quality_default_schema_version
        or "v1"
    )
    ingested_at = datetime.utcnow().isoformat()
    columns_sql = ",".join(f'"{col}"' for col in SURVEY_COLUMNS)
    placeholders = ",".join(["?"] * (len(SURVEY_COLUMNS) + 3))

    with get_db_connection() as conn:
        for record in records:
            if not isinstance(record, dict):
                raise ValueError("Each record must be an object.")

            normalized_row = {
                column: _normalize_survey_value(record.get(column))
                for column in SURVEY_COLUMNS
            }
            normalized_rows.append(normalized_row)
            survey_hash = compute_survey_row_hash(normalized_row)
            timestamp_value = (
                _normalize_survey_value(record.get("timestamp")) or ingested_at
            )

            cursor = conn.execute(
                f"""
                INSERT OR IGNORE INTO surveys ({columns_sql}, "timestamp", unique_hash, source)
                VALUES ({placeholders})
                """,
                [
                    *(normalized_row.get(col) for col in SURVEY_COLUMNS),
                    timestamp_value,
                    survey_hash,
                    f"batch:{batch_identifier}:{source}",
                ],
            )
            inserted_rows += cursor.rowcount or 0

        metrics = compute_batch_quality_metrics(normalized_rows, inserted_rows)
        config = get_data_quality_alert_config(conn)
        save_data_quality_batch(
            conn=conn,
            batch_id=batch_identifier,
            schema_version=schema,
            source=source,
            ingested_at=ingested_at,
            metrics=metrics,
        )
        alerts = evaluate_data_quality_alerts(metrics, config)
        conn.commit()

    delivery = dispatch_data_quality_alerts(batch_identifier, alerts, config)

    if alerts:
        with get_db_connection() as conn:
            persist_data_quality_alerts(
                conn=conn,
                batch_id=batch_identifier,
                alerts=alerts,
                channels=delivery,
            )
            conn.commit()

    return {
        "batchId": batch_identifier,
        "schemaVersion": schema,
        "source": source,
        "ingestedAt": ingested_at,
        "metrics": metrics,
        "alerts": alerts,
        "alertDelivery": delivery,
    }


def _candidate_paths(filename: str):
    if filename.lower() == "childsurvey.xlsx":
        return [SURVEY_EXCEL_PATH]
    app_dir = os.path.dirname(os.path.abspath(__file__))
    return [os.path.join(app_dir, filename)]


def _load_from_known_locations():
    """Load survey data from Excel from likely backend/runtime paths."""
    excel_candidates = _candidate_paths('Childsurvey.xlsx')

    for path in excel_candidates:
        if os.path.exists(path):
            try:
                df = pd.read_excel(path, sheet_name=0)
                print(f"Data loaded from Excel: {path} with {len(df)} records")
                return df
            except Exception as e:
                print(f"Failed reading Excel at {path}: {e}")

    return None


def append_submission_to_excel(submission: dict, created_at: Optional[str] = None):
    """
    Mirror a submitted survey row into backend/Childsurvey.xlsx.
    Keeps existing columns intact and appends missing columns when needed.
    """
    excel_path = SURVEY_EXCEL_PATH
    row_timestamp = created_at or datetime.utcnow().isoformat()

    row_payload = {
        column: _extract_survey_value(submission, column) for column in SURVEY_COLUMNS
    }
    row_payload["Timestamp"] = _normalize_survey_value(
        submission.get("Timestamp") or submission.get("timestamp") or row_timestamp
    )
    row_payload["Date of Birth"] = _normalize_survey_value(
        submission.get("Date of Birth") or submission.get("Date of birth")
    )
    row_payload["timestamp"] = row_timestamp

    preferred_columns = ["Timestamp", *SURVEY_COLUMNS, "Date of Birth", "timestamp"]
    if os.path.exists(excel_path):
        existing_df = pd.read_excel(excel_path, sheet_name=0)
    else:
        existing_df = pd.DataFrame(columns=preferred_columns)

    for column in row_payload.keys():
        if column not in existing_df.columns:
            existing_df[column] = None

    ordered_columns = list(existing_df.columns)
    if "timestamp" not in ordered_columns:
        ordered_columns.append("timestamp")

    append_df = pd.DataFrame(
        [{column: _lookup_payload_value(row_payload, column) for column in ordered_columns}]
    )
    updated_df = pd.concat([existing_df, append_df], ignore_index=True)
    updated_df.to_excel(excel_path, index=False)


def load_initial_data():
    global data
    data = _load_from_known_locations()
    if data is None:
        print("No initial data loaded. Place Childsurvey.xlsx in the backend directory.")

# Load data once at startup
load_initial_data()
init_surveys_table()
seed_surveys_from_dataframe(data)
init_auth_db()
init_assessments_db()
init_data_quality_tables()
backfill_data_quality_from_surveys()


def readiness_report():
    checks = {}
    overall = True

    try:
        with get_db_connection() as conn:
            conn.execute("SELECT 1")
        checks["sqlite"] = "ok"
    except Exception as exc:
        checks["sqlite"] = f"error: {exc}"
        overall = False

    try:
        redis_client.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error: {exc}"
        overall = False

    try:
        with celery_app.connection() as conn:
            conn.ensure_connection(max_retries=1)
        checks["celery_broker"] = "ok"
    except Exception as exc:
        checks["celery_broker"] = f"error: {exc}"
        overall = False

    if settings.pg_dsn:
        try:
            with psycopg.connect(settings.pg_dsn) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
            checks["pgvector"] = "ok"
        except Exception as exc:
            checks["pgvector"] = f"error: {exc}"
            overall = False

    return overall, checks

@app.route('/health', methods=['GET'])
@app.route('/api/health', methods=['GET'])
def health_check():
    ok = data is not None
    return jsonify({"status": "ok" if ok else "not_ready", "data_loaded": ok})


@app.route('/ready', methods=['GET'])
def readiness_check():
    ok, checks = readiness_report()
    return (
        jsonify(
            {
                "status": "ready" if ok else "degraded",
                "checks": checks,
            }
        ),
        200 if ok else 503,
    )


@app.route('/api/auth/signup', methods=['POST'])
def signup():
    payload = request.json or {}
    email = (payload.get('email') or '').strip().lower()
    password = payload.get('password') or ''
    role = payload.get('role')

    if not email or not password or not role:
        return jsonify({"error": "Email, password, and role are required."}), 400

    if role not in VALID_ROLES:
        return jsonify({"error": "Invalid role supplied."}), 400

    verification_token = uuid4().hex

    try:
        with get_db_connection() as conn:
            existing = conn.execute(
                "SELECT id FROM users WHERE email = ?", (email,)
            ).fetchone()
            if existing:
                return jsonify({"error": "An account with this email already exists."}), 409

            password_hash = generate_password_hash(password)
            conn.execute(
                """
                INSERT INTO users (email, password_hash, role, is_verified, verification_token, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (email, password_hash, role, 0, verification_token, datetime.utcnow().isoformat()),
            )
            conn.commit()
    except sqlite3.Error as exc:
        print(f"Signup error: {exc}")
        return jsonify({"error": "Unable to create account at this time."}), 500

    email_sent, verification_link, delivery_error = send_verification_email(
        email, verification_token
    )

    response_payload = {
        "message": (
            "Signup successful. Please check your email to verify your account."
            if email_sent
            else "Signup successful. Email delivery is not available. Use the link below to verify your account."
        ),
        "verificationUrl": verification_link,
        "verificationToken": verification_token,
        "emailDelivery": {
            "status": "sent" if email_sent else "not_sent",
            **({"error": delivery_error} if delivery_error else {}),
        },
    }

    return jsonify(response_payload)


@app.route('/api/auth/login', methods=['POST'])
def login():
    payload = request.json or {}
    email = (payload.get('email') or '').strip().lower()
    password = payload.get('password') or ''
    role = payload.get('role')

    if not email or not password or not role:
        return jsonify({"error": "Email, password, and role are required."}), 400

    if role not in VALID_ROLES:
        return jsonify({"error": "Invalid role supplied."}), 400

    try:
        with get_db_connection() as conn:
            user = conn.execute(
                "SELECT id, password_hash, role, is_verified FROM users WHERE email = ?",
                (email,),
            ).fetchone()
    except sqlite3.Error as exc:
        print(f"Login error: {exc}")
        return jsonify({"error": "Unable to process login at this time."}), 500

    if not user or user["role"] != role:
        return jsonify({"error": "Invalid credentials."}), 401

    if not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid credentials."}), 401

    if not user["is_verified"]:
        return jsonify({"error": "Please verify your email before logging in."}), 403

    token = generate_api_token()

    try:
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE users SET api_token = ? WHERE id = ?",
                (token, user["id"]),
            )
            conn.commit()
    except sqlite3.Error as exc:
        print(f"Failed to update user token: {exc}")
        return jsonify({"error": "Unable to create session. Please try again."}), 500

    return jsonify({
        "message": "Login successful.",
        "user": {
            "email": email,
            "role": role,
            "token": token,
        },
    })


@app.route('/api/students', methods=['POST'])
def create_student():
    user, error_response = authenticate_request()
    if error_response:
        payload, status_code = error_response
        return jsonify(payload), status_code

    forbidden = require_role(user, {"school_admin"})
    if forbidden:
        payload, status_code = forbidden
        return jsonify(payload), status_code

    payload = request.json or {}
    full_name = (payload.get('full_name') or '').strip()
    if not full_name:
        return jsonify({"error": "Student name is required."}), 400

    age_value = payload.get('age')
    age = None
    if age_value not in (None, ''):
        try:
            age = int(age_value)
            if age < 0:
                raise ValueError
        except (ValueError, TypeError):
            return jsonify({"error": "Age must be a positive number."}), 400

    try:
        date_of_birth = normalize_date_of_birth(payload.get('date_of_birth'))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    class_level = (payload.get('class_level') or '').strip() or None
    guardian_contact = (payload.get('guardian_contact') or '').strip() or None
    additional_info = (payload.get('additional_info') or '').strip() or None

    code = generate_student_code()
    school_number = generate_school_number(user["id"])
    now = datetime.utcnow().isoformat()

    try:
        with get_db_connection() as conn:
            # Ensure code uniqueness
            attempts = 0
            while attempts < 5:
                existing = conn.execute(
                    "SELECT 1 FROM students WHERE unique_code = ?",
                    (code,),
                ).fetchone()
                if existing:
                    code = generate_student_code()
                    attempts += 1
                else:
                    break

            cursor = conn.execute(
                """
                INSERT INTO students (
                    user_id,
                    school_number,
                    full_name,
                    unique_code,
                    age,
                    date_of_birth,
                    class_level,
                    guardian_contact,
                    additional_info,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user["id"],
                    school_number,
                    full_name,
                    code,
                    age,
                    date_of_birth,
                    class_level,
                    guardian_contact,
                    additional_info,
                    now,
                ),
            )
            student_id = cursor.lastrowid
            conn.commit()
            student_row = conn.execute(
                "SELECT * FROM students WHERE id = ?", (student_id,)
            ).fetchone()
    except sqlite3.Error as exc:
        print(f"Error creating student: {exc}")
        return jsonify({"error": "Unable to register student."}), 500

    return jsonify(
        {
            "message": "Student registered successfully.",
            "student": serialize_student(student_row),
        }
    )


@app.route('/api/students', methods=['GET'])
def list_students_route():
    user, error_response = authenticate_request()
    if error_response:
        payload, status_code = error_response
        return jsonify(payload), status_code

    forbidden = require_role(user, {"school_admin"})
    if forbidden:
        payload, status_code = forbidden
        return jsonify(payload), status_code

    try:
        with get_db_connection() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM students
                WHERE user_id = ?
                ORDER BY datetime(created_at) DESC, id DESC
                """,
                (user["id"],),
            ).fetchall()
    except sqlite3.Error as exc:
        print(f"Error listing students: {exc}")
        return jsonify({"error": "Unable to load students."}), 500

    return jsonify([serialize_student(row) for row in rows])


@app.route('/api/students/<int:student_id>', methods=['GET', 'DELETE', 'POST'])
def get_student(student_id: int):
    user, error_response = authenticate_request()
    if error_response:
        payload, status_code = error_response
        return jsonify(payload), status_code

    forbidden = require_role(user, {"school_admin"})
    if forbidden:
        payload, status_code = forbidden
        return jsonify(payload), status_code

    row = get_student_for_user(student_id, user["id"])
    if row is None:
        return jsonify({"error": "Student not found."}), 404

    if request.method in {"DELETE", "POST"}:
        try:
            with get_db_connection() as conn:
                conn.execute(
                    "DELETE FROM students WHERE id = ? AND user_id = ?",
                    (student_id, user["id"]),
                )
                conn.commit()
        except sqlite3.Error as exc:
            print(f"Error deleting student: {exc}")
            return jsonify({"error": "Unable to delete student."}), 500

        return jsonify({"message": "Student deleted successfully.", "studentId": student_id})

    return jsonify(serialize_student(row))


@app.route('/api/students/<int:student_id>/delete', methods=['POST', 'DELETE'])
def delete_student_fallback(student_id: int):
    """
    Fallback delete endpoint for environments that block HTTP DELETE.
    Mirrors DELETE /api/students/<student_id>.
    """
    return get_student(student_id)


@app.route('/api/students/lookup', methods=['POST'])
def lookup_student():
    user, error_response = authenticate_request()
    if error_response:
        payload, status_code = error_response
        return jsonify(payload), status_code

    forbidden = require_role(user, {"school_admin"})
    if forbidden:
        payload, status_code = forbidden
        return jsonify(payload), status_code

    code = (request.json or {}).get('code')
    if not code:
        return jsonify({"error": "Student code is required."}), 400

    code = str(code).strip().upper()

    try:
        with get_db_connection() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM students
                WHERE user_id = ? AND unique_code = ?
                """,
                (user["id"], code),
            ).fetchone()
    except sqlite3.Error as exc:
        print(f"Error looking up student: {exc}")
        return jsonify({"error": "Unable to lookup student."}), 500

    if row is None:
        return jsonify({"error": "Student not found."}), 404

    return jsonify(serialize_student(row))


@app.route('/api/auth/verify/<verification_token>', methods=['GET'])
def verify_account(verification_token: str):
    if not verification_token:
        return jsonify({"error": "Verification token is required."}), 400

    try:
        with get_db_connection() as conn:
            user = conn.execute(
                "SELECT id, is_verified FROM users WHERE verification_token = ?",
                (verification_token,),
            ).fetchone()

            if user is None:
                return jsonify({"error": "Invalid or expired verification token."}), 404

            if user["is_verified"]:
                return jsonify({"message": "Account already verified."})

            conn.execute(
                "UPDATE users SET is_verified = 1 WHERE id = ?",
                (user["id"],),
            )
            conn.commit()
    except sqlite3.Error as exc:
        print(f"Verification error: {exc}")
        return jsonify({"error": "Unable to verify account at this time."}), 500

    return jsonify({"message": "Account verified successfully."})

@app.route('/api/analysis/background', methods=['GET'])
@rate_limited("analysis")
@cached_json_response("analysis_background")
def get_background_analysis():
    global data
    latest_data = _load_from_known_locations()
    if latest_data is not None:
        data = latest_data
    if data is None:
        load_initial_data()
    if data is None or len(data) == 0:
        return jsonify(_empty_background_analysis_result("Data not loaded")), 200
    
    try:
        # Get include_details parameter (default to True for backward compatibility)
        include_details = request.args.get('include_details', 'true').lower() == 'true'
        results, _error = _run_background_analysis(include_details)
        return jsonify(results)
    except Exception as e:
        logger.exception("background_analysis_route_failed")
        return jsonify(_empty_background_analysis_result(str(e))), 200

@app.route('/api/analysis/behavioral', methods=['GET'])
@rate_limited("analysis")
@cached_json_response("analysis_behavioral")
def get_behavioral_analysis():
    if data is None:
        return jsonify({"error": "Data not loaded"}), 500
    
    try:
        full_mode = request.args.get('full', 'false').lower() == 'true'
        # Default to responsive mode so one heavy request does not block overview APIs.
        results = behavioral.analyze_behavioral_impact(
            data,
            allow_training=full_mode,
            lightweight=not full_mode,
        )
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analysis/rolemodel', methods=['GET'])
@rate_limited("analysis")
@cached_json_response("analysis_rolemodel")
def get_rolemodel_analysis():
    if data is None:
        return jsonify({"error": "Data not loaded"}), 500
    
    try:
        results = rolemodels.analyze_role_model(data)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analysis/income', methods=['GET'])
@rate_limited("analysis")
@cached_json_response("analysis_income")
def get_income_analysis():
    if data is None:
        return jsonify({"error": "Data not loaded"}), 500
    
    try:
        results = income.get_income_sentiment(data)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analysis/home-problems', methods=['GET'])
@rate_limited("analysis")
@cached_json_response("analysis_home_problems")
def get_home_problems_analysis():
    if data is None:
        return jsonify({"error": "Data not loaded"}), 500

    try:
        results = home_problems.analyze_problems_in_home(data)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analysis/complete', methods=['GET'])
@rate_limited("analysis")
@cached_json_response("analysis_complete")
def get_complete_analysis():
    # If not loaded yet, attempt to load; otherwise respond with empty analysis
    global data
    latest_data = _load_from_known_locations()
    if latest_data is not None:
        data = latest_data
    if data is None:
        load_initial_data()

    # Get include_details parameter (default to false to exclude background details)
    include_details = request.args.get('include_details', 'false').lower() == 'true'

    if data is None or len(data) == 0:
        empty_resp = {
            "background": _empty_background_analysis_result("Data not loaded"),
            "behavioral": {},
            "rolemodel": {},
            "income": {},
            "home_problems": {},
            "totalSurveys": 0
        }
        return jsonify(empty_resp)

    analysis_errors = {}

    bg, background_error = _run_background_analysis(include_details)
    if background_error:
        analysis_errors["background"] = background_error

    try:
        # Use full dataset for complete overview while keeping lightweight mode for speed.
        beh = behavioral.analyze_behavioral_impact(data, allow_training=False, lightweight=True)
    except Exception as e:
        print(f"complete analysis behavioral error: {e}")
        beh = {}
        analysis_errors["behavioral"] = str(e)

    try:
        rm = rolemodels.analyze_role_model(data)
    except Exception as e:
        print(f"complete analysis rolemodel error: {e}")
        rm = {}
        analysis_errors["rolemodel"] = str(e)

    try:
        inc = income.get_income_sentiment(data)
    except Exception as e:
        print(f"complete analysis income error: {e}")
        inc = {}
        analysis_errors["income"] = str(e)

    try:
        home = home_problems.analyze_problems_in_home(data)
    except Exception as e:
        print(f"complete analysis home problems error: {e}")
        home = {}
        analysis_errors["home_problems"] = str(e)

    response_payload = {
        "background": bg,
        "behavioral": beh,
        "rolemodel": rm,
        "income": inc,
        "home_problems": home,
        "totalSurveys": len(data)
    }
    if analysis_errors:
        response_payload["analysis_errors"] = analysis_errors
    return jsonify(response_payload)

@app.route('/api/analysis/complete-summary', methods=['GET'])
@rate_limited("analysis")
@cached_json_response("analysis_complete_summary")
def get_complete_summary():
    """New endpoint that returns all analyses without detailed background data"""
    global data
    latest_data = _load_from_known_locations()
    if latest_data is not None:
        data = latest_data
    if data is None:
        return jsonify({"error": "Data not loaded"}), 500
    
    analysis_errors = {}

    background_results, background_error = _run_background_analysis(include_details=False)
    if background_error:
        analysis_errors["background"] = background_error

    try:
        behavioral_results = behavioral.analyze_behavioral_impact(
            data, allow_training=False, lightweight=True
        )
    except Exception as e:
        print(f"complete-summary behavioral error: {e}")
        behavioral_results = {}
        analysis_errors["behavioral"] = str(e)

    try:
        rolemodel_results = rolemodels.analyze_role_model(data)
    except Exception as e:
        print(f"complete-summary rolemodel error: {e}")
        rolemodel_results = {}
        analysis_errors["rolemodel"] = str(e)

    try:
        income_results = income.get_income_sentiment(data)
    except Exception as e:
        print(f"complete-summary income error: {e}")
        income_results = {}
        analysis_errors["income"] = str(e)

    try:
        home_problem_results = home_problems.analyze_problems_in_home(data)
    except Exception as e:
        print(f"complete-summary home problems error: {e}")
        home_problem_results = {}
        analysis_errors["home_problems"] = str(e)

    payload = {
        "background": background_results,
        "behavioral": behavioral_results,
        "rolemodel": rolemodel_results,
        "income": income_results,
        "home_problems": home_problem_results,
        "totalSurveys": len(data)
    }
    if analysis_errors:
        payload["analysis_errors"] = analysis_errors
    return jsonify(payload)


@app.route('/api/analysis/career-confidence', methods=['POST'])
def analyze_career_confidence():
    """
    Run hierarchical regression to estimate how income, behavior, and role-model
    exposure relate to career confidence.
    """
    payload = request.json or {}
    records = payload.get("data")

    if not isinstance(records, list) or not records:
        return (
            jsonify({"error": "Request must include a non-empty 'data' array."}),
            400,
        )

    try:
        results = run_career_confidence_models(records)
        return jsonify(results)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        print(f"Error in career confidence regression: {exc}")
        return jsonify({"error": "Unable to run regression."}), 500


@app.route('/api/data-quality/ingest-surveys-batch', methods=['POST'])
@rate_limited("ingestion")
def ingest_surveys_batch():
    user, error_response = authenticate_request()
    if error_response:
        payload, status_code = error_response
        return jsonify(payload), status_code

    role_error = require_role(user, {"school_admin"})
    if role_error:
        payload, status_code = role_error
        return jsonify(payload), status_code

    payload = request.json or {}
    records = payload.get("records") or payload.get("data")
    schema_version = payload.get("schemaVersion")
    source = str(payload.get("source") or "api_batch").strip()
    batch_id = payload.get("batchId")

    try:
        result = ingest_survey_batch_records(
            records=records,
            schema_version=schema_version,
            source=source,
            batch_id=batch_id,
        )
        _bump_cache_version()
        return jsonify({"success": True, **result}), 201
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except sqlite3.IntegrityError:
        return jsonify({"error": "batchId already exists. Use a unique batchId."}), 409
    except Exception as exc:
        logger.error("batch_ingestion_failed", extra={"error": str(exc)})
        return jsonify({"error": "Unable to ingest batch."}), 500


@app.route('/api/data-quality/monitoring', methods=['GET'])
@rate_limited("analytics_reads")
@cached_json_response("data_quality_monitoring")
def get_data_quality_monitoring():
    user, error_response = authenticate_request()
    if error_response:
        payload, status_code = error_response
        return jsonify(payload), status_code

    schema_version = request.args.get("schemaVersion")
    try:
        page, page_size, offset = parse_pagination_args(
            default_page_size=50,
            max_page_size=settings.analytics_max_page_size,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    where_clauses = []
    params = []
    if schema_version:
        where_clauses.append("b.schema_version = ?")
        params.append(schema_version)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    with get_db_connection() as conn:
        total_batches = conn.execute(
            f"""
            SELECT COUNT(*) AS total_count
            FROM data_quality_batches b
            {where_sql}
            """,
            params,
        ).fetchone()["total_count"]

        rows = conn.execute(
            f"""
            SELECT
                b.batch_id,
                b.schema_version,
                b.source,
                b.ingested_at,
                b.total_rows,
                b.inserted_rows,
                b.duplicate_rows,
                b.outlier_rows,
                b.completeness_score,
                (
                    SELECT COUNT(*)
                    FROM data_quality_alerts a
                    WHERE a.batch_id = b.batch_id
                ) AS alert_count
            FROM data_quality_batches b
            {where_sql}
            ORDER BY datetime(b.ingested_at) DESC
            LIMIT ?
            OFFSET ?
            """,
            [*params, page_size, offset],
        ).fetchall()

        config = get_data_quality_alert_config(conn)

    batches = [
        {
            "batchId": row["batch_id"],
            "schemaVersion": row["schema_version"],
            "source": row["source"],
            "ingestedAt": row["ingested_at"],
            "totalRows": row["total_rows"],
            "insertedRows": row["inserted_rows"],
            "duplicateRows": row["duplicate_rows"],
            "outlierRows": row["outlier_rows"],
            "completenessScore": row["completeness_score"],
            "alertCount": row["alert_count"],
        }
        for row in rows
    ]

    return jsonify(
        {
            "batches": batches,
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "total": total_batches,
                "totalPages": (total_batches + page_size - 1) // page_size if page_size else 0,
            },
            "thresholds": {
                "completenessMin": config["completeness_min"],
                "duplicatesMax": config["duplicates_max"],
                "outliersMax": config["outliers_max"],
            },
        }
    )


@app.route('/api/data-quality/batches/<batch_id>', methods=['GET'])
@rate_limited("analytics_reads")
@cached_json_response("data_quality_batch_details")
def get_data_quality_batch_details(batch_id: str):
    user, error_response = authenticate_request()
    if error_response:
        payload, status_code = error_response
        return jsonify(payload), status_code

    try:
        page, page_size, offset = parse_pagination_args(
            default_page_size=25,
            max_page_size=settings.analytics_max_page_size,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    with get_db_connection() as conn:
        batch = conn.execute(
            """
            SELECT
                batch_id,
                schema_version,
                source,
                ingested_at,
                total_rows,
                inserted_rows,
                duplicate_rows,
                outlier_rows,
                completeness_score,
                created_at
            FROM data_quality_batches
            WHERE batch_id = ?
            """,
            (batch_id,),
        ).fetchone()

        if batch is None:
            return jsonify({"error": "Batch not found."}), 404

        field_metrics = conn.execute(
            """
            SELECT
                field_name,
                total_count,
                missing_count,
                completeness_ratio,
                outlier_count
            FROM data_quality_field_metrics
            WHERE batch_id = ?
            ORDER BY field_name
            LIMIT ?
            OFFSET ?
            """,
            (batch_id, page_size, offset),
        ).fetchall()

        total_alerts = conn.execute(
            """
            SELECT COUNT(*) AS total_count
            FROM data_quality_alerts
            WHERE batch_id = ?
            """,
            (batch_id,),
        ).fetchone()["total_count"]

        alerts = conn.execute(
            """
            SELECT
                id,
                metric_name,
                metric_value,
                threshold_value,
                comparator,
                severity,
                message,
                channels,
                created_at
            FROM data_quality_alerts
            WHERE batch_id = ?
            ORDER BY datetime(created_at) DESC
            LIMIT ?
            OFFSET ?
            """,
            (batch_id, page_size, offset),
        ).fetchall()

    return jsonify(
        {
            "batch": {
                "batchId": batch["batch_id"],
                "schemaVersion": batch["schema_version"],
                "source": batch["source"],
                "ingestedAt": batch["ingested_at"],
                "totalRows": batch["total_rows"],
                "insertedRows": batch["inserted_rows"],
                "duplicateRows": batch["duplicate_rows"],
                "outlierRows": batch["outlier_rows"],
                "completenessScore": batch["completeness_score"],
                "createdAt": batch["created_at"],
            },
            "fieldMetrics": [
                {
                    "fieldName": item["field_name"],
                    "totalCount": item["total_count"],
                    "missingCount": item["missing_count"],
                    "completenessRatio": item["completeness_ratio"],
                    "outlierCount": item["outlier_count"],
                }
                for item in field_metrics
            ],
            "alerts": [
                {
                    "id": item["id"],
                    "metricName": item["metric_name"],
                    "metricValue": item["metric_value"],
                    "thresholdValue": item["threshold_value"],
                    "comparator": item["comparator"],
                    "severity": item["severity"],
                    "message": item["message"],
                    "channels": _parse_json_column(item["channels"]) or {},
                    "createdAt": item["created_at"],
                }
                for item in alerts
            ],
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "totalAlerts": total_alerts,
                "totalAlertPages": (total_alerts + page_size - 1) // page_size
                if page_size
                else 0,
            },
        }
    )


@app.route('/api/data-quality/alerts/config', methods=['GET'])
def get_data_quality_alert_config_route():
    user, error_response = authenticate_request()
    if error_response:
        payload, status_code = error_response
        return jsonify(payload), status_code

    with get_db_connection() as conn:
        config = get_data_quality_alert_config(conn)

    return jsonify(
        {
            "completenessMin": config["completeness_min"],
            "duplicatesMax": config["duplicates_max"],
            "outliersMax": config["outliers_max"],
            "emailRecipients": config["email_recipients"],
            "webhookUrls": config["webhook_urls"],
            "slackWebhookUrl": config["slack_webhook_url"],
            "updatedAt": config["updated_at"],
        }
    )


@app.route('/api/data-quality/alerts/config', methods=['POST'])
def update_data_quality_alert_config_route():
    user, error_response = authenticate_request()
    if error_response:
        payload, status_code = error_response
        return jsonify(payload), status_code

    role_error = require_role(user, {"school_admin"})
    if role_error:
        payload, status_code = role_error
        return jsonify(payload), status_code

    payload = request.json or {}
    completeness_min = payload.get("completenessMin")
    duplicates_max = payload.get("duplicatesMax")
    outliers_max = payload.get("outliersMax")
    email_recipients = payload.get("emailRecipients") or []
    webhook_urls = payload.get("webhookUrls") or []
    slack_webhook_url = payload.get("slackWebhookUrl")

    try:
        completeness_min = float(completeness_min)
        duplicates_max = int(duplicates_max)
        outliers_max = int(outliers_max)
    except (TypeError, ValueError):
        return jsonify({"error": "Threshold values are invalid."}), 400

    if completeness_min < 0 or completeness_min > 1:
        return jsonify({"error": "completenessMin must be between 0 and 1."}), 400
    if duplicates_max < 0 or outliers_max < 0:
        return jsonify({"error": "duplicatesMax and outliersMax must be >= 0."}), 400

    if not isinstance(email_recipients, list) or not isinstance(webhook_urls, list):
        return jsonify({"error": "emailRecipients and webhookUrls must be arrays."}), 400

    cleaned_emails = [str(item).strip() for item in email_recipients if str(item).strip()]
    cleaned_urls = [str(item).strip() for item in webhook_urls if str(item).strip()]
    cleaned_slack = str(slack_webhook_url).strip() if slack_webhook_url else None

    with get_db_connection() as conn:
        conn.execute(
            """
            INSERT INTO data_quality_alert_config (
                id,
                completeness_min,
                duplicates_max,
                outliers_max,
                email_recipients,
                webhook_urls,
                slack_webhook_url,
                updated_at
            ) VALUES (1, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                completeness_min = excluded.completeness_min,
                duplicates_max = excluded.duplicates_max,
                outliers_max = excluded.outliers_max,
                email_recipients = excluded.email_recipients,
                webhook_urls = excluded.webhook_urls,
                slack_webhook_url = excluded.slack_webhook_url,
                updated_at = excluded.updated_at
            """,
            (
                completeness_min,
                duplicates_max,
                outliers_max,
                json.dumps(cleaned_emails),
                json.dumps(cleaned_urls),
                cleaned_slack,
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        updated_config = get_data_quality_alert_config(conn)

    return jsonify(
        {
            "message": "Alert configuration updated.",
            "config": {
                "completenessMin": updated_config["completeness_min"],
                "duplicatesMax": updated_config["duplicates_max"],
                "outliersMax": updated_config["outliers_max"],
                "emailRecipients": updated_config["email_recipients"],
                "webhookUrls": updated_config["webhook_urls"],
                "slackWebhookUrl": updated_config["slack_webhook_url"],
                "updatedAt": updated_config["updated_at"],
            },
        }
    )


@app.route('/api/submit-survey', methods=['POST'])
@rate_limited("ingestion")
def submit_survey():
    global data
    user, error_response = authenticate_request()
    if error_response:
        payload, status_code = error_response
        return jsonify(payload), status_code
    
    try:
        # Get the form data from the request
        survey_data = request.json or {}
        if not isinstance(survey_data, dict):
            return jsonify({"error": "Invalid survey payload."}), 400

        student_id_raw = survey_data.pop("studentId", None)
        student_id = None
        student_row = None
        if student_id_raw not in (None, ""):
            try:
                student_id_value = int(student_id_raw)
            except (ValueError, TypeError):
                return jsonify({"error": "Invalid student identifier."}), 400

            student_row = get_student_for_user(student_id_value, user["id"])
            if student_row is None:
                return jsonify({"error": "Student not found."}), 404
            student_id = student_row["id"]

        normalized_submission = normalize_submission_payload(survey_data)
        try:
            submitted_date_of_birth = normalize_date_of_birth(
                normalized_submission.get("Date of Birth")
            )
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        if student_row is not None:
            stored_date_of_birth = normalize_date_of_birth(student_row["date_of_birth"])
            if stored_date_of_birth:
                normalized_submission["Date of Birth"] = stored_date_of_birth
            elif submitted_date_of_birth:
                normalized_submission["Date of Birth"] = submitted_date_of_birth
                try:
                    with get_db_connection() as conn:
                        conn.execute(
                            "UPDATE students SET date_of_birth = ? WHERE id = ? AND user_id = ?",
                            (submitted_date_of_birth, student_id, user["id"]),
                        )
                        conn.commit()
                except sqlite3.Error as exc:
                    print(f"Failed to persist student date of birth: {exc}")
                    return jsonify({"error": "Unable to save student date of birth."}), 500
        else:
            normalized_submission["Date of Birth"] = submitted_date_of_birth

        submission_hash = compute_survey_row_hash(normalized_submission)
        with get_db_connection() as conn:
            existing_row = conn.execute(
                "SELECT 1 FROM surveys WHERE unique_hash = ? LIMIT 1",
                (submission_hash,),
            ).fetchone()
        pre_existing = existing_row is not None
        
        # Process the survey data and get analysis results
        analysis_results = survey_processor.process_and_save_survey(normalized_submission)
        created_at = (
            analysis_results.get("timestamp")
            or normalized_submission.get("Timestamp")
            or datetime.utcnow().isoformat()
        )
        normalized_submission["Timestamp"] = normalized_submission.get("Timestamp") or created_at

        try:
            append_submission_to_excel(normalized_submission, created_at=created_at)
        except Exception as excel_exc:
            print(f"Failed to append submission to Childsurvey.xlsx: {excel_exc}")
            return jsonify({"error": "Unable to store survey in Childsurvey.xlsx."}), 500

        # Extract supplemental sections if present
        recommendations_data = (
            analysis_results.get("recommendations")
            or analysis_results.get("roleModel", {})
            .get("analysis", {})
            .get("recommendations")
        )
        career_suggestions_data = (
            analysis_results.get("careerSuggestions")
            or analysis_results.get("roleModel", {})
            .get("analysis", {})
            .get("careerSuggestions")
        )

        # Persist assessment record
        try:
            with get_db_connection() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO assessments (
                        user_id,
                        created_at,
                        survey_data,
                        scores,
                        recommendations,
                        career_suggestions,
                        student_id
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user["id"],
                        created_at,
                        json.dumps(normalized_submission),
                        json.dumps(analysis_results),
                        json.dumps(recommendations_data, default=str)
                        if recommendations_data is not None
                        else None,
                        json.dumps(career_suggestions_data, default=str)
                        if career_suggestions_data is not None
                        else None,
                        student_id,
                    ),
                )
                assessment_id = cursor.lastrowid
                conn.commit()
        except sqlite3.Error as exc:
            print(f"Failed to persist assessment: {exc}")
            return jsonify({"error": "Unable to save assessment."}), 500
        
        # Reload the data to include the new entry (search known locations)
        data = _load_from_known_locations()

        inserted_rows = 0 if pre_existing else 1
        single_batch_metrics = compute_batch_quality_metrics(
            [normalized_submission],
            inserted_rows,
        )
        single_batch_id = f"single_{uuid4().hex[:12]}"
        single_schema_version = settings.data_quality_default_schema_version or "v1"
        single_source = "submit_survey"
        single_ingested_at = created_at
        alerts = []
        alert_delivery = {"email": [], "webhook": [], "slack": []}

        try:
            with get_db_connection() as conn:
                save_data_quality_batch(
                    conn=conn,
                    batch_id=single_batch_id,
                    schema_version=single_schema_version,
                    source=single_source,
                    ingested_at=single_ingested_at,
                    metrics=single_batch_metrics,
                )
                alert_config = get_data_quality_alert_config(conn)
                alerts = evaluate_data_quality_alerts(single_batch_metrics, alert_config)
                conn.commit()

            alert_delivery = dispatch_data_quality_alerts(
                single_batch_id, alerts, alert_config
            )
            if alerts:
                with get_db_connection() as conn:
                    persist_data_quality_alerts(
                        conn=conn,
                        batch_id=single_batch_id,
                        alerts=alerts,
                        channels=alert_delivery,
                    )
                    conn.commit()
        except Exception as quality_exc:
            logger.error(
                "single_submission_quality_failed",
                extra={"error": str(quality_exc)},
            )
        
        # Return the analysis results
        response = {
            "message": "Survey submitted and analyzed successfully",
            "analysis": analysis_results,
            "assessmentId": assessment_id,
            "studentId": student_id,
            "qualityBatchId": single_batch_id,
            "qualityMetrics": single_batch_metrics,
            "qualityAlerts": alerts,
        }

        # Emit real-time update to all connected clients
        socketio.emit('survey_submitted', {
            'analysis': analysis_results,
            'totalSurveys': len(data)
        })



        _bump_cache_version()
        return jsonify({"success": True, **response})
    
    except Exception as e:
        print(f"Error in submit_survey: {e}")
        return jsonify({"error": str(e)}), 500


def _parse_json_column(value: Optional[str]):
    if value in (None, "", "null"):
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError) as exc:
        print(f"Failed to decode JSON column: {exc}")
        return None


@app.route('/api/assessments', methods=['GET'])
def list_assessments():
    user, error_response = authenticate_request()
    if error_response:
        payload, status_code = error_response
        return jsonify(payload), status_code

    student_filter = request.args.get('student_id')
    student_id = None
    if student_filter not in (None, ''):
        try:
            student_id = int(student_filter)
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid student filter."}), 400

    try:
        params = [user["id"]]
        query = """
            SELECT
                a.id,
                a.created_at,
                a.scores,
                a.student_id,
                s.full_name AS student_name
            FROM assessments a
            LEFT JOIN students s ON s.id = a.student_id
            WHERE a.user_id = ?
        """
        if student_id is not None:
            query += " AND a.student_id = ?"
            params.append(student_id)
        query += " ORDER BY datetime(a.created_at) DESC, a.id DESC"

        with get_db_connection() as conn:
            rows = conn.execute(query, params).fetchall()
    except sqlite3.Error as exc:
        print(f"Error listing assessments: {exc}")
        return jsonify({"error": "Unable to load assessments."}), 500

    assessments = []
    for row in rows:
        scores = _parse_json_column(row["scores"]) or {}

        role_model_top_trait = None
        try:
            traits = scores.get("roleModel", {}).get("analysis", {}).get("topTraits", {})
            role_model_top_trait = next(iter(traits.keys())) if traits else None
        except AttributeError:
            role_model_top_trait = None

        background_avg = scores.get("background", {}).get("analysis", {}).get(
            "average_score"
        )

        assessments.append(
            {
                "id": row["id"],
                "created_at": row["created_at"],
                "headline": role_model_top_trait,
                "backgroundAverageScore": background_avg,
                "student_id": row["student_id"],
                "student_name": row["student_name"],
            }
        )

    return jsonify(assessments)


@app.route('/api/assessments/<int:assessment_id>', methods=['GET'])
def get_assessment(assessment_id: int):
    user, error_response = authenticate_request()
    if error_response:
        payload, status_code = error_response
        return jsonify(payload), status_code

    try:
        with get_db_connection() as conn:
            row = conn.execute(
                """
                SELECT
                    a.*,
                    s.full_name AS student_name,
                    s.unique_code AS student_code
                FROM assessments a
                LEFT JOIN students s ON s.id = a.student_id
                WHERE a.id = ? AND a.user_id = ?
                """,
                (assessment_id, user["id"]),
            ).fetchone()
    except sqlite3.Error as exc:
        print(f"Error fetching assessment: {exc}")
        return jsonify({"error": "Unable to load assessment."}), 500

    if row is None:
        return jsonify({"error": "Assessment not found."}), 404

    raw_survey_data = _parse_json_column(row["survey_data"]) or {}
    normalized_survey_data = dict(raw_survey_data) if isinstance(raw_survey_data, dict) else {}
    if isinstance(raw_survey_data, dict):
        normalized_survey_data.update(
            normalize_submission_payload(
                raw_survey_data, fallback_timestamp=row["created_at"]
            )
        )

    response_payload = {
        "id": row["id"],
        "created_at": row["created_at"],
        "survey_data": normalized_survey_data,
        "scores": _parse_json_column(row["scores"]) or {},
        "recommendations": _parse_json_column(row["recommendations"]),
        "career_suggestions": _parse_json_column(row["career_suggestions"]),
        "student": (
            {
                "id": row["student_id"],
                "full_name": row["student_name"],
                "unique_code": row["student_code"],
            }
            if row["student_id"]
            else None
        ),
    }

    return jsonify(response_payload)


@app.route('/api/mentor/embeddings', methods=['POST'])
def upsert_mentor_embedding_route():
    user, error_response = authenticate_request()
    if error_response:
        payload, status_code = error_response
        return jsonify(payload), status_code

    payload = request.json or {}
    mentor_id = (payload.get("mentorId") or payload.get("mentor_id") or "").strip()
    if not mentor_id:
        return jsonify({"error": "mentorId is required."}), 400

    try:
        embedding = _coerce_embedding(
            payload.get("embedding"),
            field="embedding",
            expected_dim=settings.pg_vector_dim,
        )
        profile = _coerce_dict(payload.get("profile"), field="profile")
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        store = _get_vector_store()
        store.upsert_mentor_embedding(mentor_id, embedding, profile)
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 503
    except Exception as exc:
        print(f"Error upserting mentor embedding: {exc}")
        return jsonify({"error": "Unable to store mentor embedding."}), 500

    return jsonify(
        {
            "message": "Mentor embedding stored.",
            "mentorId": mentor_id,
            "dimension": settings.pg_vector_dim,
        }
    ), 201


@app.route('/api/needs/embeddings', methods=['POST'])
def upsert_need_embedding_route():
    user, error_response = authenticate_request()
    if error_response:
        payload, status_code = error_response
        return jsonify(payload), status_code

    payload = request.json or {}
    need_id = (payload.get("needId") or payload.get("need_id") or "").strip()
    if not need_id:
        return jsonify({"error": "needId is required."}), 400

    user_id_value = (
        str(payload.get("userId") or payload.get("user_id") or user["id"])
    )

    try:
        embedding = _coerce_embedding(
            payload.get("embedding"),
            field="embedding",
            expected_dim=settings.pg_vector_dim,
        )
        context = _coerce_dict(payload.get("context") or payload.get("needContext"), field="context")
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        store = _get_vector_store()
        store.upsert_need_embedding(need_id, user_id_value, embedding, context)
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 503
    except Exception as exc:
        print(f"Error upserting need embedding: {exc}")
        return jsonify({"error": "Unable to store need embedding."}), 500

    return jsonify(
        {
            "message": "Need embedding stored.",
            "needId": need_id,
            "userId": user_id_value,
            "dimension": settings.pg_vector_dim,
        }
    ), 201


@app.route('/api/match/cosine', methods=['POST'])
def cosine_match_route():
    user, error_response = authenticate_request()
    if error_response:
        payload, status_code = error_response
        return jsonify(payload), status_code

    payload = request.json or {}
    top_k_raw = payload.get("topK") or payload.get("top_k") or 5
    try:
        top_k = max(1, min(50, int(top_k_raw)))
    except (TypeError, ValueError):
        return jsonify({"error": "topK must be an integer."}), 400

    try:
        embedding = _coerce_embedding(
            payload.get("embedding"),
            field="embedding",
            expected_dim=settings.pg_vector_dim,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        store = _get_vector_store()
        matches = store.fetch_similar_mentors(embedding, top_k=top_k)
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 503
    except Exception as exc:
        print(f"Error computing cosine matches: {exc}")
        return jsonify({"error": "Unable to compute matches."}), 500

    return jsonify(
        {
            "matches": matches,
            "count": len(matches),
            "topK": top_k,
            "dimension": settings.pg_vector_dim,
        }
    )


@app.route('/api/feedback/mentor-rating', methods=['POST'])
def record_mentor_rating_route():
    user, error_response = authenticate_request()
    if error_response:
        payload, status_code = error_response
        return jsonify(payload), status_code

    payload = request.json or {}
    mentor_id = (payload.get("mentorId") or payload.get("mentor_id") or "").strip()
    if not mentor_id:
        return jsonify({"error": "mentorId is required."}), 400

    rating_raw = payload.get("rating")
    try:
        rating = int(rating_raw)
    except (TypeError, ValueError):
        return jsonify({"error": "rating must be an integer between 1 and 5."}), 400

    try:
        store = _get_vector_store()
        store.record_rating(str(user["id"]), mentor_id, rating)
        weight_info = store.get_weight(mentor_id)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 503
    except Exception as exc:
        print(f"Error recording mentor rating: {exc}")
        return jsonify({"error": "Unable to record rating."}), 500

    return jsonify(
        {
            "message": "Rating stored and weights adjusted.",
            "mentorId": mentor_id,
            "rating": rating,
            "weight": weight_info,
        }
    ), 201


@app.route('/api/notifications/email', methods=['POST'])
def send_email_route():
    user, error_response = authenticate_request()
    if error_response:
        payload, status_code = error_response
        return jsonify(payload), status_code

    payload = request.json or {}
    recipient = (payload.get("to") or payload.get("email") or "").strip()
    subject = payload.get("subject") or "Notification"
    body = payload.get("body") or ""
    use_async = str(payload.get("async") or "true").lower() == "true"

    if not recipient:
        return jsonify({"error": "Recipient email is required."}), 400

    if use_async:
        try:
            task = send_email_task.delay(recipient, subject, body)
            return jsonify({"taskId": task.id, "status": "queued"}), 202
        except Exception as exc:
            logger.error("queue_email_failed", extra={"error": str(exc)})
            return jsonify({"error": "Unable to queue email."}), 500

    success, err = send_generic_email(recipient, subject, body)
    if not success:
        return jsonify({"error": err or "Unable to send email."}), 500
    return jsonify({"message": "Email sent."})


@app.route('/api/notifications/sms', methods=['POST'])
def send_sms_route():
    user, error_response = authenticate_request()
    if error_response:
        payload, status_code = error_response
        return jsonify(payload), status_code

    payload = request.json or {}
    to_number = (payload.get("to") or payload.get("phone") or "").strip()
    body = payload.get("body") or ""
    use_async = str(payload.get("async") or "true").lower() == "true"

    if not to_number:
        return jsonify({"error": "Destination phone number is required."}), 400

    if use_async:
        try:
            task = send_sms_task.delay(to_number, body)
            return jsonify({"taskId": task.id, "status": "queued"}), 202
        except Exception as exc:
            logger.error("queue_sms_failed", extra={"error": str(exc)})
            return jsonify({"error": "Unable to queue SMS."}), 500

    success, err = send_sms_message(to_number, body)
    if not success:
        return jsonify({"error": err or "Unable to send SMS."}), 500
    return jsonify({"message": "SMS sent."})


@app.route('/api/reports/pdf', methods=['POST'])
def generate_pdf_route():
    user, error_response = authenticate_request()
    if error_response:
        payload, status_code = error_response
        return jsonify(payload), status_code

    payload = request.json or {}
    title = payload.get("title") or "Report"
    sections = payload.get("sections") or []
    use_async = str(payload.get("async") or "false").lower() == "true"

    if use_async:
        try:
            task = generate_pdf_task.delay(title, sections)
            return jsonify({"taskId": task.id, "status": "queued"}), 202
        except Exception as exc:
            logger.error("queue_pdf_failed", extra={"error": str(exc)})
            return jsonify({"error": "Unable to queue PDF job."}), 500

    pdf_buffer = pdf_bytesio(title, sections)
    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        download_name=f"{title.replace(' ', '_').lower()}.pdf",
        as_attachment=True,
    )


@app.route('/api/analyze-survey', methods=['POST'])
def analyze_survey():
    if data is None:
        return jsonify({"error": "Data not loaded"}), 500
    
    try:
        # Get the form data from the request
        survey_data = request.json
        
        # Process the survey data without saving
        analysis_results = survey_processor.process_survey(survey_data)
        
        # Generate combined dashboard
        combined_dashboard = survey_processor.generate_combined_dashboard(analysis_results)
        analysis_results["combinedDashboard"] = combined_dashboard
        
        return jsonify({
            "message": "Survey analyzed successfully",
            "analysis": analysis_results
        })
    
    except Exception as e:
        print(f"Error in analyze_survey: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/trait-explanations', methods=['GET'])
def get_trait_explanations():
    """Return trait explanations from the text file"""
    try:
        if os.path.exists('trait_explanations.txt'):
            with open('trait_explanations.txt', 'r') as f:
                explanations = f.read()
            return jsonify({"explanations": explanations})
        else:
            return jsonify({"explanations": "Trait explanations not available"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/get-surveys', methods=['GET'])
def get_surveys():
    global data
    user, error_response = authenticate_request()
    if error_response:
        payload, status_code = error_response
        return jsonify(payload), status_code

    if data is None:
        return jsonify({"error": "Data not loaded"}), 500
    
    try:
        # Reload data to ensure we have the latest
        data = _load_from_known_locations()
        if data is None:
            return jsonify({"error": "Unable to load survey data"}), 500
        
        # Replace NaN values with None (null in JSON) and convert to records
        data = data.replace({pd.NA: None})  # Replace pandas NA
        data = data.where(pd.notnull(data), None)  # Replace numpy NaN
        
        # Convert the data to a list of dictionaries and clean the data
        records = data.to_dict('records')
        if not records:
            return jsonify([])

        # Get last record and clean it
        last_record = records[-1]
        cleaned_record = {}
        for key, value in last_record.items():
            try:
                if pd.isna(value) or value == 'NaN' or value == 'NA':
                    cleaned_record[key] = None
                elif isinstance(value, float) and value.is_integer():
                    cleaned_record[key] = int(value)
                else:
                    cleaned_record[key] = value
            except Exception:
                cleaned_record[key] = value

        # Compute model-based insights for the last record
        try:
            analysis_results = survey_processor.process_survey(cleaned_record)
            # Merge analysis into the response while keeping original keys intact
            cleaned_record["analysis"] = analysis_results
        except Exception as e_analysis:
            print(f"Error computing analysis for last survey: {e_analysis}")
            cleaned_record["analysis"] = {"error": str(e_analysis)}

        # Return only the most recent entry with analysis merged
        return jsonify([cleaned_record])
            
    except Exception as e:
        print(f"Error getting surveys: {e}")
        return jsonify({"error": str(e)}), 500

# Serve React App
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    # Delegate local launches to the import-based runner so `python app.py`
    # uses the same stable module path as other server entrypoints.
    from run_server import main as run_server_main

    run_server_main()
