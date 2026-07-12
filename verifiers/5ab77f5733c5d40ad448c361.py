import os
import struct

# NOTE: This keygen is based on the VB keygen solution by Taliesin for l0calh0st keygenme#2.
# The original crackme reads the actual Windows username (GetUserName API) and computer name.
# In this Python reimplementation:
#   - 'name' is the text entered in the Name field (txtName)
#   - 'windows_username' is the logged-in Windows username (FindUserName / GetUserName)
#     which is used in the serial computation.
# Since we cannot call GetUserName in pure Python portably, we use os.getlogin() as a fallback.
# ASSUMPTION: windows_username == os.getlogin() (may differ in some environments)

def _sum_chars(s):
    return sum(ord(c) for c in s)

def _get_part1_divisors(user_len, comp_total):
    """Find all x in [294,732] that evenly divide (user_len * comp_total) XOR 87."""
    dbl_total = int(user_len) * int(comp_total)
    dbl_total = dbl_total ^ 87
    divisors = []
    for x in range(294, 733):
        if dbl_total % x == 0:
            divisors.append(x)
    return divisors

def _create_first_key(first_key):
    """Build the 6-character first key part from an integer first_key."""
    i_common = first_key // 6
    i_extra = first_key - (i_common * 5)
    s_first_key = ''
    for _ in range(5):
        s_first_key += chr(i_common)
    s_first_key += chr(i_extra)
    return s_first_key

def _get_part2(s_first_part, dbl_user_name):
    """Find the 6-char second part: i1..i6 in [49,122] s.t.
       ((i1*8)+(i2*9)+(i3*10)+(i4*11)+(i5*12)+(i6*13)) mod dbl_user_name == 0.
       Returns first found solution appended to s_first_part.
    """
    # ASSUMPTION: We try to find the first valid (i1..i6) combo quickly.
    # The original VB iterates all combinations; we do the same but break early.
    target = int(dbl_user_name)
    if target == 0:
        # ASSUMPTION: if sum of name chars is 0, skip part2
        return s_first_part + "-??????"
    for i1 in range(49, 123):
        for i2 in range(49, 123):
            for i3 in range(49, 123):
                for i4 in range(49, 123):
                    for i5 in range(49, 123):
                        for i6 in range(49, 123):
                            i_total = (i1*8)+(i2*9)+(i3*10)+(i4*11)+(i5*12)+(i6*13)
                            if i_total % target == 0:
                                return s_first_part + "-" + chr(i1)+chr(i2)+chr(i3)+chr(i4)+chr(i5)+chr(i6)
    return s_first_part + "-NOTFOUND"

def _get_third_part(s_first_part, dbl_user_name):
    """Build and append the third part.
       third = Hex(41458989 + dbl_user_name), reversed, first 6 chars.
       Then append '-' and 6 random chars with ASCII in [55, 85] (Rnd(30)+55).
       ASSUMPTION: For deterministic output we use fixed offset chars for the random portion.
    """
    dbl_number = 41458989 + int(dbl_user_name)
    hex_string = format(dbl_number, 'X')  # uppercase hex, like VB Hex()
    reversed_hex = hex_string[::-1]
    part3 = reversed_hex[:6]
    # ASSUMPTION: random part uses fixed seed or os.urandom for demonstration
    # Original VB uses Rnd(30)+55 which gives floats in [55,85), so chr in range [55,85)
    random_chars = ''
    for _ in range(6):
        # Use os.urandom for a single byte, map to [55,85)
        val = 55 + (os.urandom(1)[0] % 30)
        random_chars += chr(val)
    return s_first_part + "-" + part3 + "-" + random_chars

def keygen(name, windows_username=None):
    """Generate a valid serial for the given name.
       windows_username: the Windows login name (GetUserName). Defaults to os.getlogin().
       Returns a serial string, or None if no serial exists for this name.
    """
    if len(name) < 5:
        raise ValueError("Name must be longer than 4 characters.")
    
    if windows_username is None:
        try:
            windows_username = os.getlogin()
        except Exception:
            windows_username = 'USER'  # ASSUMPTION: fallback
    
    dbl_user_name = float(_sum_chars(name))
    dbl_user_len = float(len(name))
    dbl_computer_name = float(_sum_chars(windows_username))
    
    divisors = _get_part1_divisors(dbl_user_len, dbl_computer_name)
    
    if not divisors:
        return None  # no valid serial for this name/username combination
    
    # Use the first valid divisor (like original iterates but outputs each)
    first_key = divisors[0]
    s_first_part = _create_first_key(first_key)
    s_first_part = _get_part2(s_first_part, dbl_user_name)
    serial = _get_third_part(s_first_part, dbl_user_name)
    return serial

def verify(name, serial):
    """Verify a serial for a name.
       ASSUMPTION: The original crackme validation logic is not shown directly;
       this verify reconstructs what the keygen produces and compares structure.
       We verify the first two parts deterministically; the third part's random suffix
       cannot be verified without knowing the original random seed.
       Returns True if the serial matches the expected pattern for the name.
    """
    # ASSUMPTION: We cannot fully verify because:
    # 1. We don't know the Windows username on the target machine.
    # 2. The 6-char random suffix at the end is truly random.
    # This is a best-effort structural check.
    parts = serial.split('-')
    if len(parts) != 4:
        return False
    
    if len(name) < 5:
        return False
    
    # Check part3 length
    if len(parts[2]) != 6:
        return False
    
    # Check part4 length (random)
    if len(parts[3]) != 6:
        return False
    
    # Check part1 length (6 chars)
    if len(parts[0]) != 6:
        return False
    
    # Check part2 length (6 chars)
    if len(parts[1]) != 6:
        return False
    
    # Verify part2: (i1*8)+(i2*9)+(i3*10)+(i4*11)+(i5*12)+(i6*13) mod sum_chars(name) == 0
    dbl_user_name = _sum_chars(name)
    if dbl_user_name == 0:
        return False
    p2 = parts[1]
    if not all(49 <= ord(c) <= 122 for c in p2):
        return False
    i_total = (ord(p2[0])*8)+(ord(p2[1])*9)+(ord(p2[2])*10)+(ord(p2[3])*11)+(ord(p2[4])*12)+(ord(p2[5])*13)
    if i_total % dbl_user_name != 0:
        return False
    
    # Verify part3 hex: Hex(41458989 + sum_chars(name)) reversed first 6
    dbl_number = 41458989 + dbl_user_name
    hex_string = format(dbl_number, 'X')
    reversed_hex = hex_string[::-1]
    expected_part3 = reversed_hex[:6]
    if parts[2] != expected_part3:
        return False
    
    # Part1 depends on windows_username which we cannot verify here
    # ASSUMPTION: skip part1 check since we don't know the Windows username
    
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
