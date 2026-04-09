import os
import glob
import psycopg2
from config import load_config
from datetime import datetime

def get_db_connection():
    c = load_config()
    return psycopg2.connect(
        dbname=c["db_name"],
        user=c["db_user"],
        password=c["db_password"],
        host=c["db_host"],
        port=c["db_port"]
    )

def parse_roc_date(roc_str):
    # e.g. "115/04/08" -> "2026-04-08"
    if not roc_str or '/' not in roc_str:
        return None
    try:
        parts = roc_str.split('/')
        y = int(parts[0]) + 1911
        m = int(parts[1])
        d = int(parts[2])
        return f"{y}-{m:02d}-{d:02d}"
    except Exception:
        return None

def extract_dates(date_range_str):
    # e.g. "115/04/09~115/04/22"
    if '~' in date_range_str:
        s, e = date_range_str.split('~')
        return parse_roc_date(s.strip()), parse_roc_date(e.strip())
    return parse_roc_date(date_range_str), parse_roc_date(date_range_str)

def ingest_aux_data():
    conn = get_db_connection()
    conn.autocommit = True
    cur = conn.cursor()

    folder = r'd:\\AI\\股票\\輔助資料'
    
    print("==== 匯入處置股與注意股資料 ====")
    for filename in os.listdir(folder):
        filepath = os.path.join(folder, filename)
        if not filename.endswith('.csv'): continue
        
        try:
            with open(filepath, 'r', encoding='cp950', errors='replace') as f:
                lines = f.readlines()
        except:
            print(f"Failed to read {filename}")
            continue

        if 'disposal' in filename:
            # Disposal logic
            print(f"處理處置股: {filename}")
            data_started = False
            for line in lines:
                line = line.strip()
                if not line: continue
                parts = [p.strip().strip('"').strip() for p in line.split('","')]
                if len(parts) == 1:
                    parts = [p.strip().strip('"').strip() for p in line.split(',')]
                
                if len(parts) > 0 and parts[0] == '序號':
                    data_started = True
                    continue
                if not data_started: continue
                # cols: 序號, 日期, 股票代號, 股票名稱, 處置起迄時間, 處置條件...
                if len(parts) >= 6 and parts[0].isdigit():
                    stock_code = parts[2]
                    date_range = parts[4]
                    condition_desc = parts[5]
                    
                    s_date, e_date = extract_dates(date_range)
                    if s_date and e_date:
                        cur.execute('''INSERT INTO disposal_stocks (stock_code, date_start, date_end, condition_desc)
                                       VALUES (%s, %s, %s, %s)
                                       ON CONFLICT (stock_code, date_start, date_end) DO NOTHING''',
                                    (stock_code, s_date, e_date, condition_desc))
                        cur.execute("INSERT INTO companies (stock_code, stock_name) VALUES (%s, %s) ON CONFLICT (stock_code) DO NOTHING", 
                                    (stock_code, parts[3]))
                                    
        elif 'attention' in filename:
            # Attention logic
            print(f"處理注意股: {filename}")
            data_started = False
            for line in lines:
                line = line.strip()
                if not line: continue
                parts = [p.strip().strip('"').strip() for p in line.split('","')]
                if len(parts) == 1:
                    parts = [p.strip().strip('"').strip() for p in line.split(',')]
                
                if len(parts) > 0 and parts[0] == '序號':
                    data_started = True
                    continue
                if not data_started: continue
                # cols: 序號, 股票代號, 股票名稱, 注意條件, 日期(公布日)
                if len(parts) >= 5 and parts[0].isdigit():
                    stock_code = parts[1]
                    reason = parts[3]
                    att_date = parse_roc_date(parts[4])
                    if att_date:
                        cur.execute('''INSERT INTO attention_stocks (stock_code, attention_date, reason)
                                       VALUES (%s, %s, %s)
                                       ON CONFLICT (stock_code, attention_date) DO NOTHING''',
                                    (stock_code, att_date, reason))
                        cur.execute("INSERT INTO companies (stock_code, stock_name) VALUES (%s, %s) ON CONFLICT (stock_code) DO NOTHING", 
                                    (stock_code, parts[2]))

    cur.close()
    conn.close()
    print("==== 輔助資料匯入完成 ====")
    
if __name__ == '__main__':
    ingest_aux_data()
