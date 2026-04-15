import os
import glob
import psycopg2
import psycopg2.extras
from config import load_config
import re

def get_db_connection():
    c = load_config()
    return psycopg2.connect(
        dbname=c["db_name"],
        user=c["db_user"],
        password=c["db_password"],
        host=c["db_host"],
        port=c["db_port"]
    )

def parse_roc_date_from_filename(filename):
    # Example: RSTA3104_1150102.csv
    match = re.search(r'RSTA3104_(\d{3})(\d{2})(\d{2})\.csv', filename, re.IGNORECASE)
    if match:
        y, m, d = match.groups()
        gregorian_y = int(y) + 1911
        return f"{gregorian_y}-{m}-{d}"
    return None

def safe_float(val):
    val = val.strip().replace(',', '')
    try:
        return float(val)
    except:
        return None

def safe_int(val):
    val = val.strip().replace(',', '')
    try:
        return int(val)
    except:
        return None

def ingest_all_3104():
    print("==== 開始讀取股價3104資料 ====")
    conn = get_db_connection()
    conn.autocommit = True
    cur = conn.cursor()
    
    file_pattern = r'd:\AI\股票\股價3104\RSTA3104_*.csv'
    files = sorted(glob.glob(file_pattern))
    
    print(f"共找到 {len(files)} 個 CSV 檔案，準備處理...")
    
    for filepath in files:
        filename = os.path.basename(filepath)
        trade_date = parse_roc_date_from_filename(filename)
        if not trade_date:
            continue
            
        print(f"正在處理: {filename} (日期: {trade_date})")
        batch_inserts = []
        
        try:
            with open(filepath, 'r', encoding='cp950', errors='replace') as f:
                lines = f.readlines()
                
            data_started = False
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                parts = [p.strip().strip('"').strip() for p in line.split('","')]
                if len(parts) == 1:
                    parts = [p.strip().strip('"').strip() for p in line.split(',')]
                
                if len(parts) > 0 and parts[0] == '代號':
                    data_started = True
                    continue
                    
                if not data_started:
                    continue
                    
                if len(parts) >= 11 and parts[0] != '':
                    stock_code = parts[0]
                    # Ensure stock_code is registered (OTC companies may have been listed)
                    # For a safer approach, upsert company if missing (usually not needed if 2026 inserts it, but let's be safe)
                    cur.execute("INSERT INTO companies (stock_code, stock_name) VALUES (%s, %s) ON CONFLICT (stock_code) DO NOTHING", 
                                (stock_code, parts[1]))

                    close_price = safe_float(parts[2])
                    open_price = safe_float(parts[4])
                    high_price = safe_float(parts[5])
                    low_price = safe_float(parts[6])
                    trade_shares = safe_int(parts[8])
                    trade_amount = safe_int(parts[9])
                    trade_transactions = safe_int(parts[10])
                    
                    batch_inserts.append((
                        trade_date, stock_code, close_price, open_price,
                        high_price, low_price, trade_shares, trade_amount, trade_transactions
                    ))
                    
        except Exception as e:
            print(f"解析檔案發生錯誤 {filepath}: {e}")
            
        if batch_inserts:
            try:
                psycopg2.extras.execute_values(
                    cur,
                    """INSERT INTO stock_prices_3104 
                       (trade_date, stock_code, close_price, open_price, high_price, low_price, trade_shares, trade_amount, trade_transactions)
                       VALUES %s 
                       ON CONFLICT (trade_date, stock_code) DO NOTHING""",
                    batch_inserts,
                    page_size=2000
                )
            except Exception as e:
                print(f"資料庫寫入發生錯誤 {filename}: {e}")

    cur.close()
    conn.close()
    print("\n==== 3104股價資料匯入完成！ ====")

if __name__ == '__main__':
    ingest_all_3104()
