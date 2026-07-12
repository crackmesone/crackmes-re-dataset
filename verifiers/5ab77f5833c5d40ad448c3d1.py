# Reconstructed algorithm for eval_n4 by ezqui3l
# Based on the IDA disassembly writeup (truncated)
#
# Serial format: 5 parts entered as integers (part0..part4)
# Name must be > 4 characters
# The writeup was truncated before showing the full math,
# so some steps are ASSUMPTION-marked.

def compute_name_hash(name):
    """Compute a hash/sum from the name characters."""
    # The writeup shows iterating over name chars into tmp_array
    # and accumulating something. The exact operation is truncated.
    # ASSUMPTION: simple sum of ord values
    total = 0
    for ch in name:
        total += ord(ch)
    return total

def verify(name, serial):
    """
    serial is expected as a string in the form 'p0-p1-p2-p3-p4'
    or a list/tuple of 5 integer parts.
    Name must be longer than 4 characters.
    """
    if isinstance(serial, str):
        parts = serial.split('-')
        if len(parts) != 5:
            return False
        try:
            ipart0, ipart1, ipart2, ipart3, ipart4 = [int(p) for p in parts]
        except ValueError:
            return False
    else:
        try:
            ipart0, ipart1, ipart2, ipart3, ipart4 = serial
        except Exception:
            return False

    # Name length must be > 4
    if len(name) <= 4:
        return False

    # Anti-debug: step_dword must equal 2 (find_olly not found)
    # In a keygen context we skip the anti-debug check and assume
    # it passes (step==2, calc_value1==0 meaning no debugger found).
    # The writeup says if step != 2, ipart1=ipart2=ipart3=0x7B=123
    # which forces invalid. We assume step==2 for a clean run.

    # ASSUMPTION: name hash drives the serial computation.
    # The writeup was truncated before revealing the exact formula.
    # Based on typical crackme patterns and partial disassembly showing
    # name chars being accumulated:

    name_hash = compute_name_hash(name)
    name_len  = len(name)

    # ASSUMPTION: derived from common patterns seen in similar crackmes
    # ipart0 = name_hash
    # ipart1 = name_hash * name_len
    # ipart2 = ipart1 - ipart0
    # ipart3 = ipart0 ^ ipart1
    # ipart4 = (ipart0 + ipart1 + ipart2 + ipart3) % 10000

    expected0 = name_hash
    expected1 = name_hash * name_len
    expected2 = expected1 - expected0
    expected3 = expected0 ^ expected1
    expected4 = (expected0 + expected1 + expected2 + expected3) % 10000

    return (ipart0 == expected0 and
            ipart1 == expected1 and
            ipart2 == expected2 and
            ipart3 == expected3 and
            ipart4 == expected4)


def keygen(name):
    """
    Generate a serial string 'p0-p1-p2-p3-p4' for the given name.
    Requires name length > 4.
    """
    if len(name) <= 4:
        raise ValueError("Name must be longer than 4 characters")

    name_hash = compute_name_hash(name)
    name_len  = len(name)

    # ASSUMPTION: same as verify
    p0 = name_hash
    p1 = name_hash * name_len
    p2 = p1 - p0
    p3 = p0 ^ p1
    p4 = (p0 + p1 + p2 + p3) % 10000

    return f"{p0}-{p1}-{p2}-{p3}-{p4}"



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
