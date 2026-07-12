# Reverse-engineered keygen for 'ifucan by st0per'
# Based on the writeup by d@b / IIDKing
#
# The writeup reveals:
#   - Three levels: Easy, Hard, Expert
#   - Serial formats:
#       Easy:   "%u-%u-%u"
#       Hard:   "%u0-O%d"
#       Expert: "ST%u-%u-%u"
#   - The serial is computed from the Name (4+ chars required)
#   - The serial parts are stored in local variables on the stack
#     (EBP-2C, EBP-24, EBP-20 for Level 1 Easy)
#   - The actual computation of serial parts is NOT shown in the writeup
#     (the writeup says "These 3 functions are very very long so I'm not going
#      to repeat them here")
#   - There is also a hardcoded string "st0persays" referenced at 00403314
#     which appears after a failed length check (possibly a fallback/cheat)
#
# ASSUMPTION: The actual arithmetic to derive the serial parts from the name
# is unknown. The writeup only shows the format strings and that parts are
# computed from the name. We cannot implement verify() or keygen() without
# the actual computation. The stubs below reflect what IS known.

def _compute_serial_parts_easy(name):
    # ASSUMPTION: The actual algorithm to derive part1, part2, part3 from
    # `name` is not described in the writeup. These are placeholders.
    # The writeup says values come from EBP-2C, EBP-24, EBP-20 after a
    # long computation involving the name string.
    raise NotImplementedError("Serial computation algorithm not recovered from writeup")

def _compute_serial_parts_hard(name):
    # ASSUMPTION: Same as above for Hard level. Format is "%u0-O%d"
    raise NotImplementedError("Serial computation algorithm not recovered from writeup")

def _compute_serial_parts_expert(name):
    # ASSUMPTION: Same as above for Expert level. Format is "ST%u-%u-%u"
    raise NotImplementedError("Serial computation algorithm not recovered from writeup")

def keygen_easy(name):
    """Generate serial for Easy level using format '%u-%u-%u'"""
    if len(name) < 4:
        raise ValueError("Name must be 4 or more characters")
    p1, p2, p3 = _compute_serial_parts_easy(name)
    return f"{p1}-{p2}-{p3}"

def keygen_hard(name):
    """Generate serial for Hard level using format '%u0-O%d'"""
    if len(name) < 4:
        raise ValueError("Name must be 4 or more characters")
    p1, p2 = _compute_serial_parts_hard(name)
    return f"{p1}0-O{p2}"

def keygen_expert(name):
    """Generate serial for Expert level using format 'ST%u-%u-%u'"""
    if len(name) < 4:
        raise ValueError("Name must be 4 or more characters")
    p1, p2, p3 = _compute_serial_parts_expert(name)
    return f"ST{p1}-{p2}-{p3}"

def keygen(name, level='easy'):
    """Generate serial for given name and level ('easy', 'hard', 'expert')"""
    level = level.lower()
    if level == 'easy':
        return keygen_easy(name)
    elif level == 'hard':
        return keygen_hard(name)
    elif level == 'expert':
        return keygen_expert(name)
    else:
        raise ValueError(f"Unknown level: {level}")

def verify(name, serial, level='easy'):
    """Verify a serial for the given name and level."""
    if len(name) < 4:
        return False
    try:
        expected = keygen(name, level)
        return serial == expected
    except NotImplementedError:
        # ASSUMPTION: Cannot verify without the actual algorithm
        raise NotImplementedError("Cannot verify: serial computation algorithm not recovered")


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
