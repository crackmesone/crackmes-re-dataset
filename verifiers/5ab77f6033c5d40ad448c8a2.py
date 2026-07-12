import struct
import ctypes

# Memory layout (simulated as Python bytearray/lists)
# byte_402300: 0xFF bytes of 0x30
# byte_4023FF: 0x30
# byte_402400: 16 bytes of 0
# dword_401FA9 = 0x0A0B0C0D
# hashsn: 8 dwords = 32 bytes
# _szvalidsn: 20 dwords = 80 bytes

MASK = 0xFFFFFFFF

def u8(v):
    return v & 0xFF

def _sanitize_string(buf):
    """
    sub_40111E: walk bytes; if < 0x20, add 0x45 and store; if > 0x7E, add 0xBA (i.e. -0x46 mod 256) and store.
    Modifies buf in-place (bytearray).
    Returns the last computed eax (not really used outside).
    """
    eax = 0
    i = 0
    while i < len(buf):
        al = buf[i]
        if al == 0:
            break
        if al < 0x20:
            eax = (eax + 0x45) & 0xFF
            buf[i] = eax
            i += 1
        elif al > 0x7E:
            eax = (eax + 0xBA) & 0xFF  # 0xFFFFFFBA truncated to byte = 0xBA
            buf[i] = eax
            i += 1
        else:
            eax = al
            i += 1
    return eax

def _sanitize_szvalidsn(buf):
    """
    loc_4011DD loop: if < 0x20, add 0x30; if > 0x7E, add 0xD0.
    """
    i = 0
    while i < len(buf):
        al = buf[i]
        if al == 0:
            break
        if al < 0x20:
            buf[i] = u8(al + 0x30)
            i += 1
        elif al > 0x7E:
            buf[i] = u8(al + 0xD0)
            i += 1
        else:
            i += 1

