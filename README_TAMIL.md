# INNOVATE TECH 2K26 — Python Flask

## Windows-ல் முதலில் இயக்குவது
1. ZIP-ஐ Extract All செய்யவும்.
2. Python 3.10+ நிறுவியிருக்க வேண்டும். PowerShell-ல் `python --version` பார்க்கவும்.
3. `run_windows.bat` double-click செய்யவும்; அல்லது PowerShell-ல் `python -m venv .venv`, ` .\.venv\Scripts\Activate.ps1`, `pip install -r requirements.txt`, `copy .env.example .env`, `python app.py` இயக்கவும்.
4. `http://127.0.0.1:5000` திறக்கவும். Local test-க்கு SQLite தானாக உருவாகும்.

## Admin password
1. PowerShell-ல் `python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your-own-strong-password'))"` இயக்கவும். Command-ல் உள்ள password-ஐ உங்கள் சொந்த strong password-ஆல் மாற்றவும்.
2. கிடைக்கும் hash-ஐ `.env`-ல் `ADMIN_PASSWORD_HASH=` பிறகு paste செய்யவும்; `SESSION_SECRET`-ஐ நீளமான random secret-ஆல் மாற்றவும்.
3. Server restart செய்து `http://127.0.0.1:5000/admin` திறக்கவும். Username default `admin`.

## Supabase இணைப்பு
1. முதலில் local SQLite version-ஐ test செய்யுங்கள்.
2. Supabase-ல் Connect > connection string/URI தேர்வு செய்யவும். Supabase தரும் PostgreSQL URI-ஐ உங்கள் PC-ல் மட்டும் `.env`-இன் `DATABASE_URL=`-ல் வைக்கவும். Password-ஐ chat-ல் அனுப்ப வேண்டாம்.
3. `.env`-இல் `DATABASE_URL`-க்கு PostgreSQL URI அமைத்தால் app psycopg வழியாக Supabase-ஐ பயன்படுத்தும். `PGSSLMODE=require` வைத்திருக்கவும். Connection URL-ஐ screenshot/chat-ல் பகிர வேண்டாம். Supabase project-ல் Connect வழியாக URI-ஐ எடுத்து, password-ஐ உங்கள் PC-ல் மட்டும் சேர்க்கவும். Password-ல் special characters இருந்தால் URL-encode செய்ய வேண்டியிருக்கலாம்.

## Features
HTML/CSS/JavaScript frontend, Flask backend, 3 team members, topic + description, contact, transaction ID, payment proof upload, admin-only dashboard, CSV export. Poster `static/images/event-poster.png`-ல் உள்ளது.

**Payment QR சேர்க்கப்படவில்லை** — சரியான QR image இந்த package-ல் இல்லை. Public deployment முன் HTTPS, CSRF protection, secure cookies, rate limiting மற்றும் file storage-ஐ configure செய்ய வேண்டும். `.env`, `registrations.db`, `uploads/`-ஐ GitHub-க்கு upload செய்ய வேண்டாம்.
