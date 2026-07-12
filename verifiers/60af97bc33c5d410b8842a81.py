from string import digits, ascii_lowercase
import itertools


def hash_name(username: str) -> int:
    """Hash the username as described in the solution writeup."""
    encoded = username.encode('ascii')

    # last char XOR 2, then *2
    hashed_char = (encoded[-1] ^ 2) * 2

    if hashed_char == 0:
        return hashed_char

    hashed_len = len(username) + 0x64  # len + 100

    result = (hashed_char * hashed_len) & 0xFFFFFFFF

    if result == 0:
        return result

    # early-exit guards from the original binary
    if result <= 0x64:
        return result

    # ASSUMPTION: values > 2147483647 are treated as signed-negative
    # and are returned early (no valid S/N can be derived from them)
    if result > 2147483647:
        return result

    hashed_len_2 = (hashed_len * 2) + 0x259  # hashed_len*2 + 601
    result = (hashed_len_2 * result) & 0xFFFFFFFF
    result = (hashed_len * result) & 0xFFFFFFFF
    return result


def hash_serial(sn: int) -> int:
    """Hash the serial: (sn^1) + (sn^2) + (sn^3).
    Here '^' means XOR, not exponentiation.
    """
    return (sn ^ 1) + (sn ^ 2) + (sn ^ 3)


def check_solution(hashed_value: int) -> int:
    """Given a username hash, try to find a serial whose hash matches.
    Returns the serial if found, -1 otherwise.
    """
    # If hashed_value would make the serial hash overflow into signed territory
    # there is no valid solution.
    if hashed_value > 2147483647:
        return -1

    # Case 1: sn & 3 == 0  =>  hash = sn*3 + 6  =>  sn = (hash-6)/3
    if (hashed_value - 6) % 3 == 0:
        candidate = (hashed_value - 6) // 3
        if candidate >= 0 and (candidate & 3) == 0:
            return candidate

    # Case 2: sn & 3 == 1  =>  hash = sn*3 + 2  =>  sn = (hash-2)/3
    if (hashed_value - 2) % 3 == 0:
        candidate = (hashed_value - 2) // 3
        if candidate >= 0 and (candidate & 3) == 1:
            return candidate

    # Case 3: sn & 3 == 2  =>  hash = sn*3 - 2  =>  sn = (hash+2)/3
    if (hashed_value + 2) % 3 == 0:
        candidate = (hashed_value + 2) // 3
        if candidate >= 0 and (candidate & 3) == 2:
            return candidate

    # Case 4: sn & 3 == 3  =>  hash = sn*3 - 6  =>  sn = (hash+6)/3
    if (hashed_value + 6) % 3 == 0:
        candidate = (hashed_value + 6) // 3
        if candidate >= 0 and (candidate & 3) == 3:
            return candidate

    return -1


def verify(name: str, serial) -> bool:
    """Verify a (username, serial) pair.
    serial may be supplied as an int or a numeric string.
    """
    try:
        sn = int(serial)
    except (ValueError, TypeError):
        return False

    name_hash = hash_name(name)

    # Early-exit conditions that produce no valid serial
    if name_hash == 0 or name_hash <= 0x64 or name_hash > 2147483647:
        return False

    sn_hash = hash_serial(sn)
    return name_hash == sn_hash


def keygen(name: str) -> int:
    """Return a valid serial for the given username, or -1 if none exists."""
    name_hash = hash_name(name)
    return check_solution(name_hash)


# ---------------------------------------------------------------------------
# Demo / bruteforce (mirrors the original script from the writeup)
# ---------------------------------------------------------------------------

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