def generate(name: str, org: str):
    """
    Python reimplementation of the _generate procedure from gene.asm.
    Returns the serial as a string.
    """
    # --- Step 1: Initialize byte_402300 (0xFF bytes of 0x30) ---
    # byte_402300[0..0xFE] = 0x30, byte_4023FF = 0x30
    # Total addressable: indices 0..0xFF (256 bytes at 0x402300..0x4023FF)
    # We model the writable region as 512 bytes for safety
    region = bytearray(0x200)  # enough
    # byte_402300 starts at offset 0, byte_4023FF at offset 0xFF
    for i in range(0x100):
        region[i] = 0x30

    name_bytes = name.encode('latin-1') + b'\x00'
    org_bytes = org.encode('latin-1') + b'\x00'

    # --- Step 2: For each char in name, set region[char_value] = 0x31 ---
    # loc_4010B9: eax = name[i], region[eax] = 0x31
    # (using eax as index into byte_402300)
    for b in name_bytes:
        if b == 0:
            break
        idx = b  # eax = char value
        if idx < len(region):
            region[idx] = 0x31

    # --- Step 3: For each char in org, NOT the char, use as index into region starting at 0xFF ---
    # esi = offset byte_4023FF = region[0xFF]
    # eax = org[i], not eax, region[not_eax + 0xFF relative... ]
    # ASSUMPTION: not eax uses only low 8 bits (not al), index = (~al & 0xFF) relative to byte_4023FF (offset 0xFF)
    # but memory wraps. We'll model it as: region[0xFF + (~b & 0xFF)] but clamp to region size
    for b in org_bytes:
        if b == 0:
            break
        idx_val = (~b) & 0xFF  # not eax (low byte)
        abs_idx = 0xFF + idx_val
        if abs_idx < len(region):
            region[abs_idx] = 0x31

    # --- Step 4: Walk byte_402300 (region[0..]), count positions, build hashsn ---
    # hashsn: 8 bytes (8 dword slots, but only byte-sized values stored)
    # ecx counts position (increments for 0x30 AND 0x31)
    # when byte == 0x31, store ecx into hashsn[esi++]
    # ASSUMPTION: hashsn stores bytes (cl), not dwords; esi advances by 1
    hashsn = bytearray(8)
    ecx = 0  # cl = 0
    esi = 0  # index into hashsn
    edi = 0  # index into region (byte_402300)
    while True:
        al = region[edi]
        if al == 0:
            break
        if al == 0x30:
            ecx = (ecx + 1) & 0xFF
            edi += 1
        elif al == 0x31:
            ecx = (ecx + 1) & 0xFF
            if esi < 8:
                hashsn[esi] = ecx
                esi += 1
            edi += 1
        else:
            # other value: just increment and continue
            # ASSUMPTION: non-0x30/0x31 bytes also increment ecx
            ecx = (ecx + 1) & 0xFF
            edi += 1

    # --- Step 5: call sub_40111E twice on hashsn (as a bytearray buffer) ---
    # sub_40111E sanitizes bytes in-place
    hashsn_buf = bytearray(hashsn) + b'\x00'  # null-terminated
    _sanitize_string(hashsn_buf)
    _sanitize_string(hashsn_buf)  # called twice (pop edi; call sub_40111E; call sub_40111E)

    # After the two sanitize calls, pop edi restored edi = offset hashsn
    # --- Step 6: sub_401178 with szname and szorg as eax ---
    # sub_401178: stores eax into [edi], [edi+4], [edi+8], [edi+12]
    # Called with edi=szname, eax=0 then edi=szorg, eax=0 (xor eax,eax before each call... but eax is set)
    # ASSUMPTION: eax after sanitize calls = last computed eax value; but code does xor eax,eax before first call
    # Actually: mov edi, offset _szname; xor eax, eax; call sub_401178
    # Then: mov edi, offset _szorg; call sub_401178 (eax still 0 or last from sub_401178?)
    # sub_401178 doesn't modify eax, so still 0 for both.
    # This zeroes out _szname[0..15] and _szorg[0..15] -- but we don't need those for the serial.
    # (They are separate buffers from hashsn_buf)

    # --- Step 7: XOR each non-zero dword in hashsn with dword_401FA9 (0x0A0B0C0D) ---
    # hashsn is 8 dwords (32 bytes), _szvalidsn = hashsn + 0x20 offset
    # [edi+0x20] = eax ^ esi, where esi = 0x0A0B0C0D
    MAGIC = 0x0A0B0C0D
    # Build hashsn as 8 dwords from hashsn_buf
    # ASSUMPTION: hashsn bytes are used as 4-byte little-endian dwords
    szvalidsn = bytearray(0x50)  # 20 dwords = 80 bytes
    hashsn_dwords = []
    for i in range(8):
        # Read 4 bytes from hashsn_buf
        chunk = bytes(hashsn_buf[i*4:(i*4)+4]).ljust(4, b'\x00')
        dw = struct.unpack_from('<I', chunk)[0]
        hashsn_dwords.append(dw)

    # loc_4011C8: for each dword in hashsn, if non-zero, xor with MAGIC, store at [edi+0x20]
    szvalidsn_dwords = []
    for dw in hashsn_dwords:
        if dw == 0:
            break
        xored = dw ^ MAGIC
        szvalidsn_dwords.append(xored)

    # Pack into szvalidsn buffer
    out_buf = bytearray()
    for dw in szvalidsn_dwords:
        out_buf += struct.pack('<I', dw)
    out_buf += b'\x00'

    # --- Step 8: sanitize _szvalidsn (loc_4011DD loop) ---
    out_sanitized = bytearray(out_buf)
    _sanitize_szvalidsn(out_sanitized)

    # Decode to string (latin-1)
    result = ''
    for b in out_sanitized:
        if b == 0:
            break
        result += chr(b)
    return result


def verify(name: str, serial: str) -> bool:
    """
    Verify by regenerating the serial and comparing.
    ASSUMPTION: The crackme checks the serial against the generated one.
    """
    expected = generate(name, '')  # org is not passed to verify in the original interface
    # ASSUMPTION: serial comparison is exact string match
    return serial == expected


def keygen(name: str, org: str = 'org') -> str:
    """Generate a valid serial for the given name and org."""
    return generate(name, org)



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
