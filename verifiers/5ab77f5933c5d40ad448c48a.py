def name_checksum(name: str) -> int:
    """
    Compute the checksum for the name:
    sum of (ord(c) ^ 0x47) for each character, interpreted as signed byte.
    """
    total = 0
    for c in name:
        val = ord(c) ^ 0x47
        # movsx: sign-extend from byte
        val = val if val < 128 else val - 256
        total += val
    return total


def pass_checksum(password: str) -> int:
    """
    Compute the checksum for the password:
    sum of (ord(c) ^ 0x42) for each character, interpreted as signed byte.
    """
    total = 0
    for c in password:
        val = ord(c) ^ 0x42
        # movsx: sign-extend from byte
        val = val if val < 128 else val - 256
        total += val
    return total


def verify(name: str, serial: str) -> bool:
    """
    The crackme accepts when:
        sum_name == sum_pass
    where:
        sum_name = sum(ord(c) ^ 0x47, sign-extended) for c in name
        sum_pass = sum(ord(c) ^ 0x42, sign-extended) for c in serial
    """
    if not name or not serial:
        return False
    return name_checksum(name) == pass_checksum(serial)


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.

    Strategy (from solution 3 / solution 4):
      Each character of the name contributes (name[i] ^ 0x47) to sum_name.
      A password character c contributes (ord(c) ^ 0x42) to sum_pass.
      The simplest keygen: for each name character c, emit chr(ord(c) ^ 0x47 ^ 0x42),
      i.e. chr(ord(c) ^ 0x05). This makes sum_pass == sum_name character-by-character.

    Alternative: use a single-character or multi-character serial that hits the target sum.
    """
    if not name:
        # ASSUMPTION: empty name is rejected by the crackme; return empty string
        return ''

    # Simple character-by-character approach (solution 3/4):
    serial = ''
    for c in name:
        serial += chr(ord(c) ^ 0x05)  # ord(c)^0x47^0x42 == ord(c)^0x05
    return serial


def keygen_checksum_based(name: str) -> str:
    """
    Alternative keygen: compute target checksum and build a serial using
    repeated 0x3c (60) chars plus a remainder character (from solution 2).
    """
    target = name_checksum(name)

    # We need sum of (ord(c) ^ 0x42) == target
    # Use chr(60 ^ 0x42) = chr(0x76) = 'v' which contributes 60 each time
    # Then a final character for the remainder.
    # ASSUMPTION: target >= 0; if negative, this simple scheme won't work.
    if target <= 0:
        # ASSUMPTION: fall back to character-by-character keygen
        return keygen(name)

    full_chars = target // 60
    remainder = target % 60

    result = chr(60 ^ 0x42) * full_chars  # each contributes 60 to sum_pass
    if remainder != 0:
        result += chr(remainder ^ 0x42)
    elif full_chars == 0:
        # target == 0, need at least one char with contribution 0
        # chr(0 ^ 0x42) = chr(0x42) = 'B'
        result = chr(0x42)
    return result



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
