import hashlib
import base64
import struct

# ASSUMPTION: The registry value for CPU MHz is machine-specific.
# For keygen purposes we need to either know it or treat it as a parameter.
# The algorithm uses it in str4 calculation.

def generate_hash(source_text: str) -> str:
    """
    Replicates VB.NET GenerateHash:
    Uses UnicodeEncoding (UTF-16 LE) to get bytes, then MD5, then Base64.
    """
    encoded = source_text.encode('utf-16-le')
    md5 = hashlib.md5(encoded).digest()
    return base64.b64encode(md5).decode('ascii')


def verify(name: str, serial: str, cpu_mhz: int = 1000) -> bool:
    """
    Verify a serial for a given name.
    cpu_mhz: the value from HKLM\HARDWARE\DESCRIPTION\SYSTEM\CentralProcessor\0 ~Mhz
             ASSUMPTION: defaults to 1000 since we can't read the registry here.
    """
    generated = keygen(name, cpu_mhz)
    return serial == generated


def keygen(name: str, cpu_mhz: int = 1000) -> str:
    """
    Generate a serial for a given name and CPU MHz.
    
    Steps (from VB source):
    1. Convert name chars to ASCII codes, build string in REVERSE order.
    2. MD5-hash that string (UTF-16LE encoded) -> base64 string (sourceText).
    3. Compute str (hash1), str2 (hash2), str3 (hash3) from specific offsets.
    4. Compute str4 (hash4) using cpu_mhz.
    5. Insert str2, str3, str4, and sourceText.Length into sourceText at specific positions.
    6. Extract substrings and reorder to form serial.
    """
    text = name
    length = len(text)
    
    # Step 1: build sourceText as reversed ASCII codes concatenated
    # Loop: sourceText = Asc(text[num]) & sourceText  (prepend each char's ASCII)
    source_text = ""
    for num in range(length):
        source_text = str(ord(text[num])) + source_text
    
    # Step 2: MD5 hash -> base64
    source_text = generate_hash(source_text)
    # source_text is now a 24-char base64 string (MD5 = 16 bytes -> 24 base64 chars)
    
    # Step 3: Extract hash components
    # VB Substring(startIndex) returns the substring starting at startIndex to end
    # Python equivalent: source_text[index:]
    
    # str = CDbl((((Asc(sourceText.Substring(sourceText.Length - 15)) - 3) + 4.5) * 2))
    # sourceText.Length for a 24-char base64: index = 24 - 15 = 9
    # Substring returns string starting at index 9, Asc takes first char
    idx1 = len(source_text) - 15
    char1 = ord(source_text[idx1])  # Asc of first char of substring
    str1_val = float(((char1 - 3) + 4.5) * 2)
    str1 = str(str1_val)
    # VB CDbl then ToString - for integer results this gives e.g. "203.0" or "203"
    # ASSUMPTION: VB CDbl->ToString on a whole number gives the integer representation
    # Actually VB Conversions.ToString(CDbl(...)) on a whole double gives integer string
    if str1_val == int(str1_val):
        str1 = str(int(str1_val))
    
    # str2 = CDbl((((Asc(sourceText.Substring(sourceText.Length - 10)) - 4) + 4) * 3))
    idx2 = len(source_text) - 10
    char2 = ord(source_text[idx2])
    str2_val = float(((char2 - 4) + 4) * 3)
    str2 = str(str2_val)
    if str2_val == int(str2_val):
        str2 = str(int(str2_val))
    
    # str3 = CDbl((((Asc(sourceText.Substring(sourceText.Length - 20)) - 5) + 11) * 5))
    idx3 = len(source_text) - 20
    char3 = ord(source_text[idx3])
    str3_val = float(((char3 - 5) + 11) * 5)
    str3 = str(str3_val)
    if str3_val == int(str3_val):
        str3 = str(int(str3_val))
    
    # str4 = CDbl(((cpu_mhz + (str3_val - str1_val)) - 1000))
    str4_val = float((float(cpu_mhz) + (str3_val - str1_val)) - 1000)
    str4 = str(str4_val)
    if str4_val == int(str4_val):
        str4 = str(int(str4_val))
    
    # Step 5: Insert into sourceText
    # sourceText = sourceText.Insert(4, "-" & str2 & "-")
    #                         .Insert(0x10, "-")
    #                         .Insert(0x19, "-" & str3 & "-")
    # Then:
    # sourceText = sourceText.Insert(30, Conversions.ToString(sourceText.Length))
    #                         .Insert(13, "-" & str4 & "-")
    
    def insert_at(s, pos, ins):
        return s[:pos] + ins + s[pos:]
    
    source_text = insert_at(source_text, 4, "-" + str2 + "-")
    source_text = insert_at(source_text, 0x10, "-")
    source_text = insert_at(source_text, 0x19, "-" + str3 + "-")
    source_text = insert_at(source_text, 30, str(len(source_text)))
    source_text = insert_at(source_text, 13, "-" + str4 + "-")
    
    # Step 6: Extract substrings
    str8 = source_text[0:9]
    str9 = source_text[9:18]          # 9 chars starting at 9
    str10 = source_text[0x12:0x12+8]  # 8 chars starting at 18
    str11 = source_text[0x1A:]        # from 26 to end
    
    # Final serial
    serial = str8 + str9 + str11 + str10
    return serial



# ===== standardized CLI (auto-added) =====
def _cli_norm(_x):
    if isinstance(_x, bytes):
        return _x.hex()
    if isinstance(_x, (list, tuple)):
        return " ".join(_cli_norm(_i) for _i in _x)
    return str(_x)


def _cli_main():
    import sys
    _SAMPLE = ['alice', 'bob', 'Kevin', 'test123', 'admin', 'crackme', 'john_doe', 'w1nner', 'root', 'dragon']
    argv = sys.argv[1:]
    mode = argv[0] if argv else ""
    if mode == "keygen":
        n = 0
        for _nm in _SAMPLE:
            _s = None
            for _call in (lambda: keygen(_nm), lambda: keygen()):
                try:
                    _s = _call()
                    break
                except TypeError:
                    continue
                except Exception:
                    _s = None
                    break
            if _s is None:
                continue
            _sv = _cli_norm(_s)
            print(_nm, _sv)
            n += 1
            if n >= 10:
                break
    elif mode == "verify":
        try:
            print("1" if verify(*argv[1:]) else "0")
        except Exception:
            print("0")
    else:
        sys.stderr.write("usage: {} {{keygen|verify <args>}}\n".format(sys.argv[0]))
        sys.exit(2)


if __name__ == "__main__":
    _cli_main()
