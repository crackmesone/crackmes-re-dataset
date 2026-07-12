# Reconstruction of tno_trial3 keygen algorithm
# Based on writeup by stan4oo and MASM keygen by Ousir
#
# Algorithm overview:
# 1. Lowercase the name
# 2. XOR each byte of szstr2 ("3TLNAOITR3TLNAO") with all bytes of name cyclically
# 3. Apply Mix() to name (reverse + extend to 15 bytes)
# 4. XOR result of step 2 with extended name (step 3)
# 5. Convert 15 bytes -> 120 bits table (LSB first per byte)
# 6. Pack bits 5-at-a-time -> 24 bytes (values 0-31)
# 7. Map through szstr3 lookup table
# 8. RSA-8bit encrypt each byte: byte^17 mod 0x81
# 9. Format as hex string

import textwrap

SZSTR2 = b"3TLNAOITR3TLNAO"  # 15 bytes
SZSTR3 = b"N3MVK28PBWDAG7J9F6QT1HRUZXSCYE45"  # 32 chars
RSA_E = 0x11  # 17
RSA_N = 0x81  # 129

def mix(name_bytes):
    """Reverse the string, then if shorter than 15, extend by repeating cyclically to 15 bytes.
    From the writeup: last char becomes first, first becomes second, etc.
    Example: 'TNOTRIAL3' -> '3LAIRTONT' -> extended to 15 by cycling
    Wait - writeup says 'TNOTRIAL3' -> '3TLNAOITR3TLNAO'
    Let's figure out the pattern:
    Original: T N O T R I A L 3
    Reversed: 3 L A I R T O N T
    But result is:  3 T L N A O I T R 3 T L N A O
    Hmm, that doesn't match simple reversal.
    Looking at the MASM keygen Mix function more carefully:
    The writeup says 'last char becomes first, first becomes second'
    For 'TNOTRIAL3' (9 chars) -> '3TLNAOITR' (9 chars reversed-interleaved?)
    Actually: T(0)N(1)O(2)T(3)R(4)I(5)A(6)L(7)3(8)
    Result:   3 T L N A O I T R
    It looks like: index 8,0,7,1,6,2,5,3,4 - take from ends alternating?
    Last, First, Last-1, Second, Last-2, Third...
    pos0=8='3', pos1=0='T', pos2=7='L', pos3=1='N', pos4=6='A', pos5=2='O', pos6=5='I', pos7=3='T', pos8=4='R'
    YES! That matches '3TLNAOITR'
    """
    n = len(name_bytes)
    result = bytearray()
    lo, hi = 0, n - 1
    toggle = 1  # start with hi
    while lo <= hi:
        if toggle:
            result.append(name_bytes[hi])
            hi -= 1
        else:
            result.append(name_bytes[lo])
            lo += 1
        toggle ^= 1
    # Extend to 15 bytes by cycling
    out = bytearray(15)
    for i in range(15):
        out[i] = result[i % len(result)]
    return out

def powmod_rsa8(base, exp, mod):
    """Modular exponentiation as implemented in the crackme (standard)."""
    return pow(base, exp, mod)

def keygen(name):
    name_lower = name.lower().encode('latin-1')
    name_len = len(name_lower)
    if name_len == 0:
        return None
    
    # Step 1: Start with szstr2, XOR each position with all name bytes cyclically (fold all name bytes into each position)
    str2 = bytearray(SZSTR2)
    for i in range(15):
        al = str2[i]
        for j in range(name_len):
            al ^= name_lower[j]
        str2[i] = al
    
    # Step 2: Mix the name and extend to 15 bytes
    name_mixed = mix(name_lower)
    
    # Step 3: XOR str2 result with mixed name
    for i in range(15):
        str2[i] ^= name_mixed[i]
    
    # Step 4: Build bit table - 15 bytes x 8 bits = 120 bits, LSB first
    table = []
    for i in range(15):
        byte_val = str2[i]
        for bit in range(8):
            table.append((byte_val >> bit) & 1)
    
    # Step 5: Pack bits 5-at-a-time into 24 bytes (values 0-31)
    # From MASM: for each group of 5 bits, accumulate with doubling multiplier
    serial = bytearray(24)
    bit_idx = 0
    for i in range(24):
        val = 0
        mult = 1
        for b in range(5):
            if table[bit_idx]:
                val += mult
            mult *= 2
            bit_idx += 1
        serial[i] = val & 0xFF
    
    # Step 6: Map through szstr3
    for i in range(24):
        serial[i] = SZSTR3[serial[i] % len(SZSTR3)]
    
    # Step 7: RSA-8bit encrypt: each byte = byte^0x11 mod 0x81
    for i in range(24):
        serial[i] = powmod_rsa8(serial[i], RSA_E, RSA_N)
    
    # Step 8: Format as hex, 6 dwords bswapped
    result = ''
    for i in range(6):
        dword = (serial[i*4] << 24) | (serial[i*4+1] << 16) | (serial[i*4+2] << 8) | serial[i*4+3]
        # bswap then convert to hex
        bswapped = ((dword & 0xFF) << 24) | (((dword >> 8) & 0xFF) << 16) | (((dword >> 16) & 0xFF) << 8) | ((dword >> 24) & 0xFF)
        result += f'{bswapped:08X}'
    
    return result

def verify(name, serial):
    expected = keygen(name)
    if expected is None:
        return False
    return serial.upper().replace('-','').replace(' ','') == expected.upper()


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
