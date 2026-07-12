import hashlib


def md5_hash(name: str) -> str:
    """Compute MD5 of name (ASCII encoded), return uppercase hex string (no separators)."""
    digest = hashlib.md5(name.encode('ascii')).digest()
    return ''.join(f'{b:02X}' for b in digest)


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.

    Serial layout (48 chars, 0-indexed):
      - Positions 0,2,4,...,30  (i*2 for i in 0..15): md5[i]
      - Positions 32..47       (i+0x10 for i in 0x10..0x1F): md5[i]  (i.e. md5[16..31])
      - Odd positions 1,3,5,...,31: numeric digits (0-9) satisfying parity constraints

    Parity constraints on the numeric digits at odd positions:
      Let d[k] = int(serial[2*k+1]) for k in 0..15  (the 16 digits at odd positions)

      Group 1 (k=0..2, i.e. serial positions 1,3,5 and 3,5,7):
        for k in 0,1,2: (d[k] + d[k+1]) % 2 != 0  => sum must be ODD
      Group 2 (k=4..6, serial positions 9,11,13 and 11,13,15):
        for k in 4,5,6: (d[k] + d[k+1]) % 2 != 1  => sum must be EVEN
      Group 3 (k=8..10, serial positions 17,19,21 and 19,21,23 -- 0x11=17):
        for k in 8,9,10: (d[k] + d[k+1]) % 2 != 0  => sum must be ODD
      Group 4 (k=12..14, serial positions 25,27,29 and 27,29,31 -- 0x19=25):
        for k in 12,13,14: (d[k] + d[k+1]) % 3 != 1  => sum%3 must be 0 or 2

    We pick fixed digits satisfying these constraints:
      d[0..3]  => need d[0]+d[1] odd, d[1]+d[2] odd, d[2]+d[3] odd
                  choose: 1,0,1,0  (1+0=1 odd, 0+1=1 odd, 1+0=1 odd) OK
      d[4..7]  => need d[4]+d[5] even, d[5]+d[6] even, d[6]+d[7] even
                  choose: 0,0,0,0  (all sums 0, even) OK
      d[8..11] => need d[8]+d[9] odd, d[9]+d[10] odd, d[10]+d[11] odd
                  choose: 1,0,1,0  OK
      d[12..15]=> need d[12]+d[13]%3 != 1, d[13]+d[14]%3 != 1, d[14]+d[15]%3 != 1
                  choose: 0,0,0,0  (all sums 0, 0%3=0 != 1) OK
    """
    md5 = md5_hash(name)
    serial = ['4'] * 48  # placeholder

    # Place MD5 chars at even positions 0..30
    for i in range(16):
        serial[i * 2] = md5[i]

    # Place MD5 chars at positions 32..47
    for i in range(16, 32):
        serial[i + 16] = md5[i]

    # Place digits at odd positions 1,3,5,...,31
    # Using fixed digits: d = [1,0,1,0, 0,0,0,0, 1,0,1,0, 0,0,0,0]
    digits = [1, 0, 1, 0,
               0, 0, 0, 0,
               1, 0, 1, 0,
               0, 0, 0, 0]
    for i in range(16):
        serial[i * 2 + 1] = str(digits[i])

    return ''.join(serial)


def verify(name: str, serial: str) -> bool:
    """
    Verify a (name, serial) pair.

    Checks:
    1. name is non-empty
    2. serial has exactly 48 characters
    3. MD5(name) chars appear at correct positions in serial
    4. Numeric parity constraints on odd-position digits
    """
    if len(name) == 0:
        return False
    if len(serial) != 48:
        return False

    md5 = md5_hash(name)
    flag = True
    flag2 = True

    try:
        # Check MD5 at even positions 0..30
        for i in range(16):
            if serial[i * 2] != md5[i]:
                flag = False

        # Check MD5 at positions 32..47
        for j in range(0x20, 0x30):
            if serial[j] != md5[j - 0x10]:
                flag = False

        # Parity check group 1: positions 1,3,5,7 (k=1,3,5 stepping by 2)
        # serial positions k and k+2 must have odd sum
        for k in range(1, 7, 2):
            a = int(serial[k])      # must be 0-9 digit
            b = int(serial[k + 2])  # must be 0-9 digit
            if (a + b) % 2 == 0:
                flag2 = False

        # Parity check group 2: positions 9,11,13,15 must have even sum
        for m in range(9, 15, 2):
            a = int(serial[m])
            b = int(serial[m + 2])
            if (a + b) % 2 == 1:
                flag2 = False

        # Parity check group 3: positions 17,19,21,23 must have odd sum (0x11=17)
        for n in range(0x11, 0x16, 2):
            a = int(serial[n])
            b = int(serial[n + 2])
            if (a + b) % 2 == 0:
                flag2 = False

        # Parity check group 4: positions 25,27,29,31 sum%3 must != 1 (0x19=25)
        for p in range(0x19, 0x1f, 2):
            a = int(serial[p])
            b = int(serial[p + 2])
            if (a + b) % 3 == 1:
                flag2 = False

    except (ValueError, IndexError):
        return False

    return flag and flag2



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
