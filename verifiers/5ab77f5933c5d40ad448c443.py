# Moofy's NamegenMe - reverse engineered algorithm
#
# HOW IT WORKS (from the writeup/solution):
#
# 1. The program generates a 10-char base string using rand() seeded with time().
#    Each char: (rand() % 26) + ord('a')  -- ASSUMPTION based on the example
#    Example base string: 'jntqvwquc{' (though '{' suggests modulo may be slightly off)
#
# 2. The serial is built from the base string split as AAA BBB CCC D:
#    serial = base[0:3] + '-11' + base[3:6] + '-522' + base[6:9] + '-914' + base[9] + 'mf-y'
#    Total length = 3+3+3+3+3+3+3+3+1+4 = ... let's count:
#    'AAA-11BBB-522CCC-914Dmf-y' = 3+1+2+3+1+3+3+1+3+3+1+4 = 25 chars
#
# 3. The NAME is derived FROM the serial (it's a nameGENme - serial->name direction).
#    From the second solution (base.asm), the name is derived from the serial as follows:
#    Extract chars from serial at positions: 0,1,2 (AAA), 6,7,8 (BBB, skipping '-11'),
#    13,14,15 (CCC, skipping '-522'), 20 (D, skipping '-914')
#    These 10 bytes are placed into szSerialName, then transformed:
#      name[0] += 4
#      name[1] -= 3
#      name[2] -= 2
#      name[3] += 2
#      name[4] -= 1
#      name[5] += 3
#      name[6] -= 2
#      name[7] -= 4
#      name[8] += 3
#      name[9] += 1
#
# NOTE: The crackme is actually a serial->name tool (given serial, compute name).
# The 'namegen' solution reconstructs the name from a serial.
# For verify(name, serial): check that deriving the name from the serial matches.

def serial_to_name(serial):
    """Given a valid 25-char serial, derive the corresponding name."""
    if len(serial) != 25:
        return None
    # Check format dashes at positions 3, 9, 16, 23
    # Serial format: XXX-11YYY-522ZZZ-914Wmf-y
    # Positions:      0123456789...
    # dash at 3, then '11' at 4-5, dash at 9 (after BBB at 6,7,8)
    # Wait, let's re-read: 'AAA-11BBB-522CCC-914Dmf-y'
    # pos: 0=A,1=A,2=A,3=-,4=1,5=1,6=B,7=B,8=B,9=-,10=5,11=2,12=2,13=C,14=C,15=C,16=-,17=9,18=1,19=4,20=D,21=m,22=f,23=-,24=y
    # Dashes at positions 3, 9, 16, 23
    if serial[3] != '-' or serial[9] != '-' or serial[16] != '-' or serial[23] != '-':
        return None
    
    # Extract base chars from serial (asm code):
    # mov eax, dword ptr [edi]     -> 4 bytes at 0,1,2,3 but only 3 used? Actually dword = 4 bytes
    # [esi] = [edi+0..3] (4 bytes: positions 0,1,2,3 -> but pos 3 is '-')
    # mov eax, [edi+6] -> 4 bytes at 6,7,8,9
    # mov [esi+3] = those 4 bytes
    # mov eax, [edi+13] -> 4 bytes at 13,14,15,16
    # mov [esi+6] = those 4 bytes
    # movzx eax, byte ptr [edi+20] -> 1 byte at 20
    # mov word ptr [esi+9], ax
    # So szSerialName gets:
    # [0..3] = serial[0..3] (AAA-)
    # [3..6] = serial[6..9] (BBB-)
    # [6..9] = serial[13..16] (CCC-)
    # [9..10] = serial[20] (D)
    # But only indices 0..9 are used for the name transformation
    # Index 0 = serial[0], 1=serial[1], 2=serial[2], 3=serial[6], 4=serial[7], 5=serial[8]
    # Index 6 = serial[13], 7=serial[14], 8=serial[15], 9=serial[20]
    
    base = [
        ord(serial[0]),
        ord(serial[1]),
        ord(serial[2]),
        ord(serial[6]),
        ord(serial[7]),
        ord(serial[8]),
        ord(serial[13]),
        ord(serial[14]),
        ord(serial[15]),
        ord(serial[20]),
    ]
    
    # Apply transformations
    base[0] += 4
    base[1] -= 3
    base[2] -= 2
    base[3] += 2
    base[4] -= 1
    base[5] += 3
    base[6] -= 2
    base[7] -= 4
    base[8] += 3
    base[9] += 1
    
    name = ''.join(chr(b & 0xFF) for b in base)
    return name


def verify(name, serial):
    """Check if the given serial produces the given name."""
    if len(serial) != 25:
        return False
    derived = serial_to_name(serial)
    if derived is None:
        return False
    return derived == name


def name_to_base(name):
    """Given a 10-char name, invert the transformation to get the base string."""
    if len(name) < 10:
        return None
    base = list(ord(c) for c in name[:10])
    # Invert the transformations
    base[0] -= 4
    base[1] += 3
    base[2] += 2
    base[3] -= 2
    base[4] += 1
    base[5] -= 3
    base[6] += 2
    base[7] += 4
    base[8] -= 3
    base[9] -= 1
    return ''.join(chr(b & 0xFF) for b in base)


def keygen(name):
    """Given a 10-char name, produce a valid serial."""
    # ASSUMPTION: name must be exactly 10 characters
    if len(name) != 10:
        raise ValueError("Name must be exactly 10 characters")
    
    base = name_to_base(name)
    # serial = AAA-11BBB-522CCC-914Dmf-y
    # base[0..2] = AAA, base[3..5] = BBB, base[6..8] = CCC, base[9] = D
    serial = base[0:3] + '-11' + base[3:6] + '-522' + base[6:9] + '-914' + base[9] + 'mf-y'
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
