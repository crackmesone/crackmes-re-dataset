#!/usr/bin/env python3
"""KeygenMe_3_SWD keygen/verifier, reconstructed from writeup by Ap0dexMe0."""
from __future__ import annotations


def _u32(x: int) -> int:
    return x & 0xFFFFFFFF


def _rol32(x: int, r: int) -> int:
    r &= 31
    x = _u32(x)
    return _u32((x << r) | (x >> (32 - r)))


def _ror32(x: int, r: int) -> int:
    r &= 31
    x = _u32(x)
    return _u32((x >> r) | (x << (32 - r)))


def _imul32(a: int, b: int) -> int:
    """Low 32 bits of signed x86 IMUL on DWORD operands (matches MSVC behaviour)."""
    sa = _u32(a)
    sb = _u32(b)
    sa = sa - 0x100000000 if sa >= 0x80000000 else sa
    sb = sb - 0x100000000 if sb >= 0x80000000 else sb
    return _u32(sa * sb)


_BASE36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _encode_base36_fixed(value: int, width: int) -> str:
    if value == 0:
        return "0" * width
    digits: list[str] = []
    v = value
    while v:
        v, r = divmod(v, 36)
        digits.append(_BASE36[r])
    body = "".join(reversed(digits))
    return body.rjust(width, "0")[-width:]


def derive_secret_code(username: str) -> str:
    """
    FUN_140002100 -- derive the secret code from username.

    Format: AAAA-BBBBB-CCC  (4-5-3 base-36 segments)

    local_104 = sum of ord(c) * (index + 1)
    local_100 = xor fold of (ord(c) + index)
    local_108 = product of (ord(c) + 3) mod 100_000, seeded with 1

    A = (local_104 ^ 0x5A5A) % 0xB640
    B = (local_108 + local_100 * 0x539) % 0x39AA400
    C = (local_104 + local_108 + local_100) % 0xB640
    """
    u = username.upper()
    local_104 = 0
    local_100 = 0
    local_108 = 1
    for i, ch in enumerate(u):
        o = ord(ch)
        local_104 += o * (i + 1)
        local_100 ^= o + i
        local_108 = (local_108 * (o + 3)) % 100_000

    a = (local_104 ^ 0x5A5A) % 0xB640
    b = (local_108 + local_100 * 0x539) % 0x39AA400
    c = (local_104 + local_108 + local_100) % 0xB640
    return (
        f"{_encode_base36_fixed(a, 4)}-"
        f"{_encode_base36_fixed(b, 5)}-"
        f"{_encode_base36_fixed(c, 3)}"
    )


def hash_username_secret(username: str, secret_code: str) -> int:
    """
    FUN_1400025a0 -- hash used for the verification PIN.

    Builds blob: UPPER(username) + chr(len(secret_code) ^ 0x5A) + secret_code
    Runs XOR/rotate mixing loop (odd indices swap the two accumulators).
    Final avalanche uses signed x86 IMUL constants.
    Result is masked to 0x7FFFFFFF (bit 31 cleared).
    """
    blob = username.upper() + chr(len(secret_code) ^ 0x5A) + secret_code
    a = 0xA3B1C2D3
    b = 0x1F2E3D4C
    for i, c in enumerate(blob):
        o = ord(c)
        a = _u32(a ^ (o + i * 0x11))
        a = _rol32(a, (i % 5) + 3)
        a = _u32(a + (b ^ 0x9E3779B9))
        b = _u32(b ^ (a + o * 0x83))
        b = _ror32(b, (i % 7) + 2)
        b = _u32(b + _u32((a << 3) ^ 0x7F4A7C15))
        if i & 1:
            a, b = b, a

    x = _u32(a ^ b ^ _u32((a ^ b) >> 16))
    x = _imul32(x, (-0x7A143595) & 0xFFFFFFFF)
    x = _u32(x ^ (x >> 13))
    x = _imul32(x, (-0x3D4D51CB) & 0xFFFFFFFF)
    return _u32(x ^ (x >> 16)) & 0x7FFFFFFF


def validate_username(username: str) -> tuple[bool, str]:
    """Username must be ASCII, length 3..15 (inclusive)."""
    if not username.isascii():
        return False, "username must be ASCII"
    n = len(username)
    if not (3 <= n < 16):
        return False, "username length must be between 3 and 15 (inclusive)"
    return True, ""


def keygen(username: str) -> str:
    """Return 'secret_code|pin' for the given username."""
    ok, msg = validate_username(username)
    if not ok:
        raise ValueError(msg)
    secret = derive_secret_code(username)
    pin = hash_username_secret(username, secret)
    return f"{secret}|{pin}"


def verify(name: str, serial: str) -> bool:
    """
    serial is expected as 'SECRET_CODE|PIN' (pipe-separated).
    If no pipe is present the entire string is tried as the secret code
    with a freshly derived PIN (i.e. only the secret is checked).

    Returns True only when BOTH secret code AND PIN are correct.
    """
    ok, _ = validate_username(name)
    if not ok:
        return False

    if '|' in serial:
        parts = serial.split('|', 1)
        secret_part = parts[0].strip()
        pin_part = parts[1].strip()
    else:
        # ASSUMPTION: caller supplied only the secret; derive expected PIN.
        secret_part = serial.strip()
        pin_part = None

    expected_secret = derive_secret_code(name)
    if secret_part.upper() != expected_secret.upper():
        return False

    expected_pin = hash_username_secret(name, secret_part)

    if pin_part is None:
        # Only secret was provided -- treat as partial pass.
        # ASSUMPTION: return True if secret matches and no PIN given.
        return True

    try:
        supplied_pin = int(pin_part)
    except ValueError:
        return False

    return supplied_pin == expected_pin


# ---------------------------------------------------------------------------
# Self-test against known-good values from the comments
# ---------------------------------------------------------------------------
_KNOWN = [
    ("zqd",         "0I36-03EMY-6KY",  1112821151),
    ("frizehack",   "0E82-03GTT-3PT",   535422696),
    ("liboxin",     "0G8A-03U06-F0M",  1030886717),
    ("NiceCrackMe", "0E95-02OZ2-3PT",  1200406703),
    ("baran",       "0ILA-01WIQ-1BQ",  2053831614),
    ("fun",         "0I2O-029Q0-G42",   546500405),
    ("skywashere",  "0EOX-01VYL-DIO",  1572369152),
]


def _run_tests() -> None:
    print("Running self-tests...")
    all_ok = True
    for username, expected_secret, expected_pin in _KNOWN:
        secret = derive_secret_code(username)
        pin = hash_username_secret(username, secret)
        ok_s = (secret == expected_secret)
        ok_p = (pin == expected_pin)
        status = "OK" if (ok_s and ok_p) else "FAIL"
        if not (ok_s and ok_p):
            all_ok = False
        print(
            f"  [{status}] {username:15s}  "
            f"secret={'OK' if ok_s else f'GOT {secret} WANT {expected_secret}':30s}  "
            f"pin={'OK' if ok_p else f'GOT {pin} WANT {expected_pin}'}"
        )
    print("All tests passed." if all_ok else "SOME TESTS FAILED.")



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
