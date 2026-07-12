# Reconstructed from the writeup for 'KeyGenMe #2 by synapse'
# The writeup shows the serial validation and the beginning of the serial
# calculation routine at 004061A4, but the writeup was truncated before
# showing the full lookup-string construction and final comparison.
#
# What is FULLY known from the writeup:
#   serial[0]  == name[1]   (second char of name)
#   serial[1]  == '.'       (literal dot)
#   serial[6]  == '-'       (literal dash)
#
# The calculation routine at 004061A4 computes:
#   edx  = name[0]*4 + name[1] + name[2]*2 + name[3]*11
#   esi  = edx
#   edx  = esi * esi          (edx = esi^2)
#   eax  = ecx * edx          (ecx was EAX at call-site; set to 0 at 004063F9 => ecx=0)
#   eax  = eax * 2
#   eax ^= 0x4035A4
#   stored at [404448]
#
# ASSUMPTION: Because ECX=0 at call time (MOV EAX,0 then MOV ECX,EAX),
#   the MUL/ADD chain produces eax=0, so eax = 0 XOR 0x4035A4 = 0x4035A4.
#
# Then the routine builds a lookup/serial string using name chars and that value.
# The writeup was TRUNCATED, so the exact serial format beyond positions 0,1,6
# is UNKNOWN from the text alone.
#
# A plausible (partial) reconstruction:
#   serial = name[1] + '.' + ??? + '-' + ???
# The full keygen cannot be built without the rest of the routine.

def _compute_intermediate(name):
    """Computes the intermediate value stored at [404448]."""
    if len(name) < 4:
        return None
    n0 = ord(name[0])
    n1 = ord(name[1])
    n2 = ord(name[2])
    n3 = ord(name[3])
    edx = (n0 * 4 + n1 + n2 * 2 + n3 * 11) & 0xFFFFFFFF
    esi = edx
    edx = (esi * esi) & 0xFFFFFFFF
    # ASSUMPTION: ECX == 0 when 004061A4 is called (set via MOV EAX,0; MOV ECX,EAX at 004063F9)
    ecx = 0
    eax = (ecx * edx) & 0xFFFFFFFF
    eax = (eax * 2) & 0xFFFFFFFF
    eax ^= 0x4035A4
    return eax


def verify(name, serial):
    """Verify a name/serial pair against the known checks."""
    if len(name) < 4:
        return False
    if len(serial) < 7:
        return False
    # Check 1: serial[0] == name[1]
    if serial[0] != name[1]:
        return False
    # Check 2: serial[1] == '.'
    if serial[1] != '.':
        return False
    # Check 3: serial[6] == '-'
    if serial[6] != '-':
        return False
    # ASSUMPTION: The rest of the serial depends on the truncated part of the
    # routine at 004061A4 which we cannot fully reconstruct.
    # We cannot fully verify the serial without that information.
    # Returning True here only means the three known checks pass.
    intermediate = _compute_intermediate(name)
    # ASSUMPTION: intermediate value is used to build chars at positions 2-5 and 7+
    # but the exact encoding (lookup table at 0x403630, etc.) is unknown.
    return True  # PARTIAL: only checks positions 0, 1, 6


def keygen(name):
    """Generate a serial for the given name.
    PARTIAL: only positions 0, 1, and 6 are known; positions 2-5 and 7+
    are filled with placeholders because the writeup was truncated.
    """
    if len(name) < 4:
        raise ValueError('Name must be at least 4 characters long')
    c1 = name[1]          # serial[0] = second char of name
    dot = '.'
    dash = '-'
    intermediate = _compute_intermediate(name)
    # ASSUMPTION: positions 2-5 before the dash and positions 7+ after the dash
    # are derived from name chars and the intermediate value via a lookup table
    # at address 0x403630 (call to 0x406547). We do not have that table.
    # Using hex of intermediate as a stand-in placeholder.
    placeholder = '{:08X}'.format(intermediate)
    # Build: serial[0]=name[1], serial[1]='.', serial[2..5]=????, serial[6]='-', serial[7+]=????
    # ASSUMPTION: 4 chars between '.' and '-', and 4+ chars after '-'
    between = placeholder[:4]   # ASSUMPTION
    after   = placeholder[4:]   # ASSUMPTION
    serial = c1 + dot + between + dash + after
    return serial



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
