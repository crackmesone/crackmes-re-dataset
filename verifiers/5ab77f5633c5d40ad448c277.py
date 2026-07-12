import ctypes

def _build_temp_string(name: str) -> str:
    """
    Transform the name by repeating each character at index i exactly i times.
    Index 0 -> 0 repetitions (skipped)
    Index 1 -> 1 repetition
    Index 2 -> 2 repetitions
    etc.

    Example: 'bla' -> 'laa'
    Example: 'Cyclops' -> 'yccllloooopppppssssss'
    """
    tmp = []
    for i, ch in enumerate(name):
        for _ in range(i):
            tmp.append(ch)
    return ''.join(tmp)


def _compute_serial(tmp_string: str) -> int:
    """
    Serial generation algorithm (32-bit unsigned arithmetic):
      eax (serial) = 0
      edi (t1)     = 0x43BA
      for each char c in tmp_string:
          eax = eax * edi
          eax = eax + ord(c)
          edi = edi * 0x6E6FA
      return eax  (as unsigned 32-bit)
    """
    # Use ctypes.c_uint32 to emulate 32-bit unsigned overflow
    serial = ctypes.c_uint32(0)
    t1     = ctypes.c_uint32(0x43BA)

    for ch in tmp_string:
        serial = ctypes.c_uint32(serial.value * t1.value)
        serial = ctypes.c_uint32(serial.value + ord(ch))
        t1     = ctypes.c_uint32(t1.value * 0x6E6FA)

    return serial.value


def keygen(name: str) -> str:
    """
    Generate the valid serial for the given name.
    Returns the serial as a decimal string (unsigned 32-bit).
    """
    tmp    = _build_temp_string(name)
    serial = _compute_serial(tmp)
    return str(serial)


def verify(name: str, serial: str) -> bool:
    """
    Verify that the supplied serial matches the one derived from name.
    The crackme compares the computed serial (printed as unsigned decimal)
    against the user-supplied serial string.
    """
    expected = keygen(name)
    return serial.strip() == expected


# ---------------------------------------------------------------------------
# Quick self-test
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
