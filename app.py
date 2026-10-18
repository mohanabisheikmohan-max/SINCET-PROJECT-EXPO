
import csv
import io
import os
import secrets
import sqlite3
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv
from flask import (
    Flask, flash, redirect, render_template, request,
    send_file, session, url_for
)
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SESSION_SECRET") or secrets.token_hex(32)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
SQLITE_DB = BASE_DIR / "registrations.db"

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
USE_POSTGRES = DATABASE_URL.startswith(
    ("postgres://", "postgresql://")
)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}

FORM_FIELDS = [
    "team_name",
    "college_name",
    "department",
    "year_of_study",
    "team_leader",
    "member1",
    "member2",
    "topic_name",
    "topic_description",
    "email",
    "phone",
    "transaction_id",
]


# ---------------- DATABASE CONNECTION ----------------

def db():
    if USE_POSTGRES:
        import psycopg
        from psycopg.rows import dict_row

        return psycopg.connect(
            DATABASE_URL,
            sslmode=os.getenv("PGSSLMODE", "require"),
            connect_timeout=15,
            row_factory=dict_row,
        )

    connection = sqlite3.connect(SQLITE_DB, timeout=15)
    connection.row_factory = sqlite3.Row
    return connection


def get_columns(connection):
    if USE_POSTGRES:
        rows = connection.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = 'registrations'
        """).fetchall()
        return {row["column_name"] for row in rows}

    rows = connection.execute(
        "PRAGMA table_info(registrations)"
    ).fetchall()

    return {row["name"] for row in rows}


# ---------------- DATABASE INITIALIZATION ----------------

def init_db():
    connection = db()

    try:
        if USE_POSTGRES:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS registrations (
                    id BIGSERIAL PRIMARY KEY,
                    team_name TEXT,
                    college_name TEXT,
                    department TEXT,
                    year_of_study TEXT,
                    team_leader TEXT,
                    member1 TEXT,
                    member2 TEXT,
                    member_1 TEXT,
                    member_2 TEXT,
                    topic_name TEXT,
                    topic_description TEXT,
                    email TEXT,
                    phone TEXT,
                    transaction_id TEXT,
                    payment_proof TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        else:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS registrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    team_name TEXT,
                    college_name TEXT,
                    department TEXT,
                    year_of_study TEXT,
                    team_leader TEXT,
                    member1 TEXT,
                    member2 TEXT,
                    member_1 TEXT,
                    member_2 TEXT,
                    topic_name TEXT,
                    topic_description TEXT,
                    email TEXT,
                    phone TEXT,
                    transaction_id TEXT,
                    payment_proof TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

        columns_to_add = {
            "team_name": "TEXT",
            "college_name": "TEXT",
            "department": "TEXT",
            "year_of_study": "TEXT",
            "team_leader": "TEXT",
            "member1": "TEXT",
            "member2": "TEXT",
            "member_1": "TEXT",
            "member_2": "TEXT",
            "topic_name": "TEXT",
            "topic_description": "TEXT",
            "email": "TEXT",
            "phone": "TEXT",
            "transaction_id": "TEXT",
            "payment_proof": "TEXT",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        }

        existing = get_columns(connection)

        for column, data_type in columns_to_add.items():
            if column not in existing:
                if USE_POSTGRES:
                    connection.execute(
                        f"ALTER TABLE registrations "
                        f"ADD COLUMN IF NOT EXISTS {column} {data_type}"
                    )
                else:
                    connection.execute(
                        f"ALTER TABLE registrations "
                        f"ADD COLUMN {column} {data_type}"
                    )

        # Keep old and new member column names compatible.
        connection.execute("""
            UPDATE registrations
            SET member1 = COALESCE(member1, member_1),
                member_1 = COALESCE(member_1, member1),
                member2 = COALESCE(member2, member_2),
                member_2 = COALESCE(member_2, member2)
        """)

        connection.commit()

    except Exception:
        connection.rollback()
        app.logger.exception("Database initialization failed")
        raise

    finally:
        connection.close()


# ---------------- HOME PAGE ----------------

@app.route("/")
def index():
    return render_template("index.html")


# ---------------- TEAM REGISTRATION ----------------

@app.post("/register")
def register():
    data = {
        key: request.form.get(key, "").strip()
        for key in FORM_FIELDS
    }

    if any(not value for value in data.values()):
        flash("Please fill in all registration fields.", "error")
        return redirect(url_for("index") + "#register")

    uploaded_file = request.files.get("payment_proof")

    if not uploaded_file or not uploaded_file.filename:
        flash("Please upload your payment proof.", "error")
        return redirect(url_for("index") + "#register")

    original_name = secure_filename(uploaded_file.filename)

    if not original_name or "." not in original_name:
        flash("Please select a valid payment-proof file.", "error")
        return redirect(url_for("index") + "#register")

    extension = original_name.rsplit(".", 1)[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        flash("Only PNG, JPG, JPEG, or PDF files are allowed.", "error")
        return redirect(url_for("index") + "#register")

    filename = f"{secrets.token_hex(8)}_{original_name}"
    saved_path = UPLOAD_DIR / filename

    values = {
        **data,
        "member_1": data["member1"],
        "member_2": data["member2"],
        "payment_proof": filename,
    }

    connection = None
    file_saved = False

    try:
        uploaded_file.save(saved_path)
        file_saved = True

        connection = db()
        available_columns = get_columns(connection)

        insert_columns = [
            column
            for column in values
            if column in available_columns
        ]

        marker = "%s" if USE_POSTGRES else "?"
        placeholders = ", ".join(
            [marker] * len(insert_columns)
        )
        column_sql = ", ".join(insert_columns)
        insert_values = [
            values[column] for column in insert_columns
        ]

        connection.execute(
            f"""
            INSERT INTO registrations ({column_sql})
            VALUES ({placeholders})
            """,
            insert_values,
        )

        connection.commit()
        flash("Registration submitted successfully!", "success")

    except Exception:
        if connection:
            connection.rollback()

        app.logger.exception("Registration could not be saved")

        if file_saved:
            try:
                saved_path.unlink(missing_ok=True)
            except OSError:
                app.logger.warning("Could not remove uploaded file.")

        flash(
            "Registration failed. Please check the server logs.",
            "error",
        )

    finally:
        if connection:
            connection.close()

    return redirect(url_for("index") + "#register")


# ---------------- ADMIN AUTHENTICATION ----------------

def admin_only(view_function):
    @wraps(view_function)
    def wrapped(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))

        return view_function(*args, **kwargs)

    return wrapped


@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        password_hash = os.getenv("ADMIN_PASSWORD_HASH", "")

        if (
            username == os.getenv("ADMIN_USERNAME", "admin")
            and password_hash
            and check_password_hash(password_hash, password)
        ):
            session.clear()
            session["admin"] = True
            return redirect(url_for("dashboard"))

        flash("Login failed. Check your admin credentials.", "error")

    return render_template("admin_login.html")


# ---------------- ADMIN DASHBOARD ----------------

@app.route("/admin/dashboard")
@admin_only
def dashboard():
    connection = db()

    try:
        rows = connection.execute(
            "SELECT * FROM registrations ORDER BY id DESC"
        ).fetchall()
    finally:
        connection.close()

    return render_template("dashboard.html", rows=rows)


# ---------------- PAYMENT PROOF DOWNLOAD ----------------

@app.route("/admin/proof/<path:name>")
@admin_only
def proof(name):
    safe_name = os.path.basename(name)
    path = UPLOAD_DIR / safe_name

    if not path.is_file():
        return (
            "Payment proof not found. The file may no longer exist "
            "on this server.",
            404,
        )

    return send_file(
        path,
        as_attachment=True,
        download_name=safe_name,
    )


# ---------------- CSV EXPORT ----------------

@app.route("/admin/export.csv")
@admin_only
def export():
    connection = db()

    try:
        cursor = connection.execute(
            "SELECT * FROM registrations ORDER BY id DESC"
        )
        rows = cursor.fetchall()
        columns = [item[0] for item in cursor.description]

        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(columns)

        for row in rows:
            writer.writerow([row[column] for column in columns])

        csv_data = output.getvalue().encode("utf-8-sig")

    finally:
        connection.close()

    memory_file = io.BytesIO(csv_data)
    memory_file.seek(0)

    return send_file(
        memory_file,
        mimetype="text/csv; charset=utf-8",
        as_attachment=True,
        download_name="registrations.csv",
    )


# ---------------- LOGOUT ----------------

@app.route("/admin/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ---------------- UPLOAD ERROR ----------------

@app.errorhandler(413)
def upload_too_large(_error):
    flash("File is too large. Maximum size is 5 MB.", "error")
    return redirect(url_for("index") + "#register")


# Initialize the database for local and Render/Gunicorn runs.
init_db()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=False,
    )
