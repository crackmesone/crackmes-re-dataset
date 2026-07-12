#!/usr/bin/env python3
"""
CFB1 Keygen — Crackmes for Beginners #1

Algorithm (confirmed by multiple writeups and disassembly):
  For each character ch at index i in the username:
      val = ((i + 0x5A) ^ ord(ch) + 0x13) & 0xFF
      serial += '%02X' % val

Minimum username length: 4 characters.
"""


def verify(name: str, serial: str) -> bool:
    """
    Returns True if serial matches the computed serial for the given name.
    """
    if len(name) < 4:
        return False
    return keygen(name) == serial.upper()


def keygen(name: str) -> str:
    """
    Compute the valid serial for a given username.

    Algorithm per character:
        val = ((index + 0x5A) XOR ord(char) + 0x13) & 0xFF
        serial += '%02X' % val
    """
    if len(name) < 4:
        raise ValueError("Username must be at least 4 characters.")

    serial = ""
    for i, ch in enumerate(name):
        val = (i + 0x5A) ^ ord(ch)   # index + 90, XOR with ASCII value
        val = (val + 0x13) & 0xFF     # add 19, wrap to byte
        serial += "%02X" % val        # uppercase 2-digit hex
    return serial



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
