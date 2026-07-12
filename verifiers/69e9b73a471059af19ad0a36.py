#!/usr/bin/env python3
"""
Reconstructed keygen for 'CrackMe Hard' by liboxin.

Algorithm (from DevVolodya's write-up):
  1. The crackme parses the serial using a custom base-64 alphabet:
       ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_'
     Each character encodes 6 bits; the serial is decoded to a 64-bit integer.
  2. The parsed 64-bit value is transformed:
       target = ROL64(parsed ^ 0xDEADBEEFCAFEBABE, 23)
  3. At 0x1400B6779 the crackme compares: cmp rbx, rax
     where rax holds the computed target and rbx holds some runtime-derived value.

CRITICAL GAP: The write-up reveals that RBX (the expected value) is computed
at runtime and depends on srand/rand internal state seeded from the username
(or something similarly dynamic). The exact function that maps username -> RBX
is NOT described in the write-up. Therefore:
  - verify() can only check that a serial encodes to a value that, when
    transformed, equals a given target; it cannot derive target from name alone.
  - The real keygen requires dynamic instrumentation (Frida) to capture RBX.

# ASSUMPTION: RBX is purely a function of the username (seed), but the exact
# hash/transform is unknown. We provide the static encode/decode helpers
# and a stub verify() that checks round-trip consistency.
"""

from __future__ import annotations

MASK64 = (1 << 64) - 1
CONST_XOR = 0xDEADBEEFCAFEBABE
ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
ALPH_MAP = {ch: i for i, ch in enumerate(ALPHABET)}


def rol64(x: int, n: int) -> int:
    x &= MASK64
    return ((x << n) | (x >> (64 - n))) & MASK64


def ror64(x: int, n: int) -> int:
    x &= MASK64
    return ((x >> n) | (x << (64 - n))) & MASK64


def decode_serial(serial: str) -> int | None:
    """Decode custom-base64 serial string -> 64-bit integer."""
    value = 0
    for ch in serial:
        if ch not in ALPH_MAP:
            return None
        value = (value << 6) | ALPH_MAP[ch]
    return value & MASK64


def encode_serial(value: int) -> str:
    """Encode 64-bit integer -> custom-base64 serial string (min 8 chars)."""
    value &= MASK64
    if value == 0:
        out = "0"
    else:
        chars = []
        v = value
        while v:
            chars.append(ALPHABET[v & 0x3F])
            v >>= 6
        out = "".join(reversed(chars))
    # Pad to at least 8 characters
    if len(out) < 8:
        out = ALPHABET[0] * (8 - len(out)) + out
    return out


def serial_to_target(serial: str) -> int | None:
    """Parse serial and apply the forward transform: target = ROL64(parsed ^ XOR_CONST, 23)."""
    parsed = decode_serial(serial)
    if parsed is None:
        return None
    return rol64(parsed ^ CONST_XOR, 23)


def target_to_serial(target: int) -> str:
    """Invert the transform and encode: serial encodes ROR64(target, 23) ^ XOR_CONST."""
    raw = ror64(target, 23) ^ CONST_XOR
    return encode_serial(raw)


# ---------------------------------------------------------------------------
# ASSUMPTION: The runtime RBX value is derived from the username via an unknown
# internal function (likely involving rand() seeded from the username bytes or
# a custom hash). Since this function is not described in the write-up, we
# cannot implement verify(name, serial) -> bool in a purely static way.
# The stub below accepts a pre-captured target for testing round-trips.
# ---------------------------------------------------------------------------

def _username_to_target(name: str) -> int:
    """
    # ASSUMPTION: Placeholder. The real mapping username -> RBX (target) is
    # unknown from the write-up. This stub returns 0 and must be replaced
    # with the actual logic extracted via dynamic analysis.
    """
    raise NotImplementedError(
        "The username->target mapping is not described in the write-up. "
        "Use the Frida-based dynamic keygen (see DevVolodya's keygen.py) to "
        "capture RBX for a given username, then call target_to_serial(rbx)."
    )


def verify(name: str, serial: str) -> bool:
    """
    Verify (name, serial) pair.

    Because the username->target mapping is unknown, this raises NotImplementedError
    unless _username_to_target() is filled in with the real logic.

    The structural check (serial alphabet validity + transform) is performed;
    the final comparison against the username-derived target cannot be done statically.
    """
    # Step 1: check all chars are in alphabet
    if not serial or any(ch not in ALPH_MAP for ch in serial):
        return False
    # Step 2: decode and re-encode must be round-trippable
    parsed = decode_serial(serial)
    if parsed is None:
        return False
    # Step 3: compute target
    computed_target = rol64(parsed ^ CONST_XOR, 23)
    # Step 4: compare against username-derived RBX
    # ASSUMPTION: _username_to_target is a stub; real logic unknown
    try:
        expected_target = _username_to_target(name)
    except NotImplementedError:
        raise
    return computed_target == expected_target


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given username.

    Requires the real _username_to_target() to be implemented, OR
    use the dynamic Frida approach from DevVolodya's write-up:
      1. Launch crackme.exe
      2. Hook 0x1400B6779, capture RBX
      3. Call target_to_serial(rbx)
    """
    # ASSUMPTION: _username_to_target is a stub; real logic unknown
    target = _username_to_target(name)  # will raise NotImplementedError
    return target_to_serial(target)


def keygen_from_captured_rbx(rbx: int) -> str:
    """
    Given a dynamically captured RBX value (via Frida), produce the correct serial.
    This is the fully working path described in the write-up.
    """
    return target_to_serial(rbx)



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
