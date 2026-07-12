#!/usr/bin/env python3
"""
Keygen for d4ph1_crackme2

Algorithm (reconstructed from writeup):

PHASE 1: Convert each byte of the name to its 2-char hex ASCII representation.
         e.g. 's'(0x73) -> '7','3'  stored as bytes 0x37, 0x33

PHASE 2: Run-length encode the phase1 result (look-and-say style).
         For each run of identical bytes, emit (count, byte) pairs as WORD values.
         The count and byte are stored as a 16-bit word: (byte << 8) | count
         (based on: SHL EAX,8 ; ADD EDX,EAX ; MOV WORD PTR [EDI+40321C],DX)

PHASE 3: For each WORD in phase2 result, combine with corresponding name byte
         via: serial_byte = (word_value + name_byte - index) transformed to hex ASCII
         The exact ops from disasm: ADD EAX,EBX ; SUB EAX,ECX (ecx is 1-based index)
         Then converted to hex ASCII for the final serial.

NOTE: Phase 3 details are truncated in the writeup. Several ASSUMPTION comments below.
"""

def phase1(name: str) -> bytes:
    """Convert each byte of name to its hex digit ASCII bytes.
    e.g. 's' (0x73) -> b'73'
    """
    result = []
    for ch in name:
        b = ord(ch)
        hi = (b >> 4) & 0xF
        lo = b & 0xF
        # convert nibble to ASCII hex digit
        hi_ascii = hi + 0x30 if hi < 10 else hi + 0x37
        lo_ascii = lo + 0x30 if lo < 10 else lo + 0x37
        result.append(hi_ascii)
        result.append(lo_ascii)
    return bytes(result)


def phase2(data: bytes) -> list:
    """
    Run-length encode (look-and-say) the phase1 data.
    Returns list of (count, byte_value) tuples.
    Each stored as WORD: (byte_value << 8) | count
    """
    if not data:
        return []
    result = []
    i = 0
    while i < len(data):
        current = data[i]
        count = 1
        while i + count < len(data) and data[i + count] == current:
            count += 1
        result.append((count, current))
        i += count
    return result


def phase2_words(data: bytes) -> list:
    """Return list of 16-bit words from phase2 encoding."""
    pairs = phase2(data)
    words = []
    for count, byte_val in pairs:
        # From disasm: SHL EAX,8 (EAX=byte_val) then ADD EDX,EAX (EDX=count)
        word = (byte_val << 8) | (count & 0xFF)
        words.append(word)
    return words


def nibble_to_hex_ascii(n: int) -> int:
    """Convert a nibble (0-15) to its ASCII hex character byte value."""
    n = n & 0xF
    if n < 10:
        return n + 0x30  # '0'-'9'
    else:
        return n + 0x37  # 'A'-'F'


def phase3_and_4(words: list, name: str) -> str:
    """
    ASSUMPTION: Phase 3 computes serial bytes from the phase2 words and name bytes.
    From the truncated disasm:
      ECX starts at 1 (INC ECX before loop)
      ESI starts at 1 (INC ESI before loop)
      BX = WORD PTR [ESI + 0x40321B]  -> word from phase2 result (ESI is word index * 2)
      EAX = MOVSX name_byte at [ECX + 0x403157] -> name[ecx-1] (ECX starts at 1)
      ADD EAX, EBX  -> eax = name_byte + word
      SUB EAX, ECX  -> eax = name_byte + word - ecx
      Then converted to hex ASCII for serial output.

    ASSUMPTION: result is taken modulo 256 then converted to 2 hex ASCII chars.
    ASSUMPTION: loop runs for min(len(words), len(name)) iterations.
    """
    name_bytes = [ord(c) for c in name]
    serial_bytes = []
    loop_count = min(len(words), len(name_bytes))
    for i in range(loop_count):
        ecx = i + 1  # ECX starts at 1
        word = words[i]  # BX = word
        name_byte = name_bytes[i] if i < len(name_bytes) else 0  # EAX = name_byte
        # ASSUMPTION: full word (16-bit) is used in ADD
        val = (name_byte + word - ecx) & 0xFFFF
        # ASSUMPTION: convert to 2 hex ASCII chars
        hi = (val >> 4) & 0xF
        lo = val & 0xF
        serial_bytes.append(nibble_to_hex_ascii(hi))
        serial_bytes.append(nibble_to_hex_ascii(lo))
    return bytes(serial_bytes).decode('ascii', errors='replace')


def compute_serial(name: str) -> str:
    p1 = phase1(name)
    words = phase2_words(p1)
    serial = phase3_and_4(words, name)
    return serial


def keygen(name: str) -> str:
    """Generate serial for given name."""
    if len(name) <= 4 or len(name) >= 0x21:
        raise ValueError("Name must be between 5 and 32 characters (exclusive).")
    return compute_serial(name)


def verify(name: str, serial: str) -> bool:
    """
    ASSUMPTION: verification checks that the entered serial matches
    the computed serial (case-insensitive or exact match).
    """
    if len(name) <= 4 or len(name) >= 0x21:
        return False
    expected = compute_serial(name)
    return serial.upper() == expected.upper()



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
