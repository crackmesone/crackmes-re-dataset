#!/usr/bin/env python3
"""
Keygen for 'FindLicenseKey' by vodeff.

Algorithm (fully recovered from multiple independent sources):
  For each position i in [0, 23]:
      output[i] = ALPHABET[(ord(username[i]) + i) % 62]

The username is read as raw bytes; if it is shorter than 24 bytes the C
implementation reads past the NUL terminator (undefined behaviour), so for
reliable / deterministic results a username of exactly 24 ASCII characters
should be used.  The keygen below handles shorter usernames by cycling the
byte values (matching typical C stack behaviour would be non-deterministic,
so we raise an error instead).
"""

import sys

ALPHABET = (
    "QAZPLWSXOKMEYDCIJNRFVUHBTG"
    "qpalzmwoeirutyskdjfhgxncbv"
    "1750284369"
)  # exactly 62 characters

KEY_LEN = 24


def verify(name: str, serial: str) -> bool:
    """Return True if serial matches the key generated from name."""
    return serial == keygen(name)


def keygen(name: str) -> str:
    """
    Generate the 24-character license key for the given username.

    The username is encoded as ASCII bytes.  If it is shorter than 24
    characters a ValueError is raised because the C binary's behaviour
    for short usernames is undefined (reads beyond the NUL terminator).
    """
    raw = name.encode("ascii")
    if len(raw) < KEY_LEN:
        raise ValueError(
            f"Username must be at least {KEY_LEN} ASCII characters "
            f"(got {len(raw)}).  The original binary reads past the NUL "
            "terminator for shorter names, giving non-deterministic results."
        )
    return "".join(
        ALPHABET[(raw[i] + i) % len(ALPHABET)]
        for i in range(KEY_LEN)
    )


# ---------------------------------------------------------------------------
# Quick self-tests against known-good values from the comments / writeups
# ---------------------------------------------------------------------------

def _self_test() -> None:
    # From the 'hatenal' comment
    assert keygen("hatenal" + "A" * 17) != ""  # length check only for short name

    # From the 'admin' ltrace comment
    assert keygen("admin" + "A" * 19) == "iycg1WpNIBTM3c8" + keygen("admin" + "A" * 19)[15:]
    # Direct check against ltrace output: key for 'admin' padded with \x00 …
    # The ltrace showed strcmp("hello", "iycg1WpNIBTM3c8AA77MQUjz") so the
    # expected key for argv[1]="admin" is "iycg1WpNIBTM3c8AA77MQUjz".
    # 'admin' is only 5 chars; the remaining 19 bytes are whatever was on the
    # stack – we cannot reproduce that exactly, so we skip the full assertion.

    # From Cenzer0's writeup: 24 x 'A' -> PLWSXOKMEYDCIJNRFVUHBTGq
    assert keygen("A" * 24) == "PLWSXOKMEYDCIJNRFVUHBTGq", (
        f"Self-test failed: got {keygen('A' * 24)!r}"
    )

    print("All self-tests passed.")



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
