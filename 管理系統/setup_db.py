import psycopg2
from config import load_config

def setup_database():
    c = load_config()
    # connect to postgres root to create db
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user=c["db_user"],
            password=c["db_password"],
            host=c["db_host"],
            port=c["db_port"]
        )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'stock_db'")
        if not cur.fetchone():
            cur.execute("CREATE DATABASE stock_db")
        cur.close()
        conn.close()
    except Exception as e:
        return False, f"Failed to connect and create database: {e}"

    # setup tables
    try:
        conn = psycopg2.connect(
            dbname=c["db_name"],
            user=c["db_user"],
            password=c["db_password"],
            host=c["db_host"],
            port=c["db_port"]
        )
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                stock_code VARCHAR(20) PRIMARY KEY,
                stock_name VARCHAR(100)
            );
            CREATE TABLE IF NOT EXISTS brokers (
                broker_code VARCHAR(20) PRIMARY KEY,
                broker_name VARCHAR(100)
            );
            CREATE TABLE IF NOT EXISTS trading_volume (
                id SERIAL PRIMARY KEY,
                trade_date DATE,
                session_time VARCHAR(10),
                stock_code VARCHAR(20) REFERENCES companies(stock_code),
                broker_code VARCHAR(20) REFERENCES brokers(broker_code),
                buy_volume BIGINT DEFAULT 0,
                sell_volume BIGINT DEFAULT 0,
                UNIQUE(trade_date, session_time, stock_code, broker_code)
            );
            CREATE TABLE IF NOT EXISTS stock_prices_3104 (
                id SERIAL PRIMARY KEY,
                trade_date DATE,
                stock_code VARCHAR(20) REFERENCES companies(stock_code),
                close_price NUMERIC,
                open_price NUMERIC,
                high_price NUMERIC,
                low_price NUMERIC,
                trade_shares BIGINT,
                trade_amount BIGINT,
                trade_transactions BIGINT,
                UNIQUE(trade_date, stock_code)
            );
            CREATE TABLE IF NOT EXISTS disposal_stocks (
                id SERIAL PRIMARY KEY,
                stock_code VARCHAR(20),
                date_start DATE,
                date_end DATE,
                condition_desc TEXT,
                UNIQUE(stock_code, date_start, date_end)
            );
            CREATE TABLE IF NOT EXISTS attention_stocks (
                id SERIAL PRIMARY KEY,
                stock_code VARCHAR(20),
                attention_date DATE,
                reason TEXT,
                UNIQUE(stock_code, attention_date)
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        return True, "Database initialized successfully"
    except Exception as e:
        return False, f"Failed to setup tables: {e}"
