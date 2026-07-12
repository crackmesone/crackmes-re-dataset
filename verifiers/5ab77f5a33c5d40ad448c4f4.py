import base64

# Character value table from the decompiled .NET source
CHAR_VALUES = {
    'a': 0x47, 'b': 0xD4, 'c': 0x35, 'd': 0x1BC, 'e': 0xEB,
    'f': 0x6A, 'g': 0xA11, 'h': 0x62, 'i': 0x1B7, 'j': 0x906,
    'k': 0x30D, 'l': 0x37C, 'm': 0x9A9, 'n': 0xD6, 'o': 0x73,
    'p': 0x2FE, 'q': 0x273, 'r': 0x120, 's': 0x3C9, 't': 10,
    'u': 0x15, 'v': 0x336, 'w': 0x3F, 'x': 0xA4, 'y': 0xC3, 'z': 0xE2
}


def _is_letter(text: str) -> bool:
    return all(c.isalpha() for c in text)


def _compute_num2(name: str) -> int:
    """Sum the char values for each lowercase letter in the name."""
    num2 = 0
    for ch in name:
        num2 += CHAR_VALUES.get(ch.lower(), 0)
    return num2


def _build_serial_string(num2: int) -> str:
    """
    Reconstruct the intermediate string exactly as in the VB.NET source.

    str = ToString((double)((num2 * 6) - ((double)num2 / 2.0)))
        + "JtNf"
        + ToString((int)(num2 * 12))
        + "OhGO"
        + ToString((int)((num2 + 0x17) + (num2 * 2)))
        + ToString((double)(num2 + ((25.0 / (double)num2) * 2.0)))
        + "CRACK"

    NOTE: .NET's Conversions.ToString(Double) for whole numbers produces
    a plain integer string (e.g. "19679" not "19679.0").
    For non-integer doubles it produces a decimal representation.
    We replicate that behaviour below.
    """
    # Part 1: (num2 * 6) - (num2 / 2.0)  -> double
    part1 = float(num2 * 6) - (float(num2) / 2.0)
    # Part 3: num2 * 12  -> int
    part3 = int(num2 * 12)
    # Part 5: (num2 + 0x17) + (num2 * 2)  -> int
    part5 = int((num2 + 0x17) + (num2 * 2))
    # Part 6: num2 + (25.0 / num2) * 2.0  -> double
    part6 = float(num2) + (25.0 / float(num2)) * 2.0

    def vb_double_to_str(v: float) -> str:
        """
        Mimic VB/C# Conversions.ToString(Double).
        If the value is a whole number, output without decimal point.
        Otherwise output full decimal representation.
        # ASSUMPTION: .NET formats doubles without trailing zeros;
        # we use Python's repr-like formatting and strip trailing zeros.
        """
        if v == int(v):
            return str(int(v))
        else:
            # Python str(float) is close enough for typical values
            s = repr(v)
            return s

    s = (vb_double_to_str(part1)
         + "JtNf"
         + str(part3)
         + "OhGO"
         + str(part5)
         + vb_double_to_str(part6)
         + "CRACK")
    return s


def _text_string_to_byte_array(s: str) -> bytes:
    """
    Mimic TextStringToByteArray which uses System.Text.Encoding.Default.
    On Western Windows systems this is typically Windows-1252 / Latin-1.
    # ASSUMPTION: Encoding.Default is Latin-1 (covers all ASCII chars used here).
    """
    return s.encode('latin-1')


def _to_base64(data: bytes) -> str:
    return base64.b64encode(data).decode('ascii')


def keygen(name: str) -> str:
    """Generate the valid serial for the given name."""
    if not _is_letter(name):
        raise ValueError("Name must contain only letters.")
    if len(name) < 7:
        raise ValueError("Name must be at least 7 characters long.")
    num2 = _compute_num2(name)
    intermediate = _build_serial_string(num2)
    raw_bytes = _text_string_to_byte_array(intermediate)
    return _to_base64(raw_bytes)


def verify(name: str, serial: str) -> bool:
    """Return True if serial is the correct key for name."""
    if not _is_letter(name):
        return False
    if len(name) < 7:
        return False
    try:
        expected = keygen(name)
    except Exception:
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
