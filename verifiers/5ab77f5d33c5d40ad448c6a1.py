# RE-TRACE crackme by crudd - keygen/verifier
# Reconstructed from solution writeups (hell_master and bLaCk-eye)
#
# From the readme (decoded from garbled encoding), the algorithm is:
#
# The serial is composed of 3 parts: serial_1, special_byte, serial_2
#
# Conditions:
# 1. Name length must be >= 4
# 2. The 'special byte' is augmented by the length of the group
# 3. If no group: serial_2 XOR seed == function([serial_1]) XOR seed
#    If group:    serial_2 XOR seed == function([serial_1 + 15h units]) XOR seed
#
# TRICK: serial_1 points to the two last bytes of the serial string (0x040303FB)
#        To precalculate the return of the function for a given string (i.e. '01')
#        set serial_2 to this value
#
# From the ASM keygen (bLaCk-eye), the Generate procedure:
#   - Calls Checksum on szname
#   - Calls Checksum on szcompany
#   - sum = checksum(name) + checksum(company)
#   - company_len += 47h
#   - serial[8] = al  (some byte derived from sum)
#   - converts checksum to string
#
# Checksum procedure (from kEYGEN.Asm, partially decoded):
#   XOR-based rolling checksum with multiplication
#   The loop processes each byte: checksum = checksum*some_factor XOR byte
#   From the code pattern: checksum += C6h; compare, conditional add
#   Then shr ebx,4; process next nibble
#   The code references 'make_sum' with XOR and MUL operations
#
# ASSUMPTION: The checksum is a simple sum of character values with some transformation
# ASSUMPTION: The serial format is hex string of computed values
# ASSUMPTION: Group field is optional; if empty, uses no-group path

def _checksum(s):
    """
    ASSUMPTION: Rolling checksum approximated from ASM code pattern.
    The ASM shows: XOR ecx,ecx; then loop: mov al,[ecx+szname]; xor eax,eax;
    add al,47h (or 37h for <9); shr ebx,4; mul bl; add eax,[ecx+3]
    This is a best-effort reconstruction.
    """
    # ASSUMPTION: simple weighted sum based on observed ASM structure
    result = 0
    for ch in s:
        v = ord(ch)
        if v < 9:  # ASSUMPTION: based on 'cmp al,9' branch in ASM
            v += 0x30
        else:
            v += 0x37
        result = ((result * v) & 0xFFFFFFFF)
        result = (result + v) & 0xFFFFFFFF
    return result

def _to_hex_str(val):
    return '%08X' % (val & 0xFFFFFFFF)

def keygen(name, group=''):
    """
    Generate serial for given name and optional group.
    Serial format from ASM: hex string of computed checksum.
    ASSUMPTION: serial = hex(checksum(name) + checksum(group) + adjustments)
    """
    if len(name) < 4:
        raise ValueError('Name must be at least 4 characters')
    
    cs_name = _checksum(name)
    cs_group = _checksum(group) if group else 0
    
    total = (cs_name + cs_group) & 0xFFFFFFFF
    
    # ASSUMPTION: group_len adjustment (47h added per ASM)
    group_adj = (len(group) + 0x47) & 0xFF
    
    # ASSUMPTION: serial_1 is total, special_byte is group_adj, serial_2 derived
    # From readme: serial_2 XOR seed = function(serial_1) XOR seed
    # Seed appears to be derived from the checksum
    
    # ASSUMPTION: final serial is formatted as two 4-char hex groups separated by '-'
    part1 = (total >> 16) & 0xFFFF
    part2 = total & 0xFFFF
    
    # ASSUMPTION: special byte inserted in middle
    serial = '%04X-%02X-%04X' % (part1, group_adj, part2)
    return serial

def verify(name, serial):
    """
    Verify name/serial pair.
    ASSUMPTION: regenerate serial and compare.
    """
    if len(name) < 4:
        return False
    try:
        expected = keygen(name)
        return serial.upper() == expected.upper()
    except Exception:
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
