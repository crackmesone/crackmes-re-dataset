def _hex_vb(n):
    """Replicate VB's Hex() function: returns uppercase hex string without '0x' prefix."""
    return format(n & 0xFF, 'X')


def keygen(username, computername):
    """
    Generate serial for given username and computername.
    Both are strings (e.g. Windows username and computer name).
    """
    szUser = username.strip()
    szComputer = computername.strip()

    # Step 1: build initial hash1
    hash1 = szUser + "@" + szComputer
    var_96 = len(hash1)  # length of "user@computer"

    if len(szUser) >= len(szComputer):
        # iterate over computer name length
        for i in range(len(szComputer)):
            c_user = szUser[i]
            c_comp = szComputer[i]
            xor_val = ord(c_user) ^ ord(c_comp)
            hash1 = hash1 + c_user + _hex_vb(xor_val)
    else:
        # iterate over user name length
        for j in range(len(szUser)):
            c_user = szUser[j]
            c_comp = szComputer[j]
            xor_val = ord(c_user) ^ ord(c_comp)
            hash1 = hash1 + c_user + _hex_vb(xor_val)

    # Step 2: strip the initial prefix ("user@computer" part)
    # VB: Mid$(hash1, var_96+1, Len(hash1)-var_96)
    # VB Mid$ is 1-based; Mid$(s, start, length)
    hash1 = hash1[var_96:var_96 + (len(hash1) - var_96)]
    # which is effectively hash1[var_96:]

    # Step 3: extend hash1 if szUser is longer than the current hash1 tail
    arg_C = szUser
    var_A4 = len(hash1) - len(arg_C)

    if len(arg_C) > var_A4:
        for k in range(1, abs(len(arg_C) - var_A4) + 1):
            # VB: k is 1-based, Mid$(hash1, 1, k) gives first k chars
            # Asc of that gives ord of first char of that substring
            # Actually Asc(Mid$(hash1, 1, k)) = ord of first char of hash1 always
            # because Asc() returns ASCII of first character
            c = hash1[0]  # Asc(Mid$(hash1, 1, k)) = ord of first char
            xor_val = ord(c) ^ var_A4
            hash1 = hash1 + _hex_vb(xor_val)

    # Step 4: build temp1
    # temp1 = hash1 & "-" & arg_C
    # temp1 = Mid$(temp1, 1, Len(hash1))  -- truncate to len(hash1)
    temp1_full = hash1 + "-" + arg_C
    temp1 = temp1_full[:len(hash1)]

    # Step 5: append XOR of each char in temp1 with corresponding char in arg_C
    for m in range(len(arg_C)):
        c_temp = temp1[m] if m < len(temp1) else '\x00'
        c_arg = arg_C[m]
        xor_val = ord(c_temp) ^ ord(c_arg)
        temp1 = temp1 + _hex_vb(xor_val)

    # Step 6: split into groups of 4 separated by '-'
    lResult = ""
    for j in range(0, len(temp1), 4):
        lResult = lResult + temp1[j:j+4] + "-"

    # Remove trailing '-'
    if lResult.endswith("-"):
        lResult = lResult[:-1]

    return lResult


def verify(username, serial):
    """
    Verify a serial for the given username.
    NOTE: The crackme uses BOTH username and computername.
    This verify function requires the computername embedded in the serial
    cannot be recovered from serial alone - so we just regenerate and compare.
    Since the serial depends on computername, we need it as part of 'name'.
    Pass name as 'username|computername' or use verify2.
    """
    # ASSUMPTION: 'username' here is passed as 'user|computer' to allow verify
    if '|' in username:
        parts = username.split('|', 1)
        user = parts[0]
        computer = parts[1]
    else:
        # ASSUMPTION: if no separator, treat as username only with empty computer
        user = username
        computer = ""

    # Length checks from the crackme
    if len(user) <= 2:
        return False
    if len(user) > 12:
        return False

    expected = keygen(user, computer)
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
