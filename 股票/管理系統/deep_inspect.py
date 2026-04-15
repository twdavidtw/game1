"""
deep_inspect.py - 直接分析 CSV 原始位元，找出股票名稱的正確編碼
"""
import re

fpath = r'd:\AI\股票\2026\OTCHOTBRK2026010210.csv'

with open(fpath, 'rb') as f:
    raw = f.read()

# 找包含 (1815) 的行
for line in raw.split(b'\r\n'):
    if b'1815' in line:
        print("Raw hex:", line.hex())
        print("Raw bytes:", list(line))
        # 嘗試各種編碼
        for enc in ['cp950', 'big5', 'big5hkscs', 'utf-8', 'latin-1', 'gb2312', 'gbk', 'euc_tw']:
            try:
                txt = line.decode(enc, errors='replace')
                print(f"  [{enc}]: {txt.strip()}")
            except Exception as e:
                print(f"  [{enc}]: ERROR {e}")
        print()
        break
