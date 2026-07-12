# Reverse-engineered validation for VB Collection crackme by 3ngma
# Based on solution writeup (Bulgarian text decoded)
#
# The collection contains multiple crackmes (v1.0 through v6.0+).
# Each crackme has a hardcoded or fixed serial described in the writeup.
# Where the algorithm is described, we implement it; otherwise we use the
# known-good hardcoded values from the writeup.

# ASSUMPTION: crackme v3.0 uses VB's Val()/CDbl() on the Name string,
# which returns 0.0 for non-numeric names, then multiplies by (random*45),
# giving 0. So the valid key for any name is "0".

# ASSUMPTION: crackme v2.0 uses fixed multi-part keys (no name dependency).
# ASSUMPTION: crackmes v1, v4, v5 use hardcoded serials (no name dependency).

# Hardcoded serials from writeup
HARDCODED_SERIALS = {
    1: "ECG ROCKS",
    4: "HaRdcOdEd",
    5: "HI DUDE !!!",
}

# Crackme v2.0 fixed multi-part keys
CRACKME2_PARTS = [
    "8716246191",
    "8971254061",
    "1074519145",
    "6123784681",
    "8127341601",
    "19275348511",
]


def verify_v1(name, serial):
    """Crackme v1.0: hardcoded serial comparison, name not used."""
    # ASSUMPTION: name field may exist but serial is hardcoded
    return serial == HARDCODED_SERIALS[1]


def verify_v2(parts):
    """Crackme v2.0: 6 fixed registration key parts.
    parts should be a list/tuple of 6 strings."""
    if len(parts) != 6:
        return False
    return list(parts) == CRACKME2_PARTS


def verify_v3(name, serial):
    """Crackme v3.0: name-key scheme.
    Steps:
      1. Take NAME as a REAL (float) variable via VB's Val()/CDbl().
      2. Generate random number, multiply by 45, save.
      3. Multiply saved number by the NAME-number, save.
      4. Compare entered serial with the result.
    Because VB's Val() of a non-numeric name returns 0.0,
    the result is always 0 for any non-numeric name.
    Valid key for any name is '0'.
    """
    # ASSUMPTION: VB Val() conversion of name string
    try:
        name_val = float(name)
    except ValueError:
        name_val = 0.0
    # ASSUMPTION: random * 45 * name_val => if name_val==0, result is 0
    # We cannot know the random number, but the product is 0 when name_val==0
    if name_val == 0.0:
        expected = 0.0
    else:
        # ASSUMPTION: cannot verify without knowing the random number
        # Return False for numeric names since we can't reproduce the random
        return False
    try:
        return float(serial) == expected
    except ValueError:
        return serial.strip() == "0"


def verify_v4(name, serial):
    """Crackme v4.0: hardcoded serial comparison."""
    # ASSUMPTION: name not used
    return serial == HARDCODED_SERIALS[4]


def verify_v5(name, serial):
    """Crackme v5.0: hardcoded serial comparison."""
    # ASSUMPTION: name not used
    return serial == HARDCODED_SERIALS[5]


def verify(name, serial):
    """Generic verify: tries all known crackmes.
    Returns True if serial matches any known valid key for the given name.
    This is a best-effort wrapper given multiple crackmes in collection.
    """
    # Try v1
    if verify_v1(name, serial):
        return True
    # Try v3 (name-based, key=0 for non-numeric names)
    if verify_v3(name, serial):
        return True
    # Try v4
    if verify_v4(name, serial):
        return True
    # Try v5
    if verify_v5(name, serial):
        return True
    # Try v2 parts (serial as comma-separated)
    parts = [p.strip() for p in serial.split(",")]
    if verify_v2(parts):
        return True
    return False


def keygen(name):
    """Returns a dict of valid serials per crackme version for the given name."""
    results = {
        "v1": HARDCODED_SERIALS[1],
        "v2_parts": CRACKME2_PARTS,
        "v4": HARDCODED_SERIALS[4],
        "v5": HARDCODED_SERIALS[5],
    }
    # v3: key depends on whether name is numeric
    try:
        name_val = float(name)
        if name_val == 0.0:
            results["v3"] = "0"
        else:
            results["v3"] = "UNKNOWN (random number involved, name is numeric)"
    except ValueError:
        results["v3"] = "0"  # Non-numeric name always gives key=0
    return results



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
