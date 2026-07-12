# Keygen for p0wnbox Cracking Challenge #4
# Based on writeup by OmegaLock
#
# Algorithm summary:
# 1. Start with hardcoded string: 'AfupqdzltFYjWcbRAVeLHgImNZXCPDQTOUiExvKoY'
#    (length 41 chars)
# 2. Overwrite first len(name) characters with the username bytes
# 3. Encrypt step 1: sum all bytes of the resulting 40-char buffer (0x28 = 40 bytes)
# 4. Encrypt step 2: iterate over each character of username, add its ASCII value
#    to the running sum
# 5. Encrypt step 3: square the running sum
# 6. The result (mod 2^32 to stay 32-bit) is the serial
#
# Verified:
#   OmegaLock  -> 20052484
#   pownboxforum -> 26183689

HARDCODED = 'AfupqdzltFYjWcbRAVeLHgImNZXCPDQTOUiExvKoY'
# The buffer used is 40 bytes (0x28), the hardcoded string starts there
BUF_LEN = 0x28  # 40


def _compute_serial(name: str) -> int:
    # Build the 40-byte buffer: overwrite first len(name) bytes with name,
    # rest comes from hardcoded string
    buf = list(HARDCODED[:BUF_LEN])
    for i, ch in enumerate(name[:BUF_LEN]):
        buf[i] = ch

    # Encrypt1: sum all 40 bytes of the modified hardcoded buffer
    acc = 0
    for i in range(BUF_LEN):
        acc += ord(buf[i])
        acc &= 0xFFFFFFFF

    # Encrypt2: iterate over name characters (index from 0 to len(name)-1)
    # and add each byte of the name to accumulator
    # The loop condition is: counter < len(name), going char by char
    for ch in name:
        acc += ord(ch)
        acc &= 0xFFFFFFFF

    # Encrypt3: square the accumulator
    acc = (acc * acc) & 0xFFFFFFFF
    return acc


def verify(name: str, serial: str) -> bool:
    # Validate inputs according to crackme rules
    if len(name) <= 5 or len(name) > 20:
        return False
    if not serial.isdigit():
        return False
    expected = _compute_serial(name)
    try:
        return int(serial) == expected
    except ValueError:
        return False


def keygen(name: str) -> str:
    if len(name) <= 5 or len(name) > 20:
        raise ValueError(f'Name must be 6-20 characters, got {len(name)}')
    return str(_compute_serial(name))



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
