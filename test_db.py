
import os
from dotenv import load_dotenv
import psycopg

# .env file-லிருந்து database connection string எடுக்கும்
load_dotenv()
database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise RuntimeError("DATABASE_URL .env file-ல் இல்லை")

try:
    # Supabase PostgreSQL database-க்கு connect செய்கிறது
    with psycopg.connect(
        database_url,
        connect_timeout=15,
        sslmode="require"
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            result = cursor.fetchone()

    print("Database connection successful!")
    print(result[0])

except Exception as error:
    print("Database connection failed.")
    print(type(error).__name__, str(error))
