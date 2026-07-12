#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Crackme: lilbitofthislilbitofthat by basmannetjeee
Algorithm fully recovered from two independent writeups.

Character set (length=52):
  'abcdefghijklmnoABCDEFGHIJKpqrstuvwxyzLMNOPQRSTUVWXYZ'

For each character in username:
  index = (ord(char) * 16 * len(username) >> 2) % 52
       == (ord(char) * 4 * len(username)) % 52
  serial_char = CHARACTER_SET[index]
"""

CHARACTER_SET = "abcdefghijklmnoABCDEFGHIJKpqrstuvwxyzLMNOPQRSTUVWXYZ"
MOD = len(CHARACTER_SET)  # 52


def generate_serial(username: str) -> str:
    """
    Generate the serial key for the given username.
    Steps per character:
      1. Multiply ASCII value by 16
      2. Multiply by username length
      3. Right-shift by 2 (equivalent to dividing by 4)
      4. Take modulo 52
      5. Use result as index into CHARACTER_SET
    """
    L = len(username)
    serial = []
    for ch in username:
        index = (ord(ch) * 16 * L >> 2) % MOD  # == (ord(ch) * 4 * L) % 52
        serial.append(CHARACTER_SET[index])
    return ''.join(serial)


def verify(name: str, serial: str) -> bool:
    """
    Returns True if the serial matches the generated serial for name.
    """
    # ASSUMPTION: no explicit length restriction enforced here beyond buffer (<=256)
    return generate_serial(name) == serial


def keygen(name: str) -> str:
    """
    Returns a valid serial for the given username.
    """
    return generate_serial(name)



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
