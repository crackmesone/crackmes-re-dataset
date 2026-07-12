#!/usr/bin/env python3
"""
TryCrackMe (v1) by LeSynd1c - Serial Validator & Keygen

Algorithm (recovered from comments, writeups, and solution source):
  1. seed = len(username)
  2. For each character in username (looptimes = len(username)):
       seed = (seed * 0x19660D + 0x3C6EF35F) % 2**32  [LCG step]
       char = chr((seed % 94) + 33)                   [printable ASCII: 0x21..0x7E]
  3. Convert each char to 2-digit uppercase hex -> concatenated string
  4. Apply ROT-12 to hex letters A-F only (A->M, B->N, C->O, D->P, E->Q, F->R)
  5. Insert '-' after every 4 characters

Note on 'odd length' grouping from nightxyz comment:
  'xxxx-xx if odd length of input name' - this likely means last group may be 2 chars.
  The solution code simply groups by 4 regardless, which handles this naturally.

Verification example:
  havok  -> 6370-697M-47
  Example -> 2P7O-437O-5N54-6R
"""

LCG_MULTIPLIER = 0x19660D
LCG_INCREMENT  = 0x3C6EF35F
LCG_MODULUS    = 1 << 32  # 2**32


def _lcg_step(seed: int) -> int:
    """One step of the Linear Congruential Generator."""
    return (seed * LCG_MULTIPLIER + LCG_INCREMENT) % LCG_MODULUS


def _rot12_hex_char(c: str) -> str:
    """
    Apply ROT-12 to uppercase hex letters A-F only.
    A(65)->M(77), B->N, C->O, D->P, E->Q, F->R
    Digits 0-9 are unchanged.
    """
    if 'A' <= c <= 'F':
        # shift within A-Z alphabet by 12, wrapping at Z back to A
        return chr(((ord(c) - 65 + 12) % 26) + 65)
    return c


def _build_serial_string(username: str) -> str:
    """Core algorithm: returns the serial string (with dashes) for a username."""
    if not username:
        raise ValueError("Username must not be empty")

    seed = len(username)  # Step 1: seed = length of name

    payload_chars = []
    for _ in range(len(username)):  # looptimes = len(name)
        seed = _lcg_step(seed)                  # Step 2: LCG
        ch = chr((seed % 94) + 33)              # 0x5E=94, 0x21=33
        payload_chars.append(ch)

    # Step 3: to 2-digit uppercase hex
    hexed = ''.join(f"{ord(c):02X}" for c in payload_chars)

    # Step 4: ROT-12 on hex letters A-F
    rotated = ''.join(_rot12_hex_char(c) for c in hexed)

    # Step 5: group by 4, join with '-'
    groups = [rotated[i:i+4] for i in range(0, len(rotated), 4)]
    return '-'.join(groups)


def keygen(name: str) -> str:
    """Generate a valid serial for the given username."""
    return _build_serial_string(name)


def verify(name: str, serial: str) -> bool:
    """
    Verify a (name, serial) pair.
    Comparison is case-insensitive for the serial string.
    """
    if not name or not serial:
        return False
    try:
        expected = _build_serial_string(name)
    except ValueError:
        return False
    return expected.upper() == serial.upper()



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
