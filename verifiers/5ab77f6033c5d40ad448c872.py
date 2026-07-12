import math

def get_hash(txt: str) -> int:
    """Custom hash: sum of (4^length + ord(ch)) for each char, decrementing length."""
    result = 0
    length = len(txt)
    for ch in txt:
        result = result + int(math.pow(4, length)) + ord(ch)
        length -= 1
    return result


def expo(txt: str, length_out: int) -> str:
    """
    Pick chars from txt in a bouncing-middle pattern to produce a string of length_out.
    txt must have len >= 1.
    """
    p = len(txt)
    if p == 0:
        return ''
    num = 0
    num2 = p - 1
    num3 = p // 2
    num5 = p - 1
    flag = False
    result = []
    i = 0
    while len(result) < length_out:
        if num == num5:
            num = 0
        if num2 == 0:
            num2 = num5
        if num3 == (num5 - 1):
            flag = False
        elif num3 == 1:
            flag = True
        # Append up to 3 chars per iteration
        result.append(txt[num])
        if len(result) >= length_out:
            break
        result.append(txt[num3])
        if len(result) >= length_out:
            break
        result.append(txt[num2])
        if len(result) >= length_out:
            break
        num += 1
        num2 -= 1
        if flag:
            num3 += 1
        else:
            num3 -= 1
        i += 1
    return ''.join(result[:length_out])


# Alpha class: A=1, B=2, ..., Z=26; digits: '0'+10=10? 
# From C keygen: if q<=26 print char(q+64) => A..Z; if q>27 print char(q+48) => digit
# getVal is the reverse: letter -> ord(ch) - 64; digit -> ord(ch) - 48 - ASSUMPTION
# ASSUMPTION: alpha.getVal maps 'A'->1, 'B'->2,...,'Z'->26, '1'->27,...
def alpha_get_val(ch: str) -> int:
    c = ch.upper()
    if c.isalpha():
        return ord(c) - 64  # A=1..Z=26
    elif c.isdigit():
        # ASSUMPTION: digits map as char(q+48) => q = ord(c)-48, q>26
        return ord(c) - 48
    return 0


def alpha_get_char(num5: int) -> str:
    """Reverse of getVal."""
    if num5 <= 26:
        return chr(num5 + 64)  # A=1..Z=26
    else:
        return chr(num5 + 48)  # digits for 27+


def _compute_serial_chars(name: str):
    """Compute the 16 serial characters (without dashes)."""
    str1 = expo(name, 16)  # expo of name, len=16

    hash_val = get_hash(name)
    hash_str = str(hash_val)  # hash as decimal string
    str2 = expo(hash_str, 32)  # expo of hash string, len=32

    chars = []
    for i in range(16):
        num3 = ord(str1[i])
        # From the VB code:
        # ch = str2[i*2]   (first assignment)
        # ch = str2[i*2+1] (second assignment, overwrites)
        # num4 = Char.ConvertToUtf32(ch,0) + Char.ConvertToUtf32(ch,0)  => 2 * ord(ch)
        # But ch was overwritten by str2[i*2+1], so both uses of ch in num4 are str2[i*2+1]
        # ASSUMPTION: The writeup says "convert to unicode (i*2) n (i*2+1) and add them"
        # but the code sets ch twice and uses ch for both. Based on C keygen:
        # ch1 = str3[2*i]+48;  ch2 = str3[2*i+1]+48;  ch1+=ch2; ch1/=2;
        # In C, expo returns raw integer indices (0-based char values from digit string)
        # But in .NET, expo returns actual characters, so ord() is used.
        # The C keygen adds 48 to convert digit index to ASCII, then averages.
        # In .NET version: num4 = ord(str2[i*2]) + ord(str2[i*2+1]) (adding both chars)
        # ASSUMPTION: Based on C keygen logic (most faithful interpretation):
        ch1_val = ord(str2[i * 2])
        ch2_val = ord(str2[i * 2 + 1])
        num4 = ch1_val + ch2_val

        num3 = num3 // 2
        num4 = num4 // 2
        num5 = abs(num3 - num4)

        while num5 > 36:
            num5 = num5 // 2

        if num5 == 0:
            num5 = 1

        chars.append(num5)
    return chars


def keygen(name: str) -> str:
    """Generate a valid serial for the given name."""
    char_vals = _compute_serial_chars(name)
    serial_chars = [alpha_get_char(v) for v in char_vals]
    # Insert dashes: format XXXX-XXXX-XXXX-XXXX (16 chars -> 4 groups of 4)
    groups = []
    for g in range(4):
        groups.append(''.join(serial_chars[g * 4:(g + 1) * 4]))
    return '-'.join(groups)


def verify(name: str, serial: str) -> bool:
    """Verify a name/serial pair."""
    # Check format: must be XXXX-XXXX-XXXX-XXXX
    parts = serial.split('-')
    if len(parts) != 4 or any(len(p) != 4 for p in parts):
        return False
    serial_stripped = ''.join(parts)  # 16 chars

    char_vals = _compute_serial_chars(name)

    for i in range(16):
        ch = serial_stripped[i]
        if alpha_get_val(ch) != char_vals[i]:
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
