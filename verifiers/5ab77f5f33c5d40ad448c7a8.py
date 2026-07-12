def _rol_byte(value, times):
    value = value & 0xFF
    for _ in range(times):
        highbit = (value >> 7) & 1
        value = ((value & 0x7F) << 1) | highbit
        value = value & 0xFF
    return value

BASE = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASELEN = len(BASE)  # 62

def _swapstring(src, n):
    """Rotate src left by n positions."""
    n = n % len(src)
    return src[n:] + src[:n]

def _stripname(name):
    """Keep only characters present in BASE."""
    return ''.join(c for c in name if c in BASE)

def _changename(name, swapped1):
    """Generate the intermediate 'encrypted' name string."""
    result = []
    baselen = BASELEN
    dl = _rol_byte(ord(name[0]), 3)
    for i in range(len(name)):
        al = ord(name[i])
        next_char = ord(name[i + 1]) if i + 1 < len(name) else 0
        al = al ^ next_char
        al = (al + dl) & 0xFF
        dl = (dl + al) & 0xFF
        offs = al % baselen
        result.append(swapped1[offs])
    return ''.join(result)

def _findoffset(ch, s):
    """Find position of ch in s."""
    return s.index(ch)

def keygen(name):
    name = _stripname(name)
    if len(name) == 0:
        return None
    namelen = len(name)
    # Calculate offset for swapped1: namelen * 4, capped at 30 if > 60
    offset = namelen * 4
    if offset > 60:
        offset = 30
    swapped1 = _swapstring(BASE, offset)
    name2 = _changename(name, swapped1)  # intermediate/encrypted name
    serial = []
    for i in range(namelen):
        # Find position of name[i] in swapped1
        offset2 = _findoffset(name[i], swapped1)
        # Generate swapped2 starting from that position
        swapped2 = _swapstring(swapped1, offset2)
        # Find position of name2[i] in swapped1
        offset3 = _findoffset(name2[i], swapped1)
        serial.append(swapped2[offset3])
    return ''.join(serial)

def verify(name, serial):
    expected = keygen(name)
    if expected is None:
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
