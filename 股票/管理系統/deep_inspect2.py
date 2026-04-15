"""
deep_inspect2.py - 找出 b4 49 b3 ec 的真正 Unicode 對應
不使用 print，直接寫入 UTF-8 文件
"""
result_lines = []

# The raw bytes for the stock name area: b4 49 b3 ec
test_bytes = bytes([0xb4, 0x49, 0xb3, 0xec])

result_lines.append(f"Test bytes: {test_bytes.hex()}\n")

# Try all relevant encodings and write result to file
for enc in ['cp950', 'big5', 'big5hkscs', 'ms950']:
    try:
        decoded = test_bytes.decode(enc, errors='strict')
        codepoints = [hex(ord(c)) for c in decoded]
        result_lines.append(f"[{enc}] decoded: {decoded!r}  codepoints: {codepoints}\n")
    except Exception as e:
        result_lines.append(f"[{enc}] ERROR: {e}\n")

# Key question: what IS 富 and 喬 in cp950?
fu_qiao = "富喬"
for enc in ['cp950', 'big5', 'big5hkscs']:
    try:
        encoded = fu_qiao.encode(enc)
        result_lines.append(f"富喬 encoded in [{enc}]: {encoded.hex()}  bytes: {list(encoded)}\n")
    except Exception as e:
        result_lines.append(f"富喬 encode [{enc}] ERROR: {e}\n")

with open('deep_inspect2.txt', 'w', encoding='utf-8') as f:
    f.writelines(result_lines)

print("Done. Check deep_inspect2.txt")
