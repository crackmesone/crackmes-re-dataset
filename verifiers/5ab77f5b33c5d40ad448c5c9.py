# Keygen for !KeygenMe 1 by HackeRMan
# Reverse-engineered from Bswap's keygen source (ASM)
#
# Algorithm:
# 1. name_val = EditName[len(name)]  (triangular numbers: 0,1,3,6,10,15,21,28,36,45,55,66,78)
# 2. city_val = EditCity[len(city)]  (0,1,1,4,4,9,9,16,16,25,25,36,36)
# 3. result1 = name_val  (stored in esi)
# 4. edi = 0 - city_val  (negate city_val)
# 5. Sum every other byte of city string (indices 0,2,4,...) into edx
#    (the loop: add al, city[ecx]; add edx, eax; ecx += 2; while len(city) > ecx)
# 6. edi += edx
# 7. temp = name_val * edi  (mul, result in eax)
# 8. ecx = 0 - temp  (negate)
# 9. edi = ecx
# 10. product = len(name) * len(city)
# 11. edi += product
# 12. serial = hex(edi & 0xFFFFFFFF).upper()

EditName = [0, 1, 3, 6, 10, 15, 21, 28, 36, 45, 55, 66, 78]
EditCity = [0, 1, 1, 4, 4, 9, 9, 16, 16, 25, 25, 36, 36]

def _compute(name, city):
    name_len = len(name)
    city_len = len(city)

    # Clamp to table size (max index supported)
    if name_len > 12 or city_len > 12:
        return None

    # Step 1: get name triangular value
    name_val = EditName[name_len]

    # Step 2: get city table value
    city_table_val = EditCity[city_len]

    # Step 3: esi = name_val
    result1 = name_val

    # Step 4: edi = 0 - city_table_val  (32-bit negation)
    edi = (0 - city_table_val) & 0xFFFFFFFF

    # Step 5: sum every other byte of city (indices 0,2,4,...)
    # The loop uses ecx as offset starting at 0, increments by 2 each time
    # Condition: continue while city_len > ecx  (so ecx=0,2,4,... while ecx < city_len)
    edx = 0
    eax = 0
    ecx = 0
    city_bytes = [ord(c) for c in city]
    while True:
        al = city_bytes[ecx] if ecx < city_len else 0
        eax = al
        edx = (edx + eax) & 0xFFFFFFFF
        ecx += 2
        eax = 0  # xor al,al
        if not (city_len > ecx):
            break

    # Step 6: edi += edx
    edi = (edi + edx) & 0xFFFFFFFF

    # Step 7: eax = name_val * edi  (32-bit mul)
    eax = (result1 * edi) & 0xFFFFFFFF

    # Step 8: ecx = 0 - eax
    ecx = (0 - eax) & 0xFFFFFFFF

    # Step 9: edi = ecx
    edi = ecx

    # Step 10: eax = len(name) * len(city)
    product = (name_len * city_len) & 0xFFFFFFFF

    # Step 11: edi += product
    edi = (edi + product) & 0xFFFFFFFF

    return edi


def verify(name, serial):
    """Verify that the serial matches the expected value for the given name+city.
    Note: the crackme takes Name + City; here 'serial' is the expected hex string.
    The function signature matches the schema but the algorithm needs City too.
    # ASSUMPTION: 'serial' parameter is used as the city field for verification.
    Call as verify(name, city) to check, then compare with keygen(name, city).
    """
    # ASSUMPTION: We treat the second argument as city since the crackme uses Name+City->Serial
    # This is a design mismatch with the verify(name, serial) interface.
    # To actually verify: computed_serial == provided_serial
    # We cannot verify without city; returning False by default.
    return False


def verify_full(name, city, serial):
    """Full verification with name, city and expected serial string."""
    computed = _compute(name, city)
    if computed is None:
        return False
    # Serial is displayed as hex (uppercase, no leading zeros, as wsprintf %lX)
    expected = '%X' % computed
    return serial.upper().lstrip('0') == expected.lstrip('0') or serial.upper() == expected


def keygen(name, city):
    """Generate the serial for the given name and city."""
    result = _compute(name, city)
    if result is None:
        raise ValueError('Name or City too long (max 12 chars)')
    # wsprintf with %lX formats as uppercase hex
    return '%X' % result



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
