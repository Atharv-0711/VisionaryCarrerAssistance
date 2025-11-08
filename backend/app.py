from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import pandas as pd
import os
import sys
import sqlite3
from datetime import datetime
import smtplib
from email.message import EmailMessage
from uuid import uuid4
from werkzeug.security import generate_password_hash, check_password_hash
from typing import Optional, Tuple, Set
import json
import hashlib
import matplotlib

matplotlib.use("Agg")

# Import analysis modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import sentiment_analysis_rolemodels as rolemodels
import sentiment_analysis_background as background
import sentiment_analysis_behavoralimpact as behavioral
import sentiment_analysis_family_income as income
import survey_processor
from config import settings

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


app = Flask(__name__)
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    supports_credentials=True,
    allow_headers=["Content-Type", "X-Auth-Token", "Authorization"],
)  # Enable CORS for all routes with custom auth header support
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variable declaration
global data
data = None


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
                    full_name TEXT NOT NULL,
                    unique_code TEXT NOT NULL UNIQUE,
                    age INTEGER,
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


def generate_api_token() -> str:
    return uuid4().hex


def generate_student_code() -> str:
    return uuid4().hex[:8].upper()


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


def serialize_student(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "full_name": row["full_name"],
        "unique_code": row["unique_code"],
        "age": row["age"],
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

def _candidate_paths(filename: str):
    app_dir = os.path.dirname(os.path.abspath(__file__))
    cwd = os.getcwd()
    return [
        os.path.join(app_dir, filename),
        os.path.join(cwd, filename),
    ]


def _load_from_known_locations():
    """Try to load Excel first, then CSV from several likely paths."""
    excel_candidates = _candidate_paths('Childsurvey.xlsx')
    csv_candidates = _candidate_paths('Childsurvey.csv')

    # Try Excel
    for path in excel_candidates:
        if os.path.exists(path):
            try:
                df = pd.read_excel(path, sheet_name=0)
                print(f"Data loaded from Excel: {path} with {len(df)} records")
                return df
            except Exception as e:
                print(f"Failed reading Excel at {path}: {e}")

    # Try CSV (utf-8 then latin-1)
    for path in csv_candidates:
        if os.path.exists(path):
            for enc in ("utf-8", "latin1"):
                try:
                    df = pd.read_csv(path, encoding=enc)
                    print(f"Data loaded from CSV: {path} (encoding={enc}) with {len(df)} records")
                    return df
                except Exception as e:
                    print(f"Failed reading CSV at {path} (encoding={enc}): {e}")

    return None


def load_initial_data():
    global data
    data = _load_from_known_locations()
    if data is None:
        print("No initial data loaded. Place Childsurvey.xlsx or Childsurvey.csv in the backend directory.")

# Load data once at startup
load_initial_data()
init_surveys_table()
seed_surveys_from_dataframe(data)
init_auth_db()
init_assessments_db()

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "data_loaded": data is not None})


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

    class_level = (payload.get('class_level') or '').strip() or None
    guardian_contact = (payload.get('guardian_contact') or '').strip() or None
    additional_info = (payload.get('additional_info') or '').strip() or None

    code = generate_student_code()
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
                    full_name,
                    unique_code,
                    age,
                    class_level,
                    guardian_contact,
                    additional_info,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user["id"],
                    full_name,
                    code,
                    age,
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


@app.route('/api/students/<int:student_id>', methods=['GET'])
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

    return jsonify(serialize_student(row))


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
def get_background_analysis():
    if data is None:
        return jsonify({"error": "Data not loaded"}), 500
    
    try:
        # Get include_details parameter (default to True for backward compatibility)
        include_details = request.args.get('include_details', 'true').lower() == 'true'
        
        # Get full results
        results = background.get_background_sentiment(data)
        
        # Remove background_details if not needed
        if not include_details and 'background_details' in results:
            del results['background_details']
        
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analysis/behavioral', methods=['GET'])
def get_behavioral_analysis():
    if data is None:
        return jsonify({"error": "Data not loaded"}), 500
    
    try:
        results = behavioral.analyze_behavioral_impact(data)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analysis/rolemodel', methods=['GET'])
