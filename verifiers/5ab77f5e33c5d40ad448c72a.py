import math

def verify(name, serial):
    """
    Reconstructed from the Pascal brute-force keygen (KEYGENCZ.PAS).
    The serial is a numeric string. Its digits are placed into array c[1..i]
    where i = len(name). Each digit of serial maps to c[pos].
    
    Conditions for a valid serial:
      1. step0: for all positions aa in 1..i, (ord(n[aa]) - c[aa]) & 0x0F != 0
      2. step1: sum = sum over a in 1..i of ((ord(n[a]) - c[a]) & 0x0F)
      3. step2/step3: compute CoCode and check sum == CoCode
    """
    i_name = len(name)
    if i_name < 5:
        return False
    
    # Convert serial (numeric string) to integer, then to digit array c[1..i]
    try:
        num = int(serial)
    except ValueError:
        return False
    
    # n_to_array: figure out number of digits, fill c
    # We need exactly i_name digits in the serial (padded with leading zeros if needed)
    # The Pascal code counts digits in num and uses that as i (cif)
    # but then uses i == i_name for iteration bounds in steps.
    # ASSUMPTION: serial must have exactly i_name digits (same length as name)
    digits = []
    tmp = num
    if tmp == 0:
        digits = [0]
    else:
        while tmp > 0:
            digits.append(tmp % 10)
            tmp //= 10
        digits.reverse()
    
    # In Pascal: cif = number of digits in num, then c[1..cif] filled
    # steps use i = cif throughout
    i = len(digits)
    
    # ASSUMPTION: i must equal i_name for the check to make sense
    if i != i_name:
        return False
    
    # Build c array (1-indexed), c[k] = digits[k-1]
    # n array (1-indexed), n[k] = name[k-1]
    n = [ord(ch) for ch in name]  # 0-indexed
    c = digits  # 0-indexed
    
    # step0: check (ord(n[aa]) - c[aa]) & 0x0F != 0 for all aa in 1..i
    # (Pascal: done:=false means FAIL if any position has (ord(n[aa])-c[aa])&0x0f == 0)
    done = True
    for aa in range(i):
        if (n[aa] - c[aa]) & 0x0F == 0:
            done = False
            break
    if not done:
        return False
    
    # step1: sum
    s = 0
    for a in range(i):
        s += (n[a] - c[a]) & 0x0F
    
    # step2: uses last character (index i-1, 1-indexed = i)
    last_idx = i - 1
    a_val = (n[last_idx] - c[last_idx]) & 0x0F
    a_sq = a_val * a_val * (i - 1) - 1  # Pascal: a:=a*a*(i-1)-1, but i is 1-indexed count
    # ASSUMPTION: In Pascal i is the digit count (same as name length). (i-1) in Pascal = i-1 in 0-indexed count = len-1
    d = (n[last_idx] - c[last_idx]) & 0x0F
    x = int(math.sqrt(a_sq)) if a_sq >= 0 else 0
    
    # step3:
    alfa = (d + x + 1) // 2
    x1 = int(math.sqrt(alfa * alfa * (i - 1) - 1)) if (alfa * alfa * (i - 1) - 1) >= 0 else 0
    
    # z depends on i // 4 (Pascal 1-indexed i)
    # In Pascal i = cif = number of digits = i_name
    i_pascal = i  # same
    if i_pascal // 4 == 1:
        z = (n[1] - c[1]) & 0x0F  # n[2] in Pascal (1-indexed) = n[1] in 0-indexed
    elif i_pascal // 4 == 2:
        z = (n[2] - c[2]) & 0x0F  # n[3] in Pascal
    elif i_pascal // 4 == 3:
        z = (n[3] - c[3]) & 0x0F  # n[4] in Pascal
    else:
        z = 0  # ASSUMPTION: for other values of i//4, z=0
    
    CoCode = ((alfa + 1 + x1) // 2) - z
    
    return s == CoCode


def keygen(name):
    """
    Brute-force keygen: tries numeric values with exactly len(name) digits.
    Returns first valid serial found, or None.
    """
    i_name = len(name)
    if i_name < 5:
        return None
    
    # Try all i_name-digit numbers
    start = 10 ** (i_name - 1)
    end = 10 ** i_name
    
    for num in range(start, end):
        s = str(num)
        if verify(name, s):
            return s
    return None



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
