import os

def decode_ascii2(s: str) -> str:
    """Shift each character's ASCII value by +3."""
    result = ""
    for ch in s:
        result += chr(ord(ch) + 3)
    return result

def to_hex_string(s: str) -> str:
    """Convert each character to its uppercase hex ASCII value and concatenate."""
    result = ""
    for ch in s:
        result += format(ord(ch), 'X')
    return result

def var1() -> str:
    """Get the computer/machine username from the environment.
    The encoded string '`ljmrqbok^jb' decoded with +3 = 'computername' -> but VB Environ uses 'USERNAME' or 'COMPUTERNAME'.
    Let's decode: '`ljmrqbok^jb' each char +3:
    ` -> c, l -> o, j -> m, m -> p, r -> u, q -> t, b -> e, o -> r, k -> n, ^ -> a, j -> m, b -> e
    => 'computername'
    So var1 = COMPUTERNAME environment variable."""
    encoded = "`ljmrqbok^jb"
    env_var_name = decode_ascii2(encoded)  # => 'computername'
    # Environ in VB is case-insensitive; try both cases
    value = os.environ.get(env_var_name.upper(), os.environ.get(env_var_name, ""))
    return value

def var2(v1: str) -> str:
    """Reverse the computername string."""
    return v1[::-1]

def var4(v2: str) -> str:
    """Convert reversed computername to hex string of ASCII values."""
    return to_hex_string(v2)

def var6(name: str) -> str:
    """Convert the user input (name) to hex string of ASCII values.
    In the original, var5 checks length >= 5; we just use the name as-is."""
    if len(name) < 5:
        raise ValueError("Name must be at least 5 characters long.")
    return to_hex_string(name)

def var7(v4: str, v6: str) -> str:
    """Concatenate hex of reversed computername + hex of name."""
    return v4 + v6

def var8(v7: str) -> str:
    """Apply decode_ascii2 (shift +3) to var7 result, then the serial is Mid(var8, 5, 15) in VB (1-based, position 5, length 15)."""
    return decode_ascii2(v7)

def compute_serial(name: str) -> str:
    v1 = var1()
    v2 = var2(v1)
    v4 = var4(v2)
    v6 = var6(name)
    v7 = var7(v4, v6)
    v8 = var8(v7)
    # VB Mid(str, 5, 15) is 1-based: take 15 chars starting at position 5 (index 4)
    serial = v8[4:4+15]
    return serial

def keygen(name: str) -> str:
    return compute_serial(name)

def verify(name: str, serial: str) -> bool:
    try:
        expected = compute_serial(name)
    except ValueError:
        return False
    return serial == expected


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
