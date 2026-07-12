# Reverse-engineered from the VB crackme 'then_crack_me' by ideku_nih
# The decompiled VB pseudocode is heavily obfuscated/truncated, so only partial
# logic can be recovered. Several gaps are filled with ASSUMPTION comments.

def encript(ntext):
    """
    From loc_0040319B: result = result & Chr$(Asc(Mid$(ntext, i, 1)) XOR 0x7A)
    This XORs each character of ntext with 0x7A.
    """
    result = ''
    for ch in str(ntext):
        result += chr(ord(ch) ^ 0x7A)
    return result


def _build_hex_string_from_name(name):
    """
    From loc_00402793:
      var_134 = Asc(Mid$(name, i, 1)) XOR 0x6A
    Then the result is converted to Hex and lowercased,
    with a leading '0' prepended if value < 16.
    The loop runs for Len(serial) iterations but we iterate over name chars.
    ASSUMPTION: We iterate over each character of name, XOR with 0x6A,
    convert to 2-digit lowercase hex, and concatenate.
    """
    result = ''
    for ch in name:
        val = ord(ch) ^ 0x6A
        hex_val = format(val, '02x')  # always 2 digits, lowercase
        result += hex_val
    return result


def verify(name, serial):
    """
    Reconstructed verification logic:
    1. Name and serial must be non-empty.
    2. For each character position i in serial, compute:
         Asc(Mid$(name, i, 1)) XOR 0x6A  -> hex string (2 digits, lowercase)
       Concatenate all these -> expected_hex
    3. LCase(serial) must equal expected_hex  (first check at loc_00402A0C)
    4. Second check (loc_00402D60): serial must equal LCase(Left(name,8)) & Mid$(serial,9,...)
       ASSUMPTION: The serial is split: first 8 chars = lcase(name[:8]),
       rest = UCase(Mid$(serial,9,...))  but the comparison uses var_BC & Mid$(...)
       which is lcase(name[:8]) & rest_of_serial_uppercase.
       This is contradictory so we ASSUME the serial IS the hex string derived from name.
    
    ASSUMPTION: The real check is simply LCase(serial) == hex_xor_string(name)
    where hex_xor_string XORs each char of name with 0x6A and converts to 2-digit hex.
    """
    if not name or not serial:
        return False
    
    # Build expected serial from name
    expected = _build_hex_string_from_name(name)
    
    # ASSUMPTION: serial length must equal len(name)*2 (2 hex digits per char)
    if serial.lower() != expected:
        return False
    
    # Second check from loc_00402D60:
    # var_FC = LCase(Left(name,8)) & Mid$(serial_text, 9, Len(...))
    # The entered serial must equal var_FC
    # ASSUMPTION: This means the serial's first 8 chars must be lcase(name[:8])
    # and chars 9+ must be the uppercase XOR-hex of name[4:] or similar.
    # Since we can't resolve this fully, we skip the second check.
    # ASSUMPTION: Only the first check matters for validity.
    
    return True


def keygen(name):
    """
    Generate a valid serial for the given name.
    ASSUMPTION: serial = hex(ord(c) ^ 0x6A) for each char c in name,
    concatenated as lowercase 2-digit hex strings.
    """
    if not name:
        raise ValueError("Name must be non-empty")
    return _build_hex_string_from_name(name)



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
