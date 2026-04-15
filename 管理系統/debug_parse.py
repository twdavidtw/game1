"""
debug_parse.py - 精確診斷一個CSV檔案的解析情況，寫入UTF-8結果
"""
import csv, io, re, psycopg2

fpath = r'd:\AI\股票\2026\OTCHOTBRK2026010210.csv'

with open(fpath, 'rb') as f:
    raw = f.read()

content = raw.decode('cp950', errors='replace')
reader = csv.reader(io.StringIO(content))

results = []
stock_rows = 0
broker_rows = 0
inserted = 0
current_sc = None
inserts = []

for row in reader:
    line = [x.strip() for x in row if x.strip()]
    if len(line) < 2:
        continue

    m_stock = re.search(r'\((\d{4,6})\)', line[1])
    if line[0].isdigit() and m_stock and len(line) == 2:
        current_sc = m_stock.group(1).zfill(4)
        sn = line[1].split('(')[0].strip()
        stock_rows += 1
        if len(results) < 5:
            results.append(f"STOCK: code={current_sc} name={repr(sn)}\n")
        continue

    if current_sc and line[0].isdigit() and len(line) >= 4:
        b_raw = line[1]
        m_b = re.match(r'^(\d{4})\s*(.*)', b_raw)
        if m_b:
            bc, bn = m_b.groups()
            bc = bc.strip()
        else:
            bc = b_raw[:4].strip()
            bn = b_raw[4:].strip()

        broker_rows += 1
        if broker_rows <= 3:
            results.append(f"BROKER raw line[1]={repr(b_raw)} -> bc={repr(bc)} isdigit={bc.isdigit()}\n")

        if not bc.isdigit():
            continue

        try:
            cb = int(float(line[2].replace(',', '')))
            cs = int(float(line[3].replace(',', '')))
            db = max(0, cb)
            ds = max(0, cs)
            if db > 0 or ds > 0:
                inserts.append((current_sc, bc, bn, db, ds))
                inserted += 1
        except Exception as e:
            results.append(f"  ERROR: {e} line={line[:4]}\n")

results.insert(0, f"stock_rows={stock_rows} broker_rows={broker_rows} would_insert={inserted}\n")

with open('debug_parse.txt', 'w', encoding='utf-8') as f:
    f.writelines(results)
    if inserts:
        f.write(f"\nFirst 3 inserts:\n")
        for row in inserts[:3]:
            f.write(f"  {row}\n")

print(f"Done: stock={stock_rows} broker={broker_rows} insert={inserted}")
print("Check debug_parse.txt")
