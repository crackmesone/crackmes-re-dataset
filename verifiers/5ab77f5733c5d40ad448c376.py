import random
import time


def _serial_to_digits(s):
    """Convert a 14-char serial string to list of digit/char values."""
    return list(s)


def verify(name: str, serial: str) -> bool:
    """
    Checks the serial for the given name.

    Conditions derived from the writeup disassembly:
      1. len(name) must be 4..23 (inclusive)
      2. len(serial) must be 14
      3. s[5] == '3'  (fixed)
      4. s[8] == '5'  (fixed)
      5. s[1] == s[2] == '9'  (fixed)
      6. s[0] + s[13] == 12
      7. s[3] + s[4] + s[0] == 20  =>  s[3]+s[4] = 20 - s[0]
      8. s[3] + s[11] == 13
      9. s[4] + s[10] == 14
     10. s[9] + s[12] == 11
     11. s[6] and s[7] are the uppercase hex digits of ord(name[0])
         (e.g. sprintf("%X", name[0]) giving 2 hex chars)
     12. All positions except s[6] and s[7] must be decimal digits ('0'-'9')
    """
    if not (4 <= len(name) <= 23):
        return False
    if len(serial) != 14:
        return False

    s = serial

    # Positions other than 6 and 7 must be digits
    for i in range(14):
        if i not in (6, 7):
            if not s[i].isdigit():
                return False

    # Fixed positions
    if s[5] != '3':
        return False
    if s[8] != '5':
        return False
    if s[1] != '9' or s[2] != '9':
        return False

    # Convert digit positions to ints
    d = {}
    for i in range(14):
        if i not in (6, 7):
            d[i] = int(s[i])

    # Condition: s[0] + s[13] == 12
    if d[0] + d[13] != 12:
        return False

    # Condition: s[3] + s[11] == 13
    if d[3] + d[11] != 13:
        return False

    # Condition: s[4] + s[10] == 14
    if d[4] + d[10] != 14:
        return False

    # Condition: s[0] + s[3] + s[4] == 20
    if d[0] + d[3] + d[4] != 20:
        return False

    # Condition: s[9] + s[12] == 11
    if d[9] + d[12] != 11:
        return False

    # Condition: s[6]+s[7] == uppercase hex of ord(name[0]), zero-padded to 2 chars
    # ASSUMPTION: name[0] is taken as its byte value (ASCII)
    hex_char = format(ord(name[0]), 'X')
    # The keygen uses sprintf("%X", name[0]) which may produce 1 or 2 hex chars
    # and copies 2 bytes into s[6..7]. If only 1 hex digit, s[7] is whatever was there.
    # ASSUMPTION: we treat it as zero-padded to 2 hex digits for simplicity.
    if len(hex_char) == 1:
        hex_char = '0' + hex_char
    hex_char = hex_char[-2:]  # take last 2 chars
    if s[6].upper() != hex_char[0].upper() or s[7].upper() != hex_char[1].upper():
        return False

    return True


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.

    Strategy:
      - s[1] = s[2] = '9'
      - s[5] = '3'
      - s[8] = '5'
      - s[6],s[7] = hex(ord(name[0])) uppercase, 2 chars
      - Pick random s[11] in [5,9], s[3] = 13 - s[11]  => s[3] in [4,8]
      - Pick random s[10] in [5,9], s[4] = 14 - s[10]  => s[4] in [5,9]
      - s[0] = 20 - s[3] - s[4]  => must be 0..9
      - s[13] = 12 - s[0]        => must be 0..9
      - Pick random s[12] in [5,9], s[9] = 11 - s[12]  => must be 0..9
      - All digit positions must be 0..9
    """
    if not (4 <= len(name) <= 23):
        raise ValueError("Name length must be between 4 and 23 characters")

    hex_chars = format(ord(name[0]), 'X')
    if len(hex_chars) == 1:
        hex_chars = '0' + hex_chars
    hex_chars = hex_chars[-2:]

    random.seed(time.time())

    for _ in range(10000):
        # MY_RAND = 5 + rand() % 5 => values 5..9
        s11 = random.randint(5, 9)
        s3 = 13 - s11  # 4..8

        s10 = random.randint(5, 9)
        s4 = 14 - s10  # 5..9

        s0 = 20 - s3 - s4
        if not (0 <= s0 <= 9):
            continue

        s13 = 12 - s0
        if not (0 <= s13 <= 9):
            continue

        s12 = random.randint(5, 9)
        s9 = 11 - s12
        if not (0 <= s9 <= 9):
            continue

        # Build serial string
        s = ['0'] * 14
        s[0] = str(s0)
        s[1] = '9'
        s[2] = '9'
        s[3] = str(s3)
        s[4] = str(s4)
        s[5] = '3'
        s[6] = hex_chars[0]
        s[7] = hex_chars[1]
        s[8] = '5'
        s[9] = str(s9)
        s[10] = str(s10)
        s[11] = str(s11)
        s[12] = str(s12)
        s[13] = str(s13)

        serial = ''.join(s)
        if verify(name, serial):
            return serial

    raise RuntimeError("Could not generate a valid serial")



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
