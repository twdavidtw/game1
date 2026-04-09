import pandas as pd
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

def load_master_data():
    broker_df = pd.read_excel(r'd:\AI\股票\共用資料\證券商基本資料.xls')
    broker_map = {}
    for _, row in broker_df.iterrows():
        code = str(row.iloc[0]).strip()
        name = str(row.iloc[1]).strip()
        broker_map[name] = code
        
    company_df = pd.read_excel(r'd:\AI\股票\共用資料\OCT上櫃公司列表.xlsx')
    company_map = {}
    for _, row in company_df.iterrows():
        code_str = str(row.iloc[0]).split()[0]
        code_int = str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else ''
        code = code_int if code_int else code_str.strip()
        name = str(row.iloc[0]).split()[-1].strip() if ' ' in str(row.iloc[0]) else ''
        company_map[code] = name
        
    return broker_map, company_map

def extract_date_session(filename):
    match = re.search(r'OTCHOTBRK(\d{4})(\d{2})(\d{2})(\d{2})\.csv', filename, re.IGNORECASE)
    if match:
        y, m, d, session = match.groups()
        return f"{y}-{m}-{d}", session
    return None, None

def detect_and_read_lines(filepath):
    # Detect BOM for UTF-8 files, else use cp950
    with open(filepath, 'rb') as f:
        raw_head = f.read(3)
        
    if raw_head == b'\xef\xbb\xbf':
        encoding = 'utf-8-sig'
    else:
        encoding = 'cp950'
        
    with open(filepath, 'r', encoding=encoding, errors='ignore') as f:
        return f.readlines()

def ingest_all():
    print("==== 載入主檔字典庫 ====")
    broker_map, company_map = load_master_data()
    
    conn = get_db_connection()
    conn.autocommit = True
    cur = conn.cursor()
    
    print("==== 清除歷史有亂碼的資料 ====")
    cur.execute("DELETE FROM trading_volume")
    cur.execute("DELETE FROM brokers")
    print("資料庫 trading_volume, brokers 已清空完成，準備重新匯入。")
    
    file_pattern = r'd:\AI\股票\2026\OTCHOTBRK*.csv'
    files = sorted(glob.glob(file_pattern))
    
    print(f"共找到 {len(files)} 個 CSV 檔案，準備處理...")
    
    accumulated = {} 
    
    cur.execute("SELECT stock_code FROM companies")
    inserted_companies = {row[0] for row in cur.fetchall()}
    inserted_brokers = set()

    for filepath in files:
        filename = os.path.basename(filepath)
        trade_date, session_time = extract_date_session(filename)
        if not trade_date:
            continue
            
        print(f"正在處理: {filename} (日期: {trade_date}, 時段: {session_time})")
        
        if trade_date not in accumulated:
            accumulated[trade_date] = {}
        
        daily_accumulated = accumulated[trade_date]
        
        current_stock_code = None
        current_stock_name = None
        batch_inserts = {}
        
        try:
            lines = detect_and_read_lines(filepath)
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split('","')
                if len(parts) == 1:
                    parts = line.split(',')
                parts = [p.strip().strip('"').strip() for p in parts]
                    
                if len(parts) >= 2 and parts[0].isdigit():
                    if len(parts) == 2:
                        match = re.search(r'(.*?)\((.*?)\)', parts[1])
                        if match:
                            current_stock_name = match.group(1).strip()
                            current_stock_code = match.group(2).strip()
                        else:
                            current_stock_name = parts[1]
                            current_stock_code = parts[1]
                            
                        if current_stock_code not in inserted_companies:
                            cur.execute("INSERT INTO companies (stock_code, stock_name) VALUES (%s, %s) ON CONFLICT (stock_code) DO NOTHING", 
                                        (current_stock_code, current_stock_name))
                            inserted_companies.add(current_stock_code)
                            
                    elif len(parts) >= 4 and current_stock_code:
                        broker_name = parts[1]
                        buy_vol = int(parts[2].replace(',', ''))
                        sell_vol = int(parts[3].replace(',', ''))
                        
                        broker_code = broker_map.get(broker_name, broker_name) 
                        
                        if broker_code not in inserted_brokers:
                            cur.execute("INSERT INTO brokers (broker_code, broker_name) VALUES (%s, %s) ON CONFLICT (broker_code) DO NOTHING",
                                        (broker_code, broker_name))
                            inserted_brokers.add(broker_code)
                            
                        stock_dict = daily_accumulated.setdefault(current_stock_code, {})
                        prev_buy, prev_sell = stock_dict.get(broker_code, (0, 0))
                        
                        session_buy = max(0, buy_vol - prev_buy)
                        session_sell = max(0, sell_vol - prev_sell)
                        
                        stock_dict[broker_code] = (buy_vol, sell_vol)
                        
                        if session_buy > 0 or session_sell > 0:
                            key = (trade_date, session_time, current_stock_code, broker_code)
                            if key in batch_inserts:
                                b, s = batch_inserts[key]
                                batch_inserts[key] = (b + session_buy, s + session_sell)
                            else:
                                batch_inserts[key] = (session_buy, session_sell)
        except Exception as e:
            print(f"解析檔案發生錯誤 {filepath}: {e}")
            
        if batch_inserts:
            try:
                # convert dict back to list for execute_values
                insert_data = [(k[0], k[1], k[2], k[3], v[0], v[1]) for k, v in batch_inserts.items()]
                psycopg2.extras.execute_values(
                    cur,
                    "INSERT INTO trading_volume (trade_date, session_time, stock_code, broker_code, buy_volume, sell_volume) VALUES %s ON CONFLICT (trade_date, session_time, stock_code, broker_code) DO UPDATE SET buy_volume = trading_volume.buy_volume + EXCLUDED.buy_volume, sell_volume = trading_volume.sell_volume + EXCLUDED.sell_volume",
                    insert_data,
                    page_size=2000
                )
            except Exception as e:
                print(f"資料庫寫入發生錯誤 {filename}: {e}")

    cur.close()
    conn.close()
    print("\n==== 所有資料匯入完成！ ====")

if __name__ == '__main__':
    ingest_all()
