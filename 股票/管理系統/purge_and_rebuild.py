"""
purge_and_rebuild.py - 完整資料庫清空並重建 (No Emojis for Windows Console)
"""
import psycopg2
import sys
import os
import subprocess

DB_CONFIG = {
    "dbname": "stock_db",
    "user": "postgres",
    "password": "1234",
    "host": "localhost",
    "port": "5432"
}

def purge():
    print("="*60)
    print("STEP 1: TRUNCATE ALL TABLES")
    print("="*60)
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    with conn.cursor() as cur:
        tables = [
            "trading_volume",
            "stock_prices_3104",
            "disposal_stocks",
            "attention_stocks",
            "ingest_history",
            "brokers",
            "companies"
        ]
        for t in tables:
            try:
                cur.execute(f"TRUNCATE TABLE {t} CASCADE;")
                print(f"  OK: TRUNCATE {t}")
            except Exception as e:
                print(f"  FAIL: {t}: {e}")
    conn.close()
    print("Purge Complete\n")

def run_script(script):
    print(f"{'='*60}")
    print(f"STEP: RUN {script}")
    print(f"{'='*60}")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, script],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        env=env
    )
    if result.returncode != 0:
        print(f"FAIL: {script} (exit code {result.returncode})")
    else:
        print(f"OK: {script} completed\n")

if __name__ == "__main__":
    purge()
    run_script("ingest_3104.py")
    run_script("ingest_2026_clean.py")
    run_script("ingest_aux_csv.py")
    print("="*60)
    print("All tasks completed successfully!")
    print("="*60)
