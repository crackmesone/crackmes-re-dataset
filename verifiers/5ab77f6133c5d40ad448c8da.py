def hmx_algo(ch):
    """
    Apply the HMX-algo to a single character.
    Steps:
      1. Get ASCII value (hex)
      2. Convert to binary, reverse the binary string (without '0b' prefix),
         then convert back to decimal  -> part1
      3. Reverse the hex digits of the ASCII value (treat as 2-digit hex),
         convert that reversed hex to decimal -> part2
      4. Direct hex-to-dec: just the decimal value of ASCII -> part3
    Return the concatenation of part1, part2, part3 as a string.
    """
    ascii_val = ord(ch)

    # Part 1: binary representation reversed -> decimal
    bin_str = bin(ascii_val)[2:]  # e.g. 'a'=0x61=97 -> '1100001'
    bin_reversed = bin_str[::-1]   # '1000011'
    part1 = int(bin_reversed, 2)   # 67

    # Part 2: hex representation reversed -> decimal
    # ASCII value as 2-digit hex (e.g. 0x61 -> '61'), reverse digits -> '16', convert hex to dec
    hex_str = format(ascii_val, '02x')  # e.g. '61'
    hex_reversed = hex_str[::-1]         # '16'
    part2 = int(hex_reversed, 16)        # 0x16 = 22

    # Part 3: ASCII value as decimal directly
    part3 = ascii_val  # 97

    return str(part1) + str(part2) + str(part3)


def keygen(name):
    """
    Generate the serial for the given name.

    Algorithm:
      1. Take the first 2 chars of the name, uppercase them, reverse their order,
         append '-'  =>  prefix
         e.g. 'anorganix' -> 'an' -> 'AN' -> 'NA' -> 'NA-'
      2. Apply the HMX-algo to the last character of the name.
         Concatenate prefix + hmx_algo(last_char).
    """
    if len(name) == 0:
        raise ValueError("Name must not be empty")

    # Step 1: prefix from first 2 chars (or 1 if name is 1 char)
    if len(name) >= 2:
        first_two = name[:2].upper()  # e.g. 'AN'
        prefix = first_two[::-1] + '-'  # reversed -> 'NA-'
    else:
        # 1-char name: only 1 char uppercased (tutorial notes this can cause a crash)
        prefix = name[0].upper() + '-'

    # Step 2: HMX-algo on last char
    last_char = name[-1]
    code_part = hmx_algo(last_char)

    return prefix + code_part


def verify(name, serial):
    """
    Check whether the serial matches the expected serial for the given name.
    """
    try:
        expected = keygen(name)
    except ValueError:
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
