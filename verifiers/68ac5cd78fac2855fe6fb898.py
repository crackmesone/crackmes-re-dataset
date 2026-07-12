#!/usr/bin/env python3
"""
Keygen for 'KeygenMe again! (fix)' by hacktooth

Algorithm (from writeup analysis):
1. Read Name as bytes (the binary uses Unicode->ANSI via system code page)
2. XOR round-robin into 4-byte accumulator: acc[i & 3] ^= byte
3. XOR the 4-byte result with constants: acc[0]^0x37, acc[1]^0x6B, acc[2]^0x4C, acc[3]^0xAC
4. Format as uppercase hex LSB-first: KGM-XX XX XX XX
   (the '-' prefix comes from the deobfuscated 'KGM-' prefix stored in the binary)

Note on encoding:
  The app converts Unicode input to ANSI using the system code page.
  For pure ASCII names, UTF-8 and ANSI are identical.
  For non-ASCII names, the encoding matters (see locale notes in writeup).
  If conversion yields empty bytes, result is constant KGM-376B4CAC.
"""

import platform
import locale
import unicodedata

# XOR constants applied to each accumulator byte
CONST_BYTES = [0x37, 0x6B, 0x4C, 0xAC]

# Fallback serial when name encodes to empty bytes
CONST_SERIAL = "KGM-376B4CAC"


def default_encoding():
    """Best guess at the system ANSI code page (mirrors Windows behavior)."""
    if platform.system().lower().startswith("win"):
        return "mbcs"  # maps to the Windows system default ANSI code page
    return locale.getpreferredencoding(False) or "utf-8"


def calc_serial_from_bytes(name_bytes: bytes) -> str:
    """Core serial computation from raw name bytes."""
    if not name_bytes:
        return CONST_SERIAL
    acc = [0, 0, 0, 0]
    for i, b in enumerate(name_bytes):
        acc[i & 3] ^= b
    out = [acc[j] ^ CONST_BYTES[j] for j in range(4)]
    hex_str = "".join(f"{x:02X}" for x in out)
    return "KGM-" + hex_str


def verify(name: str, serial: str, encoding: str = None) -> bool:
    """Return True if serial matches the expected serial for name."""
    enc = encoding or default_encoding()
    name_bytes = name.encode(enc, errors="ignore")
    expected = calc_serial_from_bytes(name_bytes)
    return serial == expected


def keygen(name: str, encoding: str = None, normalize: str = None) -> str:
    """
    Generate the valid serial for the given name.

    Parameters
    ----------
    name     : the username string
    encoding : ANSI code page to use (default: system code page)
    normalize: optional Unicode normalization form (NFC/NFD/NFKC/NFKD)
    """
    if normalize:
        name = unicodedata.normalize(normalize, name)
    enc = encoding or default_encoding()
    name_bytes = name.encode(enc, errors="ignore")
    return calc_serial_from_bytes(name_bytes)


# ---------------------------------------------------------------------------
# Self-tests from the writeups
# ---------------------------------------------------------------------------

def _run_tests():
    tests = [
        # (name, encoding, expected_serial)
        ("AAAA", "ascii",   "KGM-762A0DED"),  # from nightxyz comment
        ("k00ReLab", "ascii", "KGM-39171D9C"), # from k00ri writeup
    ]
    all_ok = True
    for name, enc, expected in tests:
        got = keygen(name, encoding=enc)
        status = "OK" if got == expected else f"FAIL (got {got})"
        print(f"  name={name!r} enc={enc} -> {got}  [{status}]")
        if got != expected:
            all_ok = False
    return all_ok



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
