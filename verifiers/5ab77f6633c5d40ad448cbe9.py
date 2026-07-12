import math

def _fix(x):
    """Equivalent to VB Fix() - truncates toward zero."""
    return int(math.trunc(x))

def verify(name: str, serial) -> bool:
    """Verify name/serial pair."""
    computed = keygen(name)
    try:
        return int(serial) == computed
    except (ValueError, TypeError):
        return False

def keygen(name: str) -> int:
    """
    Compute valid serial for a given name.
    Algorithm reverse-engineered from the VB pseudocode in the writeup:

    som3 = 0
    For each character in name:
        car  = ASCII value of character
        st0  = log(car)          # natural log
        coseno = cos(car)        # cosine of ascii value (radians)
        som1 = coseno + st0
        som2 = som3 + som1
        eax  = Fix(som2)         # truncate toward zero
        eax2 = eax XOR 0x2710   # 0x2710 = 10000 decimal
        seno = sin(som1)         # sine of som1
        tang = tan(eax)          # tangent of eax
        mul1 = tang * seno
        mul2 = mul1 * eax2
        som3 = mul2 + eax
        som3 = Fix(som3)
    return som3
    """
    som3 = 0

    for ch in name:
        car = ord(ch)

        # FPU: compute ln(car) then cos(car), add them
        st0 = math.log(car)        # natural log of ASCII value
        coseno = math.cos(car)     # cos of ASCII value in radians
        som1 = coseno + st0

        # Accumulate with previous partial result
        som2 = som3 + som1

        # CALL 0040941C converts float -> int (truncate toward zero)
        eax = _fix(som2)

        # XOR with 0x2710 (10000 decimal)
        eax2 = eax ^ 0x2710

        # sin of som1, tan of eax
        seno = math.sin(som1)
        tang = math.tan(eax)

        mul1 = tang * seno
        mul2 = mul1 * eax2

        # Second CALL 0040941C: truncate toward zero
        som3 = _fix(mul2 + eax)

    return som3



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
