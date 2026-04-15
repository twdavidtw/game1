import psycopg2, psycopg2.extras

DB = {'dbname':'stock_db','user':'postgres','password':'1234','host':'localhost','port':'5432','options':'-c client_encoding=UTF8'}
conn = psycopg2.connect(**DB)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

cur.execute('SELECT COUNT(*) as cnt FROM trading_volume')
total = cur.fetchone()['cnt']

cur.execute("SELECT COUNT(*) as cnt FROM trading_volume WHERE stock_code='1815'")
s1815 = cur.fetchone()['cnt']

cur.execute("SELECT COUNT(*) as cnt FROM companies WHERE stock_name IS NOT NULL")
co_names = cur.fetchone()['cnt']

cur.execute("SELECT COUNT(*) as cnt FROM brokers WHERE broker_name IS NOT NULL")
br_names = cur.fetchone()['cnt']

cur.execute("SELECT stock_name FROM companies WHERE stock_code='1815'")
row = cur.fetchone()
name_1815 = row['stock_name'] if row else 'NOT FOUND'

cur.execute("SELECT broker_code, broker_name FROM brokers LIMIT 5")
brokers = [(r['broker_code'], r['broker_name']) for r in cur.fetchall()]
conn.close()

with open('verify_result.txt', 'w', encoding='utf-8') as f:
    f.write(f"trading_volume total: {total}\n")
    f.write(f"1815 volume records: {s1815}\n")
    f.write(f"companies with names: {co_names}\n")
    f.write(f"brokers with names: {br_names}\n")
    f.write(f"1815 name repr: {repr(name_1815)}\n")
    f.write(f"1815 name display: {name_1815}\n")
    for bc, bn in brokers:
        f.write(f"broker: {repr(bc)} -> {repr(bn)}\n")

print("Written to verify_result.txt")
