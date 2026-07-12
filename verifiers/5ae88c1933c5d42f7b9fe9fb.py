import math
import hashlib

# Based on the XpoZed writeup for AGZ Crackme 5 (TheClueCreator, Java)
# The crackme takes a username (string) and a serial (double/number string)
# The writeup was truncated before the full algorithm was shown, so we reconstruct
# what we can from the described flow:
#
# main() flow:
#   1. Read username (equals1)
#   2. Read serial (equals2) - must be parseable as Double
#   3. double1 = Double.parseDouble(equals2)
#   4. decode = decode(double1)          -- some transform on the serial
#   5. decode2 = decode(availableProcessors(equals1))  -- some transform on username
#   6. n = (int)decode2
#   7. n2 = (int)decode
#   8. length(getDecoder(decode2, double1))  -- compare result
#
# The writeup shows:
#   getDecoder(double n, double n2) -> bool: compares Double.toString(n) with Double.toString(n2)
#   i.e., getDecoder(decode2, double1) checks decode2 == double1 (as strings)
#   So the check is: decode(availableProcessors(username)) == double1 (the serial)
#   i.e., serial == decode(availableProcessors(username))
#
# availableProcessors(username): ASSUMPTION: converts username to some numeric value
#   possibly sum of char values, or some hash-derived double
# decode(x): ASSUMPTION: some mathematical transformation (e.g., sqrt, log, or simple arithmetic)
#
# Since the writeup was truncated, we cannot recover the exact decode() and
# availableProcessors() implementations. We mark all internals as ASSUMPTION.

def available_processors(name: str) -> float:
    # ASSUMPTION: 'availableProcessors' method converts username string to a double
    # Possibly sum of ASCII values, or a checksum-based approach
    # The method name suggests it might just be a renamed function
    # ASSUMPTION: it computes sum of ord(c) for c in name as a float
    result = 0
    for c in name:
        result += ord(c)
    return float(result)

def decode(x: float) -> float:
    # ASSUMPTION: 'decode' is some mathematical or bitwise transformation of the double
    # The writeup was truncated before revealing the body of decode()
    # Common approaches: square root, log, or simple arithmetic like x * constant
    # ASSUMPTION: decode(x) = math.sqrt(x) based on common crackme patterns
    # This is highly uncertain.
    return math.sqrt(x)

def verify(name: str, serial: str) -> bool:
    """
    Verify username + serial pair.
    Based on truncated writeup - partial reconstruction.
    """
    try:
        double1 = float(serial)  # serial must be parseable as Double
    except (ValueError, TypeError):
        return False

    # decode2 = decode(availableProcessors(name))
    # The check is: getDecoder(decode2, double1)
    # getDecoder compares Double.toString(decode2) == Double.toString(double1)
    # i.e., decode2 == double1 numerically (via string comparison)

    inner = available_processors(name)  # ASSUMPTION: see above
    decode2 = decode(inner)             # ASSUMPTION: see above

    # Compare as Java Double.toString would
    # ASSUMPTION: simple equality of float values
    return abs(decode2 - double1) < 1e-10

def keygen(name: str) -> str:
    """
    Generate a valid serial for the given username.
    """
    inner = available_processors(name)  # ASSUMPTION
    serial_value = decode(inner)        # ASSUMPTION
    # Return as Java Double.toString format
    return str(serial_value)


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
