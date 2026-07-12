import math

# The crackme generates a random number 0-4 (via Int(Rnd*5)) which selects one of 5 serial types.
# Each serial is made of 6 parts separated by dashes.
# The serial fields depend on len(username) and len(company).
# verify() checks if the serial matches ANY of the 5 possible valid serials for the given name/company.
# NOTE: The original crackme only stores company in a separate field; here we pass it as a parameter.
# ASSUMPTION: serial parts are joined with '-' as shown in the keygen source.

def _fmt_float(v):
    """Mimic VB/Python2 float-to-string for integers stored as float."""
    # In Python 2, str(5.0) == '5.0'; in Python 3 same behavior
    if isinstance(v, float) and v == int(v):
        return str(v)  # e.g. '5.0'
    return str(v)

def gen1(username, company):
    u = len(username)
    c = len(company)
    num = 10
    szStr = []
    szStr.append(str(int(c * 4)))
    szStr.append(_fmt_float((u * num) / 2) + 'H')
    szStr.append(_fmt_float(u * pow(num, 6)) + 'C')
    # s4: un.TextLength + str from s3 (which is the float string without 'C')
    s3_val = u * pow(num, 6)
    szStr.append(_fmt_float(u + s3_val) + 'XZ')
    # s5: u + num as int, then str(int)
    s5_int = u + num
    szStr.append('Z3F' + str(int(s5_int)) + 'GT')
    # s6: u + float(str from s5 which is str(int)) -> u + s5_int
    s6_val = u + s5_int
    szStr.append(_fmt_float(float(s6_val)) + 'QAADA')
    return szStr

def gen2(username, company):
    u = len(username)
    c = len(company)
    num = 10
    szStr = []
    szStr.append(str(int(c * 5)))
    szStr.append(_fmt_float((u * num) / 5) + 'Z')
    szStr.append(_fmt_float(u * pow(num, 5)) + '9')
    s3_val = u * pow(num, 5)
    szStr.append(_fmt_float(u + s3_val) + 'DRM')
    s5_int = u + num
    szStr.append('ID66R' + str(int(s5_int)) + 'GT')
    s6_val = u + s5_int
    szStr.append(_fmt_float(float(s6_val)) + 'FFQE')
    return szStr

def gen3(username, company):
    u = len(username)
    c = len(company)
    num = 10
    szStr = []
    szStr.append(str(int(c * 2)))
    szStr.append(_fmt_float((u * num) / 2) + 'GBM')
    szStr.append(_fmt_float(u * pow(num, 2)) + 'RLZ')
    s3_val = u * pow(num, 2)
    szStr.append(_fmt_float(u + s3_val) + 'FAShL')
    s5_int = u + num
    szStr.append('0M' + str(int(s5_int)) + 'G')
    s6_val = u + s5_int
    szStr.append(_fmt_float(float(s6_val)) + 'FzZ')
    return szStr

def gen4(username, company):
    u = len(username)
    c = len(company)
    num = 10
    szStr = []
    szStr.append(str(int(c * 1)))
    szStr.append(_fmt_float((u * num) / 2) + 'O')
    szStr.append(_fmt_float(u * pow(num, 3)) + 'CRZ')
    s3_val = u * pow(num, 3)
    szStr.append(_fmt_float(u + s3_val) + 'RUS')
    s5_int = u + num
    szStr.append('BE' + str(int(s5_int)) + 'NED')
    s6_val = u + s5_int
    szStr.append(_fmt_float(float(s6_val)) + 'EnG')
    return szStr

def gen5(username, company):
    u = len(username)
    c = len(company)
    num = 10
    szStr = []
    szStr.append(str(int(c * 5)))
    szStr.append(_fmt_float((u * num) / 10) + 'NI')
    szStr.append(_fmt_float(u * pow(num, 15)) + 'CE')
    s3_val = u * pow(num, 15)
    szStr.append(_fmt_float(u + s3_val) + 'CW')
    s5_int = u + num
    szStr.append('OrK' + str(int(s5_int)) + 'GAeT')
    s6_val = u + s5_int
    szStr.append(_fmt_float(float(s6_val)) + 'QfaE')
    return szStr

def _parts_to_serial(parts):
    return '-'.join(parts)

def keygen(name, company=''):
    """Returns all 5 valid serials for the given username and company."""
    serials = []
    for gen in [gen1, gen2, gen3, gen4, gen5]:
        serials.append(_parts_to_serial(gen(name, company)))
    return serials

def verify(name, serial, company=''):
    """Returns True if serial is valid for the given name and company."""
    valid_serials = keygen(name, company)
    return serial in valid_serials


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
