import hashlib
import os


def _hex_of_len_username(username: str) -> str:
    """VB: Hex(Asc(CStr(Len(username))))
    Len gives length as integer, CStr converts to string e.g. '5',
    Asc gives ASCII code of first character of that string,
    Hex converts that ASCII code to hex string (uppercase in VB).
    """
    length = len(username)
    length_str = str(length)  # e.g. 5 -> '5'
    asc_val = ord(length_str[0])  # ASCII of first char of the string representation
    hex_str = hex(asc_val)[2:].upper()  # VB Hex() returns uppercase without '0x'
    return hex_str


def generate_serial(username: str) -> str:
    """Generate the serial (TextBox4) based on username.
    Formula: CStr(CDbl(Hex(Asc(CStr(Len(username)))) * 4 - (-1818180))) & '-' &
             CStr(CDbl(Hex(Asc(CStr(Len(username)))) * 4))
    Note: Hex(Asc(CStr(Len(username)))) is treated as a hex string then
    converted to double via CDbl. In VB, CDbl('35') = 35.0 (decimal interpretation
    of the hex string as if it were a decimal number).
    """
    hex_str = _hex_of_len_username(username)
    # VB CDbl(Hex(...)) treats the hex string as a decimal number
    # e.g. Hex(Asc('5')) = Hex(53) = '35', CDbl('35') = 35.0
    val = float(hex_str)  # interpret hex string digits as decimal number
    part2 = val * 4
    part1 = part2 - (-1818180)  # i.e. part2 + 1818180
    # CStr(CDbl(...)) in VB formats floats: if integer value, no decimal point
    def vb_cstr_cdbl(v: float) -> str:
        if v == int(v):
            return str(int(v))
        return str(v)
    return vb_cstr_cdbl(part1) + '-' + vb_cstr_cdbl(part2)


def _md5_unicode(text: str) -> str:
    """MD5 of text encoded as UTF-16-LE (UnicodeEncoding in .NET),
    returned as uppercase hex string with dashes like BitConverter.ToString.
    """
    data = text.encode('utf-16-le')
    digest = hashlib.md5(data).digest()
    return '-'.join(f'{b:02X}' for b in digest)


def _house_license(license_number: str) -> str:
    """VB: Hex(CDbl(CStr(Len(TextBox1))) - 100)
    Length of license number string, minus 100, converted to hex.
    """
    length = len(license_number)
    val = float(str(length)) - 100.0
    int_val = int(val)
    if int_val < 0:
        # VB Hex of negative numbers uses two's complement (32-bit)
        int_val = int_val & 0xFFFFFFFF
    return hex(int_val)[2:].upper()


def verify_serial(username: str, serial: str) -> bool:
    """Verify the serial (step 1 check - Button2)."""
    expected = generate_serial(username)
    return serial == expected


def verify_license(license_number: str, house_license: str, unlock_code: str) -> bool:
    """Verify the license fields (step 2 check - Button1).
    license_number: TextBox1
    house_license:  TextBox2 must equal Hex(Len(license_number) - 100)
    unlock_code:    TextBox3 must equal MD5(Trim(license_number)) as BitConverter string
    """
    license_trimmed = license_number.strip()
    expected_house = _house_license(license_number)
    expected_unlock = _md5_unicode(license_trimmed)
    return house_license.upper() == expected_house and unlock_code.upper() == expected_unlock


def verify(name: str, serial: str) -> bool:
    """Combined verify: checks serial against username.
    The license check requires separate inputs (license_number, house, unlock).
    This verify() implements the serial (step 1) check only.
    """
    return verify_serial(name, serial)


def keygen(name: str) -> str:
    """Generate serial from username."""
    return generate_serial(name)


def keygen_license(license_number: str):
    """Generate house license and unlock code from license number."""
    house = _house_license(license_number)
    unlock = _md5_unicode(license_number.strip())
    return house, unlock



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
