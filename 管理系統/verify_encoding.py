"""
verify_encoding.py - 驗證資料庫中的中文名稱是否正確
寫入 UTF-8 檔案避免 Windows terminal 顯示問題
"""
import psycopg2
DB = {'dbname':'stock_db','user':'postgres','password':'1234','host':'localhost','port':'5432','options':'-c client_encoding=UTF8'}

raw = b'\xb4\x49\xb3\xec'  # 富喬 in cp950
decoded = raw.decode('cp950')

with open('encode_test.txt', 'w', encoding='utf-8') as f:
    f.write(f"cp950 decode result: {decoded}\n")
    f.write(f"Expected: 富喬\n")
    f.write(f"Match: {decoded == '富喬'}\n")

print("Result written to encode_test.txt")
print("Match:", decoded == '富喬')
