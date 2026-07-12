import winreg

def get_machine_guid():
    """Read MachineGuid from registry (Windows only). Falls back to a provided value."""
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Cryptography')
        value, _ = winreg.QueryValueEx(key, 'MachineGuid')
        winreg.CloseKey(key)
        return value
    except Exception:
        return None


def keygen(machine_guid: str) -> str:
    """
    Generate the verification code from a MachineGuid string.

    Algorithm (reconstructed from writeup + comments):
      Stage 1: Read MachineGuid from registry.
      Stage 2: Remove all '-' characters (dashes) from the GUID.
      Stage 3: Transform each character:
               - If letter: convert to lowercase, compute ord(c) - ord('a') + 1  (so 'a'->1, 'b'->2, ...)
               - If digit: keep as-is (as a digit character/value)
               Result is a big decimal number string.
      Stage 4: Divide that number by 5 using string long-division (big-integer div).
      Stage 5: Strip leading zeros from the quotient.
      Stage 6: Multiply the quotient by 2 using string right-to-left multiply
               (with carry propagation).
               # ASSUMPTION: prepend carry digit if non-zero after processing all digits
      Stage 7: Encode the result digit by digit:
               - '0' -> 'x'
               - digits '1'-'9' -> chr(ord('a') + (digit - 1))  i.e. 1->'a', 2->'b', ..., 9->'i'
    """
    # Stage 2: Remove dashes
    cleaned = machine_guid.replace('-', '')

    # Stage 3: Character transformation to digit string
    digit_chars = []
    for c in cleaned:
        if c.isalpha():
            val = ord(c.lower()) - ord('a') + 1  # a=1, b=2, ..., f=6, etc.
            digit_chars.append(str(val))
        else:
            digit_chars.append(c)  # keep digit as-is
    big_num_str = ''.join(digit_chars)

    # Stage 4: Big-integer string division by 5 (long division)
    quotient_digits = []
    carry = 0
    for ch in big_num_str:
        value = int(ch) + carry * 10
        q = value // 5
        carry = value % 5
        quotient_digits.append(str(q))
    quotient_str = ''.join(quotient_digits)

    # Stage 5: Strip leading zeros
    quotient_str = quotient_str.lstrip('0') or '0'

    # Stage 6: Big-integer multiply by 2 (right to left with carry)
    digits = list(quotient_str)
    carry2 = 0
    for i in range(len(digits) - 1, -1, -1):
        val = int(digits[i]) * 2 + carry2
        digits[i] = str(val % 10)
        carry2 = val // 10
    if carry2:
        digits.insert(0, str(carry2))
    doubled_str = ''.join(digits)

    # Stage 7: Encode digits to letters
    # 0 -> 'x', 1 -> 'a', 2 -> 'b', ..., 9 -> 'i'
    result = []
    for ch in doubled_str:
        d = int(ch)
        if d == 0:
            result.append('x')
        else:
            result.append(chr(ord('a') + d - 1))
    return ''.join(result)


def verify(machine_guid: str, serial: str) -> bool:
    """Verify a serial against the machine GUID."""
    expected = keygen(machine_guid)
    return serial == expected


def verify_known_examples():
    """Test against known examples from comments."""
    # From genass3 comment (no MachineGuid provided, just the serial example)
    # From @mike: MachineGuid b4fda2c6-0931-4672-8da0-ba7cf6c9f309 -> ihefdiddcgbehfiacfdxhfidfeehebb
    guid_mike = 'b4fda2c6-0931-4672-8da0-ba7cf6c9f309'
    key_mike = 'ihefdiddcgbehfiacfdxhfidfeehebb'
    computed = keygen(guid_mike)
    print(f'MachineGuid: {guid_mike}')
    print(f'Expected:    {key_mike}')
    print(f'Computed:    {computed}')
    print(f'Match: {computed == key_mike}')
    print()



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
