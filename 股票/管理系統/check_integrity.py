import csv, io, os, psycopg2, psycopg2.extras

DB_CONFIG = {
    "dbname": "stock_db",
    "user": "postgres",
    "password": "1234",
    "host": "localhost",
    "port": "5432",
    "options": "-c client_encoding=UTF8"
}

FOLDER = r"d:\AI\股票\2026"
TEST_DATE = "2026-04-08"
TEST_STOCK = "1815"

def get_db_vols():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT session_time, broker_code, buy_volume, sell_volume 
        FROM trading_volume 
        WHERE trade_date = %s AND stock_code = %s
        ORDER BY session_time
    """, (TEST_DATE, TEST_STOCK))
    rows = cur.fetchall()
    conn.close()
    
    # Aggregate DB totals by broker
    db_aggs = {}
    for r in rows:
        bc = r['broker_code']
        db_aggs.setdefault(bc, {'buy': 0, 'sell': 0})
        db_aggs[bc]['buy'] += r['buy_volume']
        db_aggs[bc]['sell'] += r['sell_volume']
        
    return db_aggs

def decode_file(path):
    with open(path, 'rb') as f:
        raw = f.read()
    return raw.decode('utf-8-sig', errors='replace')

def get_csv_vols():
    # Read the final session file for the day: OTCHOTBRK2026040813.csv
    # Because TPEX files are cumulative, the 13:00 file has the final total for the day
    files = [f for f in os.listdir(FOLDER) if f.startswith(f"OTCHOTBRK{TEST_DATE.replace('-','')}13")]
    if not files:
        return {}
    
    path = os.path.join(FOLDER, files[0])
    lines = decode_file(path).splitlines()
    
    csv_aggs = {}
    current_sc = None
    
    reader = csv.reader(lines)
    for row in reader:
        line = [x.strip() for x in row if x.strip()]
        if len(line) < 2:
            continue
            
        import re
        m_stock = re.search(r'\((\d{4,6})\)', line[1])
        if line[0].isdigit() and m_stock and len(line) == 2:
            current_sc = m_stock.group(1).zfill(4)
            continue
            
        if current_sc == TEST_STOCK and line[0].isdigit() and len(line) >= 4:
            b_raw = line[1]
            m_b = re.match(r'^(\d{4})\s*(.*)', b_raw)
            if m_b:
                bc, bn = m_b.groups()
            else:
                bc = b_raw.strip()
                
            cb = int(float(line[2].replace(',', '')))
            cs = int(float(line[3].replace(',', '')))
            
            csv_aggs[bc] = {'buy': cb, 'sell': cs}
            
    return csv_aggs

def compare():
    db_aggs = get_db_vols()
    csv_aggs = get_csv_vols()
    
    print(f"Comparison for Stock {TEST_STOCK} on {TEST_DATE}")
    print("-" * 50)
    all_brokers = set(list(db_aggs.keys()) + list(csv_aggs.keys()))
    
    for bc in all_brokers:
        db_b = db_aggs.get(bc, {}).get('buy', 0)
        db_s = db_aggs.get(bc, {}).get('sell', 0)
        csv_b = csv_aggs.get(bc, {}).get('buy', 0)
        csv_s = csv_aggs.get(bc, {}).get('sell', 0)
        
        diff_b = db_b - csv_b
        diff_s = db_s - csv_s
        
        if diff_b != 0 or diff_s != 0:
            print(f"❌ MISMATCH: Broker '{bc}'")
            print(f"      DB: Buy={db_b}, Sell={db_s}")
            print(f"     CSV: Buy={csv_b}, Sell={csv_s}")
        else:
            if db_b > 0 or db_s > 0:
                print(f"✅ MATCH: Broker '{bc}' (Buy={db_b}, Sell={db_s})")

if __name__ == "__main__":
    compare()
