"""
ingest_2026_clean.py - 全新乾淨版 2026 券商資料匯入 (修正解析與中文字編碼)
核心修正: 
1. 強制使用 cp950 解碼，並讓 psycopg2 以 UTF-8 寫入 PostgreSQL。
2. 允許「非數字」的純中文券商名稱作為 broker_code，避免零筆寫入問題。
"""
import os
import csv
import re
import io
import psycopg2
import psycopg2.extras

DB_CONFIG = {
    "dbname": "stock_db",
    "user": "postgres",
    "password": "1234",
    "host": "localhost",
    "port": "5432",
    "options": "-c client_encoding=UTF8"   # ← 強制 UTF-8 連線
}

FOLDER = r"d:\AI\股票\2026"

def decode_file(path):
    """嘗試以 cp950 解析 TPEX 舊版檔案"""
    with open(path, 'rb') as f:
        raw = f.read()
    for enc in ['cp950', 'big5hkscs', 'utf-8-sig', 'utf-8']:
        try:
            text = raw.decode(enc, errors='strict')
            return text, enc
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode('cp950', errors='replace'), 'cp950(fallback)'

def extract_date_session(filename):
    """從  OTCHOTBRK2026010210.csv  取得 (2026-01-02, 10)"""
    m = re.match(r'OTCHOTBRK(\d{4})(\d{2})(\d{2})(\d{2})\.csv', filename)
    if not m:
        return None, None
    y, mo, d, h = m.groups()
    return f"{y}-{mo}-{d}", int(h)

def main():
    files = sorted(f for f in os.listdir(FOLDER)
                   if f.startswith("OTCHOTBRK") and f.endswith(".csv"))
    if not files:
        print("找不到 OTCHOTBRK*.csv 檔案")
        return

    print(f"==== 2026 券商匯入 (clean) - 共 {len(files)} 個檔案 ====")

    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False

    processed = 0

    for fname in files:
        t_date, s_hour = extract_date_session(fname)
        if not t_date:
            print(f"  ! 跳過 (無法解析日期): {fname}")
            continue

        fpath = os.path.join(FOLDER, fname)
        content, enc = decode_file(fpath)

        inserts = []
        current_sc = None
        
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT stock_code, broker_code,
                           SUM(buy_volume) as pb, SUM(sell_volume) as ps
                    FROM trading_volume
                    WHERE trade_date = %s AND session_time::integer < %s
                    GROUP BY stock_code, broker_code
                """, (t_date, s_hour))
                prev = {(r['stock_code'], str(r['broker_code'])): (r['pb'] or 0, r['ps'] or 0)
                        for r in cur.fetchall()}

                reader = csv.reader(io.StringIO(content))
                for row in reader:
                    line = [x.strip() for x in row if x.strip()]
                    if len(line) < 2:
                        continue

                    # ── 股票列 ──
                    # 格式 e.g. "1", "方土昶(6265)"
                    m_stock = re.search(r'\((\d{4,6})\)', line[1])
                    if line[0].isdigit() and m_stock and len(line) == 2:
                        current_sc = m_stock.group(1).zfill(4)
                        sn = line[1].split('(')[0].strip()
                        cur.execute("""
                            INSERT INTO companies (stock_code, stock_name) VALUES (%s, %s)
                            ON CONFLICT (stock_code) DO UPDATE SET stock_name = EXCLUDED.stock_name
                        """, (current_sc, sn))
                        continue

                    # ── 券商列 ──
                    # 格式 e.g. "1", "元大", "11680", "8727"
                    if current_sc and line[0].isdigit() and len(line) >= 4:
                        b_raw = line[1]
                        m_b = re.match(r'^(\d{4})\s*(.*)', b_raw)
                        if m_b:
                            bc, bn = m_b.groups()
                        else:
                            # 如果沒有找到 4 位數字代號，表示純粹給券商名字（如 TPEX 格式）
                            # 則 broker_code 直接存為中文名稱本身！
                            bc = b_raw.strip()
                            bn = bc

                        bc = bc.strip()
                        if not bc:
                            continue

                        cur.execute("""
                            INSERT INTO brokers (broker_code, broker_name) VALUES (%s, %s)
                            ON CONFLICT (broker_code) DO NOTHING
                        """, (bc, bn))

                        try:
                            cb = int(float(line[2].replace(',', '')))
                            cs = int(float(line[3].replace(',', '')))
                            pb, ps = prev.get((current_sc, bc), (0, 0))
                            db = max(0, cb - pb)
                            ds = max(0, cs - ps)
                            if db > 0 or ds > 0:
                                inserts.append((t_date, s_hour, current_sc, bc, db, ds))
                        except (ValueError, TypeError, IndexError):
                            continue

                if inserts:
                    psycopg2.extras.execute_values(cur, """
                        INSERT INTO trading_volume
                            (trade_date, session_time, stock_code, broker_code, buy_volume, sell_volume)
                        VALUES %s
                        ON CONFLICT (trade_date, session_time, stock_code, broker_code) DO NOTHING
                    """, inserts)

            conn.commit()
            print(f"  ✓ {fname} ({enc}) → 匯入 {len(inserts):,} 筆增量")
            processed += 1

        except Exception as e:
            conn.rollback()
            print(f"  ✗ {fname} 匯入失敗: {e}")

    conn.close()
    print(f"\n✅ 券商主力資料重構完畢！共處理 {processed}/{len(files)} 個檔案")

if __name__ == '__main__':
    main()
