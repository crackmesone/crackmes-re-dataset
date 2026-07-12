import math
import struct


def _ecvt(value, ndigits):
    """
    Emulate C's ecvt(): convert a double to a string of ndigits significant
    decimal digits.  Returns the digit string (length == ndigits).
    The sign and decimal-point position are ignored here because the keygen
    only uses the digit characters themselves.
    """
    if value == 0.0:
        return '0' * ndigits, 0, 0
    sign = 0
    if value < 0:
        sign = 1
        value = -value
    # number of digits before decimal point
    import math as _math
    exp10 = _math.floor(_math.log10(value)) + 1  # decimal exponent
    # scale so we get ndigits significant digits as an integer
    scaled = value * (10 ** (ndigits - exp10))
    rounded = int(round(scaled))
    s = str(rounded)
    # If rounding caused an extra digit, trim or re-adjust
    if len(s) > ndigits:
        exp10 += len(s) - ndigits
        s = s[:ndigits]
    elif len(s) < ndigits:
        s = s.ljust(ndigits, '0')
    return s, exp10, sign


def _compute_serial(name: str):
    """
    Reproduce the algorithm from KeyGen.cpp / disassembly.

    Steps:
      1. Build cNewName where cNewName[i] = cName[i-4] for i in [4, sLen+4).
         The character used for exponentiation is cNewName[sLen],
         which equals cName[sLen - 4].
      2. y = exp(x)  where x = ord(that character)
      3. cFirstSerial = ecvt(y, 5)   -> 5-digit string
      4. nSum  = sum of ASCII values of those 5 chars
         nSum  = nSum * 180           -> second serial (decimal string)
      5. nSum  = nSum * 3
         nSum  = nSum << 2
         nSum  = nSum + 268           -> third serial (decimal string)
      6. Final serial = cFirstSerial + cSecondSerial + cThirdSerial
    """
    sLen = len(name)

    # cNewName layout: indices 0..3 are unused/zero, indices 4..sLen+3 = name
    # The char taken is cNewName[sLen] = name[sLen - 4]
    # ASSUMPTION: the original code uses cNewName[sLen] which maps to name[sLen-4]
    char_index = sLen - 4
    x = float(ord(name[char_index]))

    y = math.exp(x)

    # ecvt with nPrecision = 5
    digits, decimal_pos, sign = _ecvt(y, 5)
    cFirstSerial = digits  # 5-character digit string

    # Sum ASCII values of the 5 characters
    nSum = sum(ord(c) for c in cFirstSerial)

    # Second serial
    nSum = nSum * 180  # 0xB4 == 180
    cSecondSerial = str(nSum)

    # Third serial
    nSum = nSum * 3
    nSum = nSum << 2
    nSum = nSum + 268  # 0x10C == 268
    cThirdSerial = str(nSum)

    return cFirstSerial + cSecondSerial + cThirdSerial


def keygen(name: str) -> str:
    if len(name) < 5:
        raise ValueError('Name must be more than 5 characters')
    if len(name) > 15:
        raise ValueError('Name must be at most 15 characters')
    return _compute_serial(name)


def verify(name: str, serial: str) -> bool:
    if len(name) < 5 or len(name) > 15:
        return False
    try:
        expected = _compute_serial(name)
    except (IndexError, ValueError):
        return False
    return serial == expected



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
