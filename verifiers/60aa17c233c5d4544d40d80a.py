# Reverse-engineered algorithm for 'spank me v1' by mohammadali
# Based on the writeup by pranav and comments in the crackme thread.
#
# Summary of the algorithm (from disassembly walkthrough):
#   1. Read name (username) string.
#   2. Compute checksum_uname from the name:
#        - For each character c in name: checksum_uname = (c ^ 2) * 2
#          (only the LAST character matters because each iteration overwrites)
#        - Let L = len(name) + 100  (add 0x64)
#        - If checksum_uname != 0: checksum_uname *= L
#        - If checksum_uname > 0 and checksum_uname > 0x64:
#              checksum_uname *= L
#              L = L*2 + 0x258
#              checksum_uname = checksum_uname * L + checksum_uname
#   3. Read input_serial (numeric).
#   4. Transform input_serial:
#        input_serial = (input_serial ^ 1) + (input_serial ^ 2) + (input_serial ^ 3)
#   5. Comparison: the program checks checksum_uname == input_serial (transformed).
#      The final check actually tests whether (checksum_uname - transformed_serial) == 0.
#   6. Additionally, strlen(name) + result_flag must equal strlen(name) + 1,
#      meaning result_flag must be 1, i.e. checksum_uname == transformed_serial.
#
# PATCHING NOTE from pranav:
#   The intended 'reversing' path involves patching the IsDebuggerPresent check.
#   The XOR transformation on the serial can be worked around by noting:
#     (x^1) + (x^2) + (x^3) ~= 3*x for large x (within a few bits).
#   The exact way to reverse: given code = checksum_uname, find x such that
#     (x^1)+(x^2)+(x^3) == code.
#   pranav's approach: set all XOR args to 0, so serial = code/3 exactly.
#   We implement both: exact brute-force search and the /3 approximation.

def compute_checksum(name: str) -> int:
    if not name:
        # ASSUMPTION: empty name produces checksum 0
        return 0

    # Only the last character matters (each iteration overwrites)
    c = ord(name[-1])
    checksum_uname = (c ^ 2) * 2

    L = len(name) + 0x64  # add 100 (0x64)

    if checksum_uname != 0:
        checksum_uname = checksum_uname * L

    if checksum_uname > 0 and checksum_uname > 0x64:
        checksum_uname = checksum_uname * L
        L = L * 2 + 0x258
        checksum_uname = checksum_uname * L + checksum_uname

    # ASSUMPTION: arithmetic is 32-bit unsigned (wrap at 2^32)
    checksum_uname = checksum_uname & 0xFFFFFFFF
    return checksum_uname


def transform_serial(x: int) -> int:
    """Apply the XOR transformation from the crackme source:
       input_serial = (input_serial ^ 1) + (input_serial ^ 2) + (input_serial ^ 3)
    """
    return ((x ^ 1) + (x ^ 2) + (x ^ 3)) & 0xFFFFFFFF


def verify(name: str, serial: str) -> bool:
    """Verify a name/serial pair.
    serial is a string representation of an integer.
    """
    try:
        input_serial = int(serial)
    except ValueError:
        return False

    code = compute_checksum(name)
    transformed = transform_serial(input_serial)
    return transformed == code


def _find_preimage(code: int) -> int:
    """Find x such that transform_serial(x) == code.
    Uses approximation x ~ code/3, then searches nearby.
    """
    # From pranav: setting XOR args to 0 gives serial = code/3
    # Search in a window around code//3
    approx = code // 3
    search_range = 16  # small window; XOR with 1,2,3 only flips low bits
    for delta in range(-search_range, search_range + 1):
        candidate = approx + delta
        if candidate >= 0 and transform_serial(candidate) == code:
            return candidate
    # Wider search fallback
    # ASSUMPTION: if not found in small window, try brute force up to 2^24
    for candidate in range(0, 2**24):
        if transform_serial(candidate) == code:
            return candidate
    raise ValueError(f'Could not find preimage for code={code}')


def keygen(name: str) -> str:
    """Generate a valid serial for the given name."""
    code = compute_checksum(name)
    x = _find_preimage(code)
    return str(x)



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
