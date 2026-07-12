# Reverse-engineered from moon's CrackMe#3 (Delphi 5/6)
# Based on the writeup analysis of Button1Click procedures in Unit1 and Unit2

def _compute_hash_level3(bypass_code: int) -> int:
    """Compute hash for level 3 password check."""
    h = 0
    for i in range(1, 5):  # i = 1..4
        val = bypass_code
        val ^= 1234          # xor eax, 0x4D2
        val += 15            # add eax, 0x0F
        val = (val << 3) & 0xFFFFFFFF  # shl eax, 3
        val ^= 0x11          # xor eax, 17
        # cdq + idiv esi => signed division; simulate with Python int
        # Convert val to signed 32-bit
        if val >= 0x80000000:
            val -= 0x100000000
        quotient = int(val) // i  # integer (truncating) division
        h += quotient
    return h


def keygen_level3() -> int:
    """Brute-force the level-3 password (4-digit number 0-9999)."""
    for candidate in range(10000):
        if _compute_hash_level3(candidate) == 0x13488:
            return candidate
    return -1


# Level-3 password is fixed (does not depend on name)
LEVEL3_PASSWORD = 5792  # found by brute-force per writeup


# ---------------------------------------------------------------------------
# Level-4 Name/Serial keygen
# The writeup was truncated before fully describing the serial algorithm.
# What we know from the text:
#   - Name must be >= 4 characters
#   - Serial length is also checked (exact check value truncated)
#   - The algorithm uses character ASCII values from the name
# ---------------------------------------------------------------------------

def _serial_from_name(name: str) -> str:
    # ASSUMPTION: The serial generation iterates over name characters and
    # accumulates some hash, similar in style to the level-3 check.
    # The writeup was truncated so the exact algorithm is unknown.
    # Below is a placeholder that always returns an empty string.
    # Replace this body once the full algorithm is recovered.
    raise NotImplementedError(
        "Level-4 serial algorithm not fully described in writeup (truncated). "
        "Cannot implement keygen without the complete disassembly."
    )


def verify(name: str, serial: str) -> bool:
    """Verify a name/serial pair for Level 4.
    Returns True if valid, False otherwise.
    The serial algorithm was truncated in the writeup, so this is partial."""
    # Check 1: name length >= 4
    if len(name) < 4:
        return False
    # ASSUMPTION: Serial length must be >= 4 (truncated from writeup)
    if len(serial) < 4:
        return False
    # ASSUMPTION: The actual serial value is derived from the name via
    # character-based arithmetic. We cannot verify without the full algorithm.
    try:
        expected = _serial_from_name(name)
        return serial == expected
    except NotImplementedError:
        return False  # Algorithm not fully recovered


def keygen(name: str) -> str:
    """Generate a valid serial for the given name (Level 4)."""
    if len(name) < 4:
        raise ValueError("Name must be at least 4 characters.")
    # ASSUMPTION: Serial is derived deterministically from the name.
    return _serial_from_name(name)



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
