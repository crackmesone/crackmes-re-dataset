# crackmechaise1 keygen / verifier (PARTIAL reconstruction)
# Based on the solution writeup by alex_ls
#
# What is known:
#   1. Name length must be 4..10 (strictly: len > 3 and len <= 10)
#   2. Every name character must be in range 0x30..0x7A
#   3. A 'XOR buffer' is derived from the name characters using a multiply-by-
#      0x66666667 / sar-edx-2 trick (i.e. integer division by 10, essentially)
#   4. A 'char buffer' is derived from GetLocalTime (day, month, year) plus
#      some arithmetic – the writeup was truncated before the full details.
#   5. The serial chars are produced by XORing char_buffer[i] ^ xor_buffer[i],
#      then adjusting the result to avoid certain byte ranges:
#        if 0x20 < result < 0x30  -> result += 0x20
#        if 0x39 < result <= 0x40 -> result += 0x14
#        if 0x5A < result <= 0x60 -> result += 0x0F
#   6. Serial length == len(xor_buffer) which is computed during the XOR-buffer
#      init loop (exact formula unknown; writeup truncated).
#
# ASSUMPTION: The XOR buffer is built as follows:
#   For each character c in name:
#     digit = (c * 0x66666667) >> 34  (signed)  -- divide c by 10, integer
#     xor_buf.append(digit & 0xFF)
#   (This is a guess at what 'imul 66666667h / sar edx,2' does per character;
#    the real loop body was only partially shown.)
#
# ASSUMPTION: The char buffer is derived from GetLocalTime values.
#   Since we cannot call GetLocalTime deterministically, we use the current
#   local time from Python's datetime.  The exact formula is UNKNOWN because
#   the writeup was truncated at that section.  We use a placeholder that
#   produces plausible byte values.
#
# ASSUMPTION: serial_length == len(name)  (common in simple crackmes).

import ctypes
import datetime


def _xor_buffer(name: str) -> list:
    """Build the XOR buffer from the name.
    ASSUMPTION: each entry is (ord(c) * 0x66666667) arithmetic-right-shift 34, low byte.
    This mimics: mov eax,66666667h / imul ecx / sar edx,2  where ecx=ord(c).
    """
    buf = []
    for c in name:
        v = ctypes.c_int32(ord(c)).value
        # 64-bit signed multiply, take high 32 bits (EDX after imul)
        product = ctypes.c_int64(v * 0x66666667).value
        edx = ctypes.c_int32(product >> 32).value
        edx = ctypes.c_int32(edx >> 2).value  # sar edx,2
        buf.append(edx & 0xFF)
    return buf


def _char_buffer(name: str) -> list:
    """Build the char buffer from local time + name.
    ASSUMPTION: writeup was truncated; we reconstruct a plausible formula.
    The writeup mentions day, month, year variables derived from GetLocalTime,
    and some arithmetic involving year * 0x51EB851F / sar edx,7.
    We use a placeholder: char_buffer[i] = (day + month + year_mod + i) & 0xFF
    where year_mod is derived similarly to the crackme.
    THIS IS HIGHLY SPECULATIVE.
    """
    now = datetime.datetime.now()
    day = now.day
    month = now.month
    year = now.year

    # ASSUMPTION: year computation uses imul 51EB851Fh / sar edx,7
    # which is equivalent to year // 100  (century)
    v = ctypes.c_int32(year).value
    product = ctypes.c_int64(v * 0x51EB851F).value
    edx = ctypes.c_int32(product >> 32).value
    edx = ctypes.c_int32(edx >> 7).value  # sar edx,7
    year_mod = edx & 0xFF

    buf = []
    for i, c in enumerate(name):
        # ASSUMPTION: combines day, month, year_mod, name index and char value
        val = (day + month + year_mod + ord(c) + i) & 0xFF
        buf.append(val)
    return buf


def _adjust(b: int) -> int:
    """Apply the byte-range adjustment described in the writeup."""
    b = b & 0xFF
    if 0x20 < b < 0x30:
        b = (b + 0x20) & 0xFF
    elif 0x39 < b <= 0x40:
        b = (b + 0x14) & 0xFF
    elif 0x5A < b <= 0x60:
        b = (b + 0x0F) & 0xFF
    return b


def _compute_serial(name: str) -> str:
    xbuf = _xor_buffer(name)
    cbuf = _char_buffer(name)
    # ASSUMPTION: serial length == len(name)
    length = len(name)
    serial_bytes = []
    for i in range(length):
        raw = (cbuf[i] ^ xbuf[i]) & 0xFF
        adjusted = _adjust(raw)
        serial_bytes.append(adjusted)
    return ''.join(chr(b) for b in serial_bytes)


def _validate_name(name: str) -> bool:
    if len(name) <= 3 or len(name) > 10:
        return False
    for c in name:
        if ord(c) <= 0x2F or ord(c) > 0x7A:
            return False
    return True


def verify(name: str, serial: str) -> bool:
    """Verify a name/serial pair.
    NOTE: Because char_buffer depends on the current time (GetLocalTime),
    this check is only valid when run at approximately the same time as
    serial generation.  The char_buffer formula is also ASSUMED.
    """
    if not _validate_name(name):
        return False
    expected = _compute_serial(name)
    return serial == expected


def keygen(name: str) -> str:
    """Generate a serial for the given name."""
    if not _validate_name(name):
        raise ValueError(f"Invalid name '{name}': must be 4-10 chars, each 0x30-0x7A")
    return _compute_serial(name)



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
