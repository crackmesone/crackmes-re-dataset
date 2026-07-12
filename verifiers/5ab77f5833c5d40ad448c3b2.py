def _name_hash(name):
    """Compute the hash of a 6-character name.
    Process: start with eax=0, for each char: eax = (eax ^ 0xC) + ord(char)
    Then final XOR with 0xC.
    """
    result = 0
    for ch in name:
        result = (result ^ 0xC) + ord(ch)
    result ^= 0xC
    return result

def _sn_hash(sn):
    """Compute the hash of a 6-character serial.
    Process: start with edx=0, for each char: edx = (edx ^ 0x1A) + ord(char)
    """
    result = 0
    for ch in sn:
        result = (result ^ 0x1A) + ord(ch)
    return result

def verify(name, serial):
    """The crackme checks that len(name)==6 and len(serial)==6,
    then computes name_hash and sn_hash, and performs idiv(name_hash - sn_hash).
    A DivideByZero exception is triggered (and presumably caught/used as success)
    when name_hash == sn_hash, i.e. (name_hash - sn_hash) == 0.
    """
    if len(name) != 6 or len(serial) != 6:
        return False
    nh = _name_hash(name)
    sh = _sn_hash(serial)
    # Success condition: the divisor (nh - sh) == 0, triggering DivideByZero exception
    return nh == sh

def keygen(name):
    """Generate a valid serial for the given 6-character name.
    Reconstructed from the keygen.cpp provided in the writeup.
    The algorithm decomposes the name_hash into 6 characters by repeatedly
    subtracting either 'z' (if s > 0x100) or 'A' (otherwise) and XORing with 0x1A.
    """
    if len(name) != 6:
        raise ValueError('Name must be exactly 6 characters')

    nh = _name_hash(name)

    sn = [''] * 6
    s = nh
    for i in range(6):
        if s > 0x100:
            s -= ord('z')
            sn[5 - i] = 'z'
            s ^= 0x1A
        else:
            if i == 5:
                # Last iteration: store the raw byte
                sn[5 - i] = chr(s & 0xFF)
            else:
                s -= ord('A')
                sn[5 - i] = 'A'
                s ^= 0x1A

    result = ''.join(sn)
    return result


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
