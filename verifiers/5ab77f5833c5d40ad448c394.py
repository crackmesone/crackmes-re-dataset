# Keygen for darkmaster2's keygenME #1
# Reversed from Stanley White's keygen source (control.h / main.cpp)
#
# The crackme picks an 8-char serial string and checks:
#   1. Sum all 8 ASCII values -> serialValue
#   2. serValue = (serialValue << 1) ^ serialValue   (i.e. serialValue * 3)
#   3. Convert serValue to decimal string
#   4. Sum the decimal digits of that string
#   5. Result must equal 20
#
# The keygen starts from a random-looking 8-char hex string and increments
# serial[0] until the check passes.

def calc(serial: str) -> int:
    """Compute the check value for an 8-character serial string."""
    # Step 1: sum ASCII values of the 8 chars
    serial_value = sum(ord(c) for c in serial[:8])

    # Step 2: serValue = serialValue*2 XOR serialValue  =>  serialValue * 3
    ser_value = (serial_value << 1) ^ serial_value

    # Step 3: convert to decimal string, then sum the digits
    s = str(ser_value)
    digit_sum = sum(int(ch) for ch in s)

    return digit_sum


def verify(name: str, serial: str) -> bool:
    """Return True if serial is valid (digit_sum of 3*ascii_sum == 20).
    The name field is not used by this crackme."""
    if len(serial) < 8:
        return False
    return calc(serial) == 20


def keygen(name: str = "") -> str:
    """Generate a valid 8-character serial.

    Mirrors the original keygen logic:
      - Start with a fixed 8-char hex-style seed.
      - Increment serial[0] (as an integer character code) until calc()==20.
    """
    import time as _time
    import ctypes

    # Mimic: time ^= 0xC0DEDEAD; itoa(time, serial, 16)
    # Use a pseudo-random seed similar to GetTickCount ^ 0xC0DEDEAD
    seed = (int(_time.time() * 1000) & 0xFFFFFFFF) ^ 0xC0DEDEAD
    base = format(seed, '08x')[:8]   # 8 hex chars

    serial = list(base)

    # Ensure we have exactly 8 chars
    while len(serial) < 8:
        serial.append('0')

    # Increment serial[0] until check passes (wraps through ASCII)
    max_attempts = 256
    for _ in range(max_attempts):
        candidate = ''.join(serial)
        if calc(candidate) == 20:
            return candidate
        # Increment the first character's ASCII value by 1
        serial[0] = chr(ord(serial[0]) + 1)

    # If we exhausted the first char, brute-force a simple valid serial
    # ASSUMPTION: fall back to a brute-force search over printable ASCII serials
    for c0 in range(32, 127):
        for c1 in range(32, 127):
            candidate = chr(c0) + chr(c1) + 'aaaaaaa'[:6]
            if calc(candidate[:8]) == 20:
                return candidate[:8]

    raise ValueError("Could not find a valid serial")



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
            print(_sv)
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
