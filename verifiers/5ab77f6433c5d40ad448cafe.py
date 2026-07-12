def genproc1(data: bytes, static: int) -> bytes:
    """
    For each byte b in data:
      start with eax=1
      loop 0x9d (157) times: eax = eax * b  (16-bit, ax)
      while ax > static: ax -= static
      result byte = al (low byte of ax)
    """
    result = bytearray()
    for b in data:
        ax = 1
        for _ in range(0x9d):
            ax = ax * b
            # keep as 16-bit after multiply but only subtract static while > static
            while ax > static:
                ax -= static
        result.append(ax & 0xFF)
    return bytes(result)


def genproc2(data: bytes) -> int:
    """
    For each byte b in data: total += (b XOR 0x7F)
    Returns total as a 32-bit value (but stored in a word in original; we keep full int).
    """
    total = 0
    for b in data:
        total += (b ^ 0x7F)
    return total


# Character tables (as defined in the source)
TEK_ORIG  = b"2349aeghijmprsuvyzCDEFJKLMNQTVWXY"
CIFT_ORIG = b"015678bcdfklnoqtxwABGHIOPRSUZ"


def verify(name: str, serial: str) -> bool:
    """
    Verification reconstructed from the tuto.html writeup:
    PART 1: For each char c in (coded_name): name_total += (c XOR 0x7F)
    PART 2: For each char c in serial:        serial_total += c  (direct, no XOR)
    Check: name_total == serial_total

    But wait -- GenProc1 is called on szName with constant 0DDh BEFORE GenProc2.
    So GenProc2 receives the CODED name bytes, not the raw name.
    Similarly the serial chars are added directly (no XOR).

    Reproduce exactly:
      1. coded_name = genproc1(name_bytes, 0xDD)
      2. name_result = genproc2(coded_name)   # sum of (byte XOR 0x7F)
      3. serial_result = sum of raw serial bytes (no XOR, direct add)
      Compare name_result == serial_result
    """
    name_bytes = name.encode('latin-1')
    if len(name_bytes) < 4:
        return False
    coded_name = genproc1(name_bytes, 0xDD)
    name_result = genproc2(coded_name)

    serial_bytes = serial.encode('latin-1')
    serial_result = sum(serial_bytes)

    return name_result == serial_result


def keygen(name: str) -> str:
    """
    Key generation algorithm (from the keygen source in the writeup):

    1. Compute name_result (as in verify)
    2. Transform the character tables using GenProc1 with constant 0xFD:
         tek1  = genproc1(TEK_ORIG,  0xFD)
         cift1 = genproc1(CIFT_ORIG, 0xFD)
       These become the 'weight' tables.
       The original tek/cift remain as the output character tables.
    3. Build serial:
       eax = name_result
       esi = 0 (serial output index)
       edi = 0 (index into current table)
       loop:
         if eax == 0: done
         edx = eax & 0x0F
         # reduce edx: while edx > 1: edx -= 2  => edx becomes 0 or 1
         while edx > 1:
             edx -= 2
         # choose table based on odd(1) or even(0)
         if edx == 1:  # odd
             weight_table = tek1
             char_table   = TEK_ORIG
         else:         # even
             weight_table = cift1
             char_table   = CIFT_ORIG
         # get weight at current index
         if edi >= len(weight_table) or weight_table[edi] == 0:
             return None  # 'Not Found! Change The Name'
         w = weight_table[edi]
         if eax >= w:
             eax -= w
             serial += char_table[edi]
             esi += 1
             edi = 0
         else:
             edi += 1
         goto loop
    """
    name_bytes = name.encode('latin-1')
    if len(name_bytes) < 4:
        raise ValueError("Name must be at least 4 characters")

    coded_name = genproc1(name_bytes, 0xDD)
    eax = genproc2(coded_name)  # name_result

    tek1  = genproc1(TEK_ORIG,  0xFD)
    cift1 = genproc1(CIFT_ORIG, 0xFD)

    serial_chars = []
    edi = 0

    while eax != 0:
        edx = eax & 0x0F
        # reduce edx to 0 or 1
        while edx > 1:
            edx -= 2

        if edx == 1:  # odd
            weight_table = tek1
            char_table   = TEK_ORIG
        else:          # even
            weight_table = cift1
            char_table   = CIFT_ORIG

        if edi >= len(weight_table):
            # ASSUMPTION: if we run out of table entries, generation fails
            raise ValueError("Not Found! Change The Name")

        w = weight_table[edi]
        if w == 0:
            raise ValueError("Not Found! Change The Name (zero weight)")

        if eax >= w:
            eax -= w
            serial_chars.append(chr(char_table[edi]))
            edi = 0
        else:
            edi += 1

    return ''.join(serial_chars)



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
