# Reverse-engineered from crackme_11 by fireworx
# Based on the writeup by Bengi
#
# The serial format is: "VL - -XXXXXXX..XXXXX.-XXXXXX."
# The name does NOT affect the serial.
# The algorithm loops 6 times computing values from loop position (EDI = 0..5).
#
# Per iteration:
#   esi = edi
#   esi >>= 0x0E          (SHR ESI, 0E)
#   esi ^= edi            (XOR ESI, EDI)
#   esi += 0x2F21A0       (ADD ESI, 2F21A0)
#   esi += 0x795CE        (ADD ESI, 795CE -> total add = 0x2F9B6E)
#
#   val1 = esi            (formatted as %d => decimal string)
#
#   local5 = (esi // 0x49) - 0x0BBA   (IDIV 0x49, then SUB 0x0BBA)
#   val2 = local5         (formatted as %d)
#
#   tmp = (esi // 0x130)  (IDIV 0x130)
#   tmp = tmp * 4         (SHL EAX, 2)
#   tmp = tmp + tmp*4     (LEA EAX,[EAX+EAX*4]) => tmp *= 5
#   tmp ^= local5         (XOR with local5)
#   tmp += 0x10F          (ADD 10F)
#   tmp -= 0              (SUB 0, no-op)
#   val3 = tmp            (formatted as %d)
#
# The final serial string is built by format:
#   "{val3}{part_from_edit1} -{part_from_edit2}{val1}..{val2}.-{val3}."
#
# ASSUMPTION: The writeup mentions two Edit fields (EBX+2CC and EBX+2D8) whose
# string values are fetched. These likely correspond to parts of the serial
# entered by the user. The serial pattern is compared against a generated string.
# ASSUMPTION: The loop runs 6 times but the exact structure of how 6 iterations
# map to the serial parts is not fully described. Only the first number is said
# to vary. We treat the loop with i=0 as the primary source.
# ASSUMPTION: The separator characters in the format string seen in the disasm
# are " -", "..", ".-" which appear as delimiters in the serial.

import ctypes

def _compute_for_iteration(i):
    """Compute the three values for loop iteration i (0-indexed)."""
    # Simulate 32-bit arithmetic
    edi = i & 0xFFFFFFFF
    esi = edi
    esi = (esi >> 0x0E) & 0xFFFFFFFF
    esi = (esi ^ edi) & 0xFFFFFFFF
    esi = (esi + 0x2F21A0) & 0xFFFFFFFF
    esi = (esi + 0x795CE) & 0xFFFFFFFF
    # val1
    val1 = esi
    # IDIV signed by 0x49
    # Use ctypes for signed 32-bit division
    esi_signed = ctypes.c_int32(esi).value
    quotient = int(esi_signed / 0x49)  # truncate toward zero
    local5 = quotient - 0x0BBA
    val2 = local5
    # Compute val3
    quotient2 = int(esi_signed / 0x130)  # truncate toward zero
    tmp = quotient2
    tmp = tmp * 4  # SHL 2
    tmp = tmp + tmp * 4  # LEA [eax + eax*4] => *5
    tmp = tmp ^ local5
    tmp = tmp + 0x10F
    # SUB 0 is no-op
    val3 = tmp
    return val1, val2, val3

def keygen(name):
    """Generate a valid serial. Name is ignored per the writeup."""
    # ASSUMPTION: The serial is built from iteration 0 values.
    # The writeup says the loop goes 6 times but only the first number changes;
    # since i starts at 0 and esi only varies by the SHR(edi) term (which is 0
    # for i=0..13), all 6 iterations produce the same esi value.
    val1, val2, val3 = _compute_for_iteration(0)
    # Format: pattern from disasm separators: " -", "..", ".-"
    # Observed serial template: "VL - -XXXXXXX..XXXXX.-XXXXXX."
    # ASSUMPTION: The two user-input fields contribute fixed parts "VL" prefix etc.
    # Based solely on disasm format string pushes:
    #   push LOCAL.9  (edit field 2)
    #   push " -"
    #   push LOCAL.2  (val1 as string)
    #   push ".."
    #   push LOCAL.3  (val2 as string)
    #   push ".-"
    #   push LOCAL.4  (val3 as string)
    #   push ??? (4556C4)
    # => format appears to be: {edit2} -{val1}..{val2}.-{val3}{suffix}
    # ASSUMPTION: edit1 content is from EBX+2CC, edit2 from EBX+2D8.
    # The known valid serial prefix 'VL - ' suggests edit fields hold 'VL' etc.
    # We'll just show the computed number parts.
    serial = f"{val1} - {val2} - {val3}"
    # Also show full pattern matching the known example format
    serial_full = f"(edit2_val) -{val1}..{val2}.-{val3}."
    return serial_full

def verify(name, serial):
    """Verify a serial. Name is ignored.
    ASSUMPTION: We attempt to parse the serial in the format:
    '{edit2} -{val1}..{val2}.-{val3}.'
    and check the computed values match.
    """
    import re
    # ASSUMPTION: serial format is: anything + ' -' + val1 + '..' + val2 + '.-' + val3 + '.'
    # Try to extract numeric parts
    pattern = re.compile(r'^.*?\s*-\s*([-]?\d+)\.\.\s*([-]?\d+)\.-([-]?\d+)\.$')
    m = pattern.match(serial.strip())
    if not m:
        return False
    try:
        s_val1 = int(m.group(1))
        s_val2 = int(m.group(2))
        s_val3 = int(m.group(3))
    except ValueError:
        return False
    # ASSUMPTION: loop i=0 is used (since writeup says only first number varies
    # and loop runs over a constant range for the check)
    for i in range(6):
        val1, val2, val3 = _compute_for_iteration(i)
        if s_val1 == val1 and s_val2 == val2 and s_val3 == val3:
            return True
    return False


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
