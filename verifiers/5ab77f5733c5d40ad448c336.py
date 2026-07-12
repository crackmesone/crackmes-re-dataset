#!/usr/bin/env python3
"""
amkTwo keygen / verifier
Based on the full source code provided in the solution writeup.

The crackme uses a key FILE (amkTwo.key) containing:
  Line 1: name + '\n'
  Line 2: serial (32 chars, no newline)

The verify() function here checks whether a given serial matches
the one generated from the name.
"""

KEY_CHARS = "0123456789ABCDEF"
KEY_CHARS_LEN = len(KEY_CHARS)  # 16


def rot(chars: list) -> None:
    """Mutate chars list in-place (C char array semantics).
    Only transforms letters and digits; non-transformed chars are left alone.
    For letters (upper or lower): if ASCII value is even -> decrement, else increment.
    For digits: if ASCII value is even -> increment, else decrement.
    """
    for i in range(len(chars)):
        c = ord(chars[i])
        bMod2 = c % 2
        if 96 < c < 123:  # lowercase a-z
            if bMod2 == 0:
                chars[i] = chr(c - 1)
            else:
                chars[i] = chr(c + 1)
        elif 64 < c < 91:  # uppercase A-Z
            if bMod2 == 0:
                chars[i] = chr(c - 1)
            else:
                chars[i] = chr(c + 1)
        elif 47 < c < 58:  # digits 0-9
            if bMod2 == 0:
                chars[i] = chr(c + 1)
            else:
                chars[i] = chr(c - 1)


def rot13(chars: list) -> None:
    """Mutate chars list in-place.
    Letters: standard rot13.
    Digits 0-4: +5; digits 5-9: -5.
    """
    for i in range(len(chars)):
        c = chars[i]
        o = ord(c)
        if ('a' <= c <= 'm') or ('A' <= c <= 'M'):
            chars[i] = chr(o + 13)
        elif ('n' <= c <= 'z') or ('N' <= c <= 'Z'):
            chars[i] = chr(o - 13)
        elif '0' <= c <= '4':
            chars[i] = chr(o + 5)
        elif '5' <= c <= '9':
            chars[i] = chr(o - 5)


def gen_serial(name_with_newline: str) -> str:
    """
    Reproduces genSerial() from the C source.
    name_with_newline = name + '\n'  (the crackme appends \x0A to the name).
    Returns a 32-character serial string.
    """
    sz_string = name_with_newline
    n = len(sz_string)

    output = []   # grows as we fill positions 0..31
    y = 0
    z = 0

    for x in range(32):
        # Note: szString[y] is used as a signed char in C.
        # Python ord() gives unsigned; convert to signed byte.
        byte_val = ord(sz_string[y])
        if byte_val > 127:
            byte_val -= 256

        k = (x + 1) + byte_val + z
        if k < 0:
            k = -k
        k = k % KEY_CHARS_LEN  # equivalent to the while loop since k >= 0

        output.append(KEY_CHARS[k])

        y += 1
        if y > n - 1:  # y > strlen(szString) - 1
            z += 1
            y = 0
            # rot and rot13 are applied to the OUTPUT built so far
            rot(output)
            rot13(output)

    return ''.join(output)


def keygen(name: str) -> str:
    """Generate the valid serial for the given name."""
    # The crackme appends \x0A (newline) to the name before generating.
    name_with_newline = name + '\x0a'
    return gen_serial(name_with_newline)


def verify(name: str, serial: str) -> bool:
    """Return True if serial matches the expected serial for name."""
    if not name or not serial:
        return False
    expected = keygen(name)
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
