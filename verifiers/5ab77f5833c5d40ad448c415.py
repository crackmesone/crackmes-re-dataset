import math

def gen_serial(name: str) -> str:
    """
    Pascal: for each char in name, result += chr(Round((ord(c) xor len) / 1.5))
    then lowercase.
    Pascal's Round() uses banker's rounding (round half to even).
    """
    length = len(name)
    result = ''
    for c in name:
        val = (ord(c) ^ length) / 1.5
        # Pascal Round() = banker's rounding (round half to even)
        rounded = int(round(val))  # Python 3 round() also does banker's rounding
        result += chr(rounded)
    return result.lower()


def strip_leading_zero(s: str) -> str:
    """Remove leading zeros but keep at least one char if all zeros."""
    # Pascal: while str[1]='0' and Length(str)>0 do Delete(str,1,1)
    # Note: Pascal checks str[1] first, so if string becomes empty it stops
    while len(s) > 0 and s[0] == '0':
        s = s[1:]
    return s


def _bitwise_not_32bit(x: int) -> int:
    """Pascal 'not' on integer (32-bit signed twos complement NOT)."""
    # In Pascal, 'not' on an integer is bitwise NOT
    # For a 32-bit signed integer: not x = -(x+1)
    return -(x + 1)


def gen_security_code(serial: str) -> str:
    """
    Pascal GenSecurityCode implementation.
    """
    serial_upper = serial.upper()
    length = len(serial_upper)
    temp = ''

    for i in range(length):
        ch = round(ord(serial_upper[i]) / 2)  # Pascal Round()
        if ch > 0x39:  # 57
            # ch := (not (ch - $39)) + ch
            ch = _bitwise_not_32bit(ch - 0x39) + ch
        else:
            # ch := ch - (not (ch + $30))
            ch = ch - _bitwise_not_32bit(ch + 0x30)
        ch = (ch - 0x0A) * 2
        temp += str(ch)

    length2 = len(temp)
    result = ''

    for i in range(length2):
        # MidStr(temp, i, 9) in Pascal is 1-indexed, so MidStr(temp, i+1, 9) in 0-indexed
        # But the loop is 'for i := 1 to len' in Pascal
        # So i goes 1..len, MidStr(temp, i, 9) = temp[i-1:i-1+9]
        substr = temp[i:i+9]
        if not substr:
            break
        ch2 = int(substr) + 97
        hex_str = format(ch2, '08X')
        result += strip_leading_zero(hex_str)
        if i < length2 - 1:
            result += '-'

    return result


def keygen(name: str):
    """Generate serial and security code for a given name."""
    serial = gen_serial(name)
    security_code = gen_security_code(serial)
    return serial, security_code


def verify(name: str, serial: str, security_code: str = None) -> bool:
    """
    Verify name against serial (and optionally security_code).
    The crackme checks:
      1. serial == gen_serial(name)
      2. security_code == gen_security_code(serial)  (if provided)
    """
    expected_serial = gen_serial(name)
    if serial.lower() != expected_serial.lower():
        return False
    if security_code is not None:
        expected_sc = gen_security_code(serial)
        if security_code != expected_sc:
            return False
    return True



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
