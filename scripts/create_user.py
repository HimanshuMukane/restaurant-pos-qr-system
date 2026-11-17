# tools/input_user_pg.py
import os
from datetime import datetime
import getpass
import bcrypt
import psycopg
from psycopg.errors import UniqueViolation
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise SystemExit("Set DATABASE_URL in .env (e.g. postgresql://pos_user:secret@localhost:5432/pos_db)")

VALID_ROLES = {"admin", "cashier", "waiter", "viewer"}

def input_user():
    username = input("username (kecil, tanpa spasi): ").strip().lower()
    full_name = input("nama penuh: ").strip()
    role = input("Role (admin/cashier/waiter/viewer): ").strip().lower()

    if not username or " " in username:
        print("username invalid")
        return
    if role not in VALID_ROLES:
        print("role invalid")
        return

    pw1 = getpass.getpass("Password: ")
    pw2 = getpass.getpass("Tulis lagi: ")
    if pw1 != pw2:
        print("password ga sama")
        return

    pw_hash = bcrypt.hashpw(pw1.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    created_at = datetime.now().isoformat()

    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO public.users (username, full_name, password_hash, role, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (username, full_name, pw_hash, role, created_at),
                )
        print(f"user '{username}' added successfully")
    except UniqueViolation:
        print("username udah ada")
    except Exception as e:
        print("gagal menambah user:", e)

if __name__ == "__main__":
    input_user()
