import os

def compute_serial1(computer_name: str) -> int:
    """
    Compute first serial field from computer name (first 5 chars).
    Algorithm from assembly / VB source:
      sec = ord(C[0]) - 4
      sec += ord(C[1])
      sec += 0x137  (311)
      sec += 0x2C7  (711)
      sec += ord(C[2])
      sec -= 5
      sec += ord(C[3])
      sec <<= 1       (multiply by 2)
      sec += ord(C[4])
    """
    name = computer_name.upper() if False else computer_name  # keep original case
    # The crackme uses the raw computer name as returned by GetComputerNameA
    c = [ord(ch) for ch in name[:5]]
    # Pad with 0 if computer name shorter than 5 chars (ASSUMPTION: behaviour undefined for short names)
    while len(c) < 5:
        c.append(0)
    sec = c[0] - 4
    sec += c[1]
    sec += 0x137
    sec += 0x2C7
    sec += c[2]
    sec -= 5
    sec += c[3]
    sec <<= 1
    sec += c[4]
    return sec


def compute_serial3(serial1: int) -> int:
    """
    Third serial field = serial1 + 0x7C0 (1984)
    """
    return serial1 + 0x7C0


def keygen(computer_name: str) -> str:
    """
    Generate the valid serial for the given computer name.
    Format: '<serial1>-DaXXoR-<serial3>'
    """
    s1 = compute_serial1(computer_name)
    s3 = compute_serial3(s1)
    return f"{s1}-DaXXoR-{s3}"


def verify(name: str, serial: str) -> bool:
    """
    Verify a serial against the computer name.
    name   : computer name (GetComputerNameA result)
    serial : string in format '<int>-DaXXoR-<int>'
    """
    parts = serial.split('-')
    # Expect exactly 3 parts; middle must be 'DaXXoR'
    if len(parts) != 3:
        return False
    box1_str, box2_str, box3_str = parts
    if box2_str != 'DaXXoR':
        return False
    try:
        box1 = int(box1_str)
        box3 = int(box3_str)
    except ValueError:
        return False
    expected1 = compute_serial1(name)
    expected3 = compute_serial3(expected1)
    return box1 == expected1 and box3 == expected3



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
