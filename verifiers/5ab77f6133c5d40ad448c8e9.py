# secretme_2 by hmx0101
# Reverse-engineered from the solution writeup by br0ken
#
# What we know from the writeup:
# 1. The crackme is a Delphi 6/7 binary.
# 2. It reads the computer name.
# 3. It compares the computer name to the hardcoded string "HMX0101".
#    If they don't match => badboy (no serial generation at all).
# 4. It generates a serial from the computer name.
# 5. The generated serial is compared to a hardcoded serial.
# 6. For computer name "HMX0101", the hardcoded serial is "1075411813".
# 7. The reverser's computer name (unknown) produced serial "1016613794".
#
# The actual serial generation algorithm is described as "very very big"
# and was NOT documented in the writeup. We only have two data points:
#   "HMX0101"  -> "1075411813"
#   <unknown>  -> "1016613794"
#
# ASSUMPTION: We attempt a simple sum-of-ASCII-values style algorithm
# and check it against the known pair. This is a GUESS since the real
# algorithm was not disclosed.

def _generate_serial_attempt(name: str) -> str:
    # ASSUMPTION: The real algorithm is complex Delphi code not disclosed.
    # We try a weighted sum as a placeholder guess.
    # Known: "HMX0101" -> 1075411813
    # H=72, M=77, X=88, 0=48, 1=49, 0=48, 1=49
    # Simple sum = 72+77+88+48+49+48+49 = 431  (does not match 1075411813)
    # The algorithm is clearly more complex (possibly involves large multiplications,
    # Delphi string hashing, or CRC-like operations).
    # Without the actual disassembly or more data points, we cannot recover it.
    # ASSUMPTION: Return None to indicate we cannot compute.
    return None


def verify(name: str, serial: str) -> bool:
    """
    Verify a (name, serial) pair for secretme_2.

    Based on the writeup:
    - The crackme ONLY accepts computer name == "HMX0101" without patching.
    - For name "HMX0101", the valid serial is "1075411813" (hardcoded in the binary).
    - For any other name, a serial is generated from the name and compared to
      "HMX0101"'s hardcoded serial -- but the generation algorithm is unknown.
    """
    # ASSUMPTION: The first check requires the name to be exactly "HMX0101"
    # (the hardcoded value in the binary). Without patching, any other name fails.
    if name != "HMX0101":
        # ASSUMPTION: Other names would need a keygen we cannot implement.
        # Return False since we cannot verify other names.
        return False

    # For "HMX0101", the hardcoded serial from the writeup is "1075411813"
    return serial == "1075411813"


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.

    ASSUMPTION: Only "HMX0101" is supported because:
    - The real serial generation algorithm was not documented.
    - We only know the serial for "HMX0101" from the writeup.
    """
    if name == "HMX0101":
        return "1075411813"
    # ASSUMPTION: Cannot generate serials for other names without the algorithm.
    raise NotImplementedError(
        f"Serial generation algorithm unknown. "
        f"Only 'HMX0101' -> '1075411813' is known from the writeup. "
        f"For name '{name}', the real Delphi algorithm must be reversed."
    )



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
