# Reverse-engineered algorithm for tJw's Crackme#5
# Based on: solution writeup by Zephyrous (internal keygen / OllyDbg patching)
#
# The writeup does NOT reveal the actual serial generation algorithm.
# The cracker used an 'internal keygen' approach: patching the binary to
# display the correct serial instead of comparing against user input.
# Only two example name/serial pairs are given:
#   Name: Zephyrous  -> Serial: C5H18Q30-K110X55R66-P152T91S102
#   Name: [+tJw+]   -> Serial: A5C17T30-C103V55C65-B138
#
# From these examples we can observe the serial structure:
#   - Groups separated by '-'
#   - Each group appears to be: Letter + number + Letter + number + ...
#   - Numbers seem to grow larger in later groups
#
# Without the actual VBA source or a full disassembly trace showing how
# the serial is computed, we cannot reconstruct the algorithm.
# The function below is a STUB that only validates against known pairs.

KNOWN = {
    'Zephyrous': 'C5H18Q30-K110X55R66-P152T91S102',
    '[+tJw+]':   'A5C17T30-C103V55C65-B138',
}

def verify(name: str, serial: str) -> bool:
    """Verify name/serial pair.
    ASSUMPTION: Only validates against known pairs from the writeup.
    The real algorithm was never published; only an internal keygen
    (binary patch) approach was described.
    """
    # ASSUMPTION: Serial comparison is case-sensitive (VBA __vbaStrCmp)
    expected = KNOWN.get(name)
    if expected is not None:
        return serial == expected
    # ASSUMPTION: For unknown names we cannot compute the serial.
    raise NotImplementedError(
        "The actual serial generation algorithm was not described in the writeup. "
        "Only an 'internal keygen' (binary patch) approach was used by the cracker."
    )

def keygen(name: str) -> str:
    """Return a valid serial for the given name.
    ASSUMPTION: Only known pairs from the writeup are returnable.
    """
    if name in KNOWN:
        return KNOWN[name]
    raise NotImplementedError(
        "Serial generation algorithm not recovered from the available writeup. "
        "The cracker patched the binary to display the serial rather than "
        "reverse-engineering the computation."
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