def get_rolemodel_analysis():
    if data is None:
        return jsonify({"error": "Data not loaded"}), 500
    
    try:
        results = rolemodels.analyze_role_model(data)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analysis/income', methods=['GET'])
def get_income_analysis():
    if data is None:
        return jsonify({"error": "Data not loaded"}), 500
    
    try:
        results = income.get_income_sentiment(data)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analysis/complete', methods=['GET'])
def get_complete_analysis():
    # If not loaded yet, attempt to load; otherwise respond with empty analysis
    global data
    if data is None:
        load_initial_data()

    # Get include_details parameter (default to false to exclude background details)
    include_details = request.args.get('include_details', 'false').lower() == 'true'

    if data is None or len(data) == 0:
        empty_resp = {
            "background": {},
            "behavioral": {},
            "rolemodel": {},
            "income": {},
            "totalSurveys": 0
        }
        return jsonify(empty_resp)

    try:
        bg = background.get_background_sentiment(data)
        if not include_details and 'background_details' in bg:
            del bg['background_details']

        beh = behavioral.analyze_behavioral_impact(data)
        rm = rolemodels.analyze_role_model(data)
        inc = income.get_income_sentiment(data)

        return jsonify({
            "background": bg,
            "behavioral": beh,
            "rolemodel": rm,
            "income": inc,
            "totalSurveys": len(data)
        })
    except Exception as e:
        print(f"complete analysis error: {e}")
        # Return safe default instead of 500 so frontend can still render
        return jsonify({
            "background": {},
            "behavioral": {},
            "rolemodel": {},
            "income": {},
            "totalSurveys": len(data) if data is not None else 0
        })

@app.route('/api/analysis/complete-summary', methods=['GET'])
def get_complete_summary():
    """New endpoint that returns all analyses without detailed background data"""
    if data is None:
        return jsonify({"error": "Data not loaded"}), 500
    
    try:
        # Get background results
        background_results = background.get_background_sentiment(data)
        
        # Always remove background_details
        if 'background_details' in background_results:
            del background_results['background_details']
        
        behavioral_results = behavioral.analyze_behavioral_impact(data)
        rolemodel_results = rolemodels.analyze_role_model(data)
        income_results = income.get_income_sentiment(data)
        
        return jsonify({
            "background": background_results,
            "behavioral": behavioral_results,
            "rolemodel": rolemodel_results,
            "income": income_results,
            "totalSurveys": len(data)
        })
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/submit-survey', methods=['POST'])
def submit_survey():
    global data
    user, error_response = authenticate_request()
    if error_response:
        payload, status_code = error_response
        return jsonify(payload), status_code

    if data is None:
        return jsonify({"error": "Data not loaded"}), 500
    
    try:
        # Get the form data from the request
        survey_data = request.json or {}
        if not isinstance(survey_data, dict):
            return jsonify({"error": "Invalid survey payload."}), 400

        student_id_raw = survey_data.pop("studentId", None)
        student_id = None
        if student_id_raw not in (None, ""):
            try:
                student_id_value = int(student_id_raw)
            except (ValueError, TypeError):
                return jsonify({"error": "Invalid student identifier."}), 400

            student_row = get_student_for_user(student_id_value, user["id"])
            if student_row is None:
                return jsonify({"error": "Student not found."}), 404
            student_id = student_row["id"]
        
        # Process the survey data and get analysis results
        analysis_results = survey_processor.process_and_save_survey(survey_data)
        created_at = analysis_results.get("timestamp") or datetime.utcnow().isoformat()

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
                        json.dumps(survey_data),
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
        
        # Return the analysis results
        response = {
            "message": "Survey submitted and analyzed successfully",
            "analysis": analysis_results,
            "assessmentId": assessment_id,
            "studentId": student_id,
        }

        # Emit real-time update to all connected clients
        socketio.emit('survey_submitted', {
            'analysis': analysis_results,
            'totalSurveys': len(data)
        })



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

    response_payload = {
        "id": row["id"],
        "created_at": row["created_at"],
        "survey_data": _parse_json_column(row["survey_data"]) or {},
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
    socketio.run(app, host='0.0.0.0', debug=True, port=5000)
