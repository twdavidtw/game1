"""
check_true_name.py - Find what the bytes of 富喬 actually are in cp950
and compare with what's in the file  
"""

# What does 富喬 encode to?
fu_qiao = "富喬"
encoded = fu_qiao.encode('cp950')
result = [
    f"富喬 in cp950 = {encoded.hex()} = bytes {list(encoded)}\n"
]

# Now check ALL lines with (1815) from the file
fpath = r'd:\AI\股票\2026\OTCHOTBRK2026010210.csv'
with open(fpath, 'rb') as f:
    raw = f.read()

for line in raw.split(b'\r\n'):
    if b'1815' in line:
        result.append(f"Line hex: {line.hex()}\n")
        # The name bytes are between the first quote group and (1815)
        # Format seems to be: "3","NAME(1815)"
        # Find bytes before (1815)
        idx = line.find(b'1815')
        if idx > 5:
            name_area = line[4:idx-1]  # skip past "3","
            result.append(f"Name area hex: {name_area.hex()}\n")
            result.append(f"Name area bytes: {list(name_area)}\n")
            for enc in ['cp950', 'big5hkscs']:
                try:
                    decoded = name_area.decode(enc, errors='replace')
                    result.append(f"  [{enc}]: {decoded!r}\n")
                except Exception as e:
                    result.append(f"  [{enc}] ERROR: {e}\n")
        break

# Also check what stock 1815 should be — user said "富喬"
fu_bytes = "富喬".encode('cp950')
result.append(f"\n富 = U+5BCC, 喬 = U+55AC\n")
result.append(f"cp950 bytes for 富喬: {fu_bytes.hex()}\n")

# Compare - what is in the file vs what 富喬 encodes to?
file_name_bytes = bytes([0xb4, 0x49, 0xb3, 0xec])
result.append(f"\nFile bytes:  {file_name_bytes.hex()}\n")
result.append(f"富喬 bytes:  {fu_bytes.hex()}\n")
result.append(f"Match: {file_name_bytes == fu_bytes}\n")

# So what DO the file bytes decode to?
result.append(f"\nFile bytes decoded cp950: {file_name_bytes.decode('cp950')!r}\n")
result.append(f"That is U+{ord(file_name_bytes.decode('cp950')[0]):04X} U+{ord(file_name_bytes.decode('cp950')[1]):04X}\n")

with open('check_true_name.txt', 'w', encoding='utf-8') as f:
    f.writelines(result)
print("Done: check check_true_name.txt")
