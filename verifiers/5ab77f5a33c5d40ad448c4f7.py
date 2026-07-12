import random
import string

# Constants derived from the crackme analysis
KEY_PREFIX = 62  # 0x08048416 - 0x080483D8 = 0x3E = 62 decimal
JMP_OFFSET = 0x1C  # target: patch jmp to point at 'key_ok' (0x08048437 - 0x0804841b = 0x1C)


def name_checksum(name: str) -> int:
    """Sum of all character ASCII values, squared, truncated to 1 byte."""
    c = sum(ord(ch) for ch in name)
    return (c * c) & 0xFF


def key_part2_checksum(part2: str) -> int:
    """Checksum of the part after '-': (0 - sum_of_chars) & 0xFF"""
    c = sum(ord(ch) for ch in part2)
    return (-c) & 0xFF


def verify(name: str, serial: str) -> bool:
    """
    A valid serial has the form: '62-XXXXXXX'
    where:
      - The part before '-' must equal 62 (decimal) when converted via atoi
      - The part after '-' must have length > 5
      - (name_checksum(name) ^ key_part2_checksum(part2)) & 0xFF == 0x1C
    """
    if '-' not in serial:
        return False

    dash_idx = serial.index('-')
    prefix_str = serial[:dash_idx]
    part2 = serial[dash_idx + 1:]

    # Prefix must be non-empty and convert to non-zero via atoi
    try:
        prefix_val = int(prefix_str)
    except ValueError:
        return False

    if prefix_val == 0:
        return False

    # key_prefix must equal 62
    if prefix_val != KEY_PREFIX:
        return False

    # part2 length must be > 5
    if len(part2) <= 5:
        return False

    nchk = name_checksum(name)
    kchk = key_part2_checksum(part2)

    return ((nchk ^ kchk) & 0xFF) == JMP_OFFSET


def _rand_alnum_char() -> str:
    """Return a random alphanumeric character."""
    chars = string.ascii_letters + string.digits
    return random.choice(chars)


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.

    Strategy (mirrors keygen.cpp):
      1. Compute name_checksum(name).
      2. Required key_chk = JMP_OFFSET ^ name_checksum = 0x1C ^ nchk.
         Because: name_chk ^ key_chk == 0x1C  =>  key_chk = name_chk ^ 0x1C.
      3. Build a random alphanumeric string of length >= 6 whose
         key_part2_checksum equals the required key_chk.
      4. Return '62-' + that string.
    """
    nchk = name_checksum(name)
    required_kchk = (nchk ^ JMP_OFFSET) & 0xFF

    # Build a base of 4 random alnum chars, then append chars until checksum matches
    while True:
        base = [_rand_alnum_char() for _ in range(4)]
        part2 = base[:]
        running_sum = sum(ord(c) for c in part2)

        for _ in range(200):  # safety limit on iterations
            # We need (-running_sum - ord(next_char)) & 0xFF == required_kchk
            # => ord(next_char) == (-running_sum - required_kchk) & 0xFF
            # but the result may not be alnum; if so, append a random alnum char
            # and keep going.
            needed = (-running_sum - required_kchk) & 0xFF
            if chr(needed).isalnum() and not chr(needed).isspace():
                part2.append(chr(needed))
                break
            else:
                # Append a random alnum char to change the running sum
                c = _rand_alnum_char()
                part2.append(c)
                running_sum += ord(c)

        part2_str = ''.join(part2)
        if len(part2_str) > 5 and key_part2_checksum(part2_str) == required_kchk:
            return f"62-{part2_str}"
        # else retry



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
