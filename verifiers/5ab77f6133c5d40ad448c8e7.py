import math

def generate_std(user: str) -> str:
    """
    Reconstructed from the Delphi keygen source (generate_std function).
    Concatenate ASCII ordinals of each character, convert to float,
    then apply a series of arithmetic operations, finally format.
    """
    # Build number string by concatenating ord of each char
    n = ''
    for ch in user:
        n += str(ord(ch))
    nf = float(n)
    nf = math.sqrt(nf * 2)
    nf = nf * 89.5
    nf = nf / 5
    nf = nf + 190.48
    nf = nf - 70.93
    nf = nf + 120.1
    nf = nf * 2.2
    nf = nf - (nf / 5)
    nf = nf + 1000
    nf = nf - (nf / 6.7777777788)
    nf = nf + math.pow(9.43210001, (len(user) * 9.35673636))
    # ASSUMPTION: The result is converted to string (integer part or formatted float).
    # The Delphi source was truncated before the StringReplace/format call.
    # We assume the decimal separator comma is removed (as described in the writeup)
    # and the final serial is 'STD-<number>-HMX'
    # Format as integer (truncate float) to match likely behavior
    serial_num = str(int(nf))
    # ASSUMPTION: any ',' (locale decimal separator) would be removed; in Python there's none
    return 'STD-' + serial_num + '-HMX'


def generate_pro(user: str) -> str:
    """
    Reconstructed from assembly comments: PRO procedure is similar to STD
    but uses a different serial generation call (unpacked.000190C0 vs unpacked.00018E84).
    The exact PRO algorithm is not shown in the truncated source.
    ASSUMPTION: PRO uses same arithmetic but with a different variant/parameter.
    We cannot fully reconstruct this without the generate_pro Delphi source.
    """
    # ASSUMPTION: generate_pro likely applies similar math to generate_std
    # but with different constants. We replicate generate_std as a placeholder.
    n = ''
    for ch in user:
        n += str(ord(ch))
    nf = float(n)
    nf = math.sqrt(nf * 2)
    nf = nf * 89.5
    nf = nf / 5
    nf = nf + 190.48
    nf = nf - 70.93
    nf = nf + 120.1
    nf = nf * 2.2
    nf = nf - (nf / 5)
    nf = nf + 1000
    nf = nf - (nf / 6.7777777788)
    nf = nf + math.pow(9.43210001, (len(user) * 9.35673636))
    # ASSUMPTION: PRO uses a different inner calculation; this is a copy of STD
    serial_num = str(int(nf))
    return 'PRO-' + serial_num + '-HMX'


def verify(name: str, serial: str) -> bool:
    """
    Verify a serial for a given name.
    Rules from writeup:
    1. Name must be at least 6 chars.
    2. Serial must start with 'STD-' or 'PRO-'.
    3. Serial must match generated serial for name.
    """
    if len(name) < 6:
        return False
    if serial.startswith('STD-'):
        expected = generate_std(name)
        return serial == expected
    elif serial.startswith('PRO-'):
        expected = generate_pro(name)
        return serial == expected
    return False


def keygen(name: str) -> str:
    """
    Generate a valid STD serial for the given name.
    Name must be at least 6 characters.
    """
    if len(name) < 6:
        raise ValueError('Name must be at least 6 characters long')
    return generate_std(name)



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
