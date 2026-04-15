"""
debug_csv.py - 診斷 CSV 解析的實際情況
"""
import csv, io

fpath = r'd:\AI\股票\2026\OTCHOTBRK2026010210.csv'

with open(fpath, 'rb') as f:
    raw = f.read()

content = raw.decode('cp950', errors='replace')
lines = content.splitlines()

results = []
results.append(f"Total lines: {len(lines)}\n")
results.append("=" * 60 + "\n")

# Show first 20 raw lines
for i, ln in enumerate(lines[:20]):
    results.append(f"Line {i}: {repr(ln[:100])}\n")

results.append("\n" + "=" * 60 + "\n")
results.append("CSV PARSED (first 20 data rows):\n")

reader = csv.reader(io.StringIO(content))
count = 0
for row in reader:
    if count >= 20:
        break
    line = [x.strip() for x in row if x.strip()]
    if len(line) < 1:
        continue
    results.append(f"  cols={len(line)} line[0]={repr(line[0])} | " + 
                   " | ".join(repr(x[:30]) for x in line[:5]) + "\n")
    count += 1

with open('debug_csv.txt', 'w', encoding='utf-8') as f:
    f.writelines(results)

print("Done: check debug_csv.txt")
