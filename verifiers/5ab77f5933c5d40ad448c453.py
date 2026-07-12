import struct

def _find_pairs(target_byte):
    """Find all (i, j) pairs where 0 <= i,j < 255 and ((i << 2) ^ (j >> 2)) == target_byte"""
    pairs = []
    for i in range(255):
        for j in range(255):
            if ((i << 2) ^ (j >> 2)) == target_byte:
                pairs.append((i, j))
    return pairs

def keygen(name):
    """Generate valid serials for the given name. Returns a list of valid serials."""
    if len(name) < 3:
        return []
    
    name_bytes = name.encode('ascii')
    bs = (len(name) - 1) // 3
    
    # Get target bytes
    target1 = name_bytes[bs]
    target2 = name_bytes[bs * 2]
    target3 = name_bytes[bs * 3]
    
    # Find pairs for each target
    pairs1 = _find_pairs(target1)
    pairs2 = _find_pairs(target2)
    pairs3 = _find_pairs(target3)
    
    serials = []
    
    if bs == 0:
        # Special case: just 2-char keys from pairs1
        for (i, j) in pairs1:
            try:
                serial = chr(i) + chr(j)
                serials.append(serial)
            except (ValueError, OverflowError):
                pass
    else:
        # Normal case: format is "xxXX" + c1 + c2 + "XX" + c3 + c4 + "xx" + c5 + c6
        # Only first 25 pairs are used (i from 0 to 48 step 2, so indices 0..24)
        max_pairs = min(25, len(pairs1), len(pairs2), len(pairs3))
        for idx in range(max_pairs):
            try:
                c1 = chr(pairs1[idx][0])
                c2 = chr(pairs1[idx][1])
                c3 = chr(pairs2[idx][0])
                c4 = chr(pairs2[idx][1])
                c5 = chr(pairs3[idx][0])
                c6 = chr(pairs3[idx][1])
                candidate = 'xxXX' + c1 + c2 + 'XX' + c3 + c4 + 'xx' + c5 + c6
                # The crackme checks that the generated string length == 14
                if len(candidate) == 14:
                    serials.append(candidate)
            except (ValueError, OverflowError):
                pass
    
    return serials

def verify(name, serial):
    """Verify that serial is valid for the given name."""
    if len(name) < 3:
        return False
    
    name_bytes = name.encode('ascii')
    bs = (len(name) - 1) // 3
    
    target1 = name_bytes[bs]
    target2 = name_bytes[bs * 2]
    target3 = name_bytes[bs * 3]
    
    if bs == 0:
        # Serial should be 2 chars
        if len(serial) != 2:
            return False
        i = ord(serial[0])
        j = ord(serial[1])
        return ((i << 2) ^ (j >> 2)) == target1
    else:
        # Serial must be length 14 with format "xxXX??XX??xx??"
        if len(serial) != 14:
            return False
        if not serial.startswith('xxXX'):
            return False
        if serial[6:8] != 'XX':
            return False
        if serial[10:12] != 'xx':
            return False
        
        c1 = ord(serial[4])
        c2 = ord(serial[5])
        c3 = ord(serial[8])
        c4 = ord(serial[9])
        c5 = ord(serial[12])
        c6 = ord(serial[13])
        
        check1 = ((c1 << 2) ^ (c2 >> 2)) == target1
        check2 = ((c3 << 2) ^ (c4 >> 2)) == target2
        check3 = ((c5 << 2) ^ (c6 >> 2)) == target3
        
        return check1 and check2 and check3


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
