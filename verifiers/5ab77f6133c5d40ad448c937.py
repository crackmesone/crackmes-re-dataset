# Reconstruction of dr.xj Keygen This #1 validation algorithm
# Based on the VB6 keygen source code found in the writeup (Form1.frm)
# The keygen source was truncated but enough logic is visible to reconstruct.

# Constants from the VB6 source
MY_STR = "Mehrpouya"
# ASSUMPTION: MyStr2 is not used in the core serial generation visible in the writeup


def generate_serial(name: str) -> str:
    """
    Reconstructs the serial generation algorithm from the VB6 keygen source.
    Steps:
    1. Reverse the name
    2. XOR each char of reversed name with corresponding char of 'Mehrpouya',
       add 2, and concatenate the numeric results -> Temp
    3. Compute len1 = Fix(Len(Temp) / 3), len2 = Len(Temp) / 2 + 1
    4. Take first len2 chars of Temp, XOR with 679851 -> temp2
    5. Take remaining chars of Temp (from len2+1 onward), XOR with temp2 -> temp3
       # ASSUMPTION: the 'rest' uses temp2 as the XOR key (consistent with the writeup example)
    6. Concatenate temp2 and temp3 -> MySTR_local (a numeric string)
    7. If len(MySTR_local) < 18, pad by appending characters from MySTR_local cyclically
       using index = len(MySTR_local)*2 (i.e., append chars from position len*2 onward, wrapping)
       # ASSUMPTION: The loop appends chars at position (current_len * 2) mod len(MySTR_local)
       until total length reaches 18
    """
    if len(name) < 4:
        raise ValueError("Name must be at least 4 characters")

    # Step 1 & 2: Reverse name, XOR with Mehrpouya chars, +2, concatenate
    reversed_name = name[::-1]
    temp = ""
    for i in range(len(reversed_name)):
        ch_name = ord(reversed_name[i])
        # ASSUMPTION: if name is longer than MY_STR, wrap around MY_STR
        ch_key = ord(MY_STR[i % len(MY_STR)])
        temp += str((ch_name ^ ch_key) + 2)

    # Step 3: lengths
    import math
    len_temp = len(temp)
    len1 = math.floor(len_temp / 3)   # Fix() in VB = floor for positive
    len2 = int(len_temp / 2 + 1)      # VB integer truncation; +1 so len2 chars taken

    # Step 4: first len2 chars XOR 679851
    first_part_str = temp[0:len2]      # VB Mid(Temp, 1, len2) -> chars 1..len2
    # XOR string-as-integer with 679851
    # In VB, XOR on a numeric string converts it to a number first
    try:
        temp2 = int(first_part_str) ^ 679851
    except ValueError:
        # ASSUMPTION: if non-numeric, treat as 0
        temp2 = 0 ^ 679851

    # Step 5: remaining chars XOR temp2
    rest_str = temp[len2:]             # remaining characters
    if rest_str:
        try:
            temp3 = int(rest_str) ^ temp2
        except ValueError:
            temp3 = 0 ^ temp2
    else:
        temp3 = temp2  # ASSUMPTION: if no remaining chars, use temp2 alone

    # Step 6: concatenate
    my_str_local = str(temp2) + str(temp3)

    # Step 7: pad to 18 characters
    # From writeup: difference = 18 - len(my_str_local)
    # difference * 2 gives starting index, then take chars one by one
    # ASSUMPTION: the loop appends chars at positions (len(my_str_local)*2), 
    # (len(my_str_local)*2 + 1), etc., cycling if needed, until length == 18
    serial = my_str_local
    if len(serial) < 18:
        # In the example: MySTR_local = '731103730913' (len=12), need 6 more
        # diff = 18-12=6, diff*2=12, so start reading from index 12 of '731103730913'
        # index 12 is out of bounds for len-12 string, so it wraps (mod)
        # ASSUMPTION: wrap around using modulo
        diff = 18 - len(serial)
        start_idx = (len(serial) * 2) % len(serial) if len(serial) > 0 else 0
        # But from the example: Mid('731103730913', 12, 1) -> 12th char (1-based) = '3'
        # In 0-based: index 11 = '3'. len=12, start_idx = 12*2 % 12 = 0? 
        # ASSUMPTION: VB Mid is 1-based, so position = len*2 mod len + 1 in 1-based
        # Re-examine: len=12, diff*2=12, position in loop = 12 (1-based) = index 11 (0-based)
        # So start_pos_1based = diff * 2  (not len * 2)
        start_pos = diff * 2  # 1-based starting position in VB
        for j in range(diff):
            idx_1based = start_pos + j
            # wrap around
            idx_0based = (idx_1based - 1) % len(serial)
            serial += serial[idx_0based]
    elif len(serial) > 18:
        serial = serial[:18]

    return serial


def verify(name: str, serial: str) -> bool:
    """
    Verifies name/serial pair by generating the expected serial and comparing.
    """
    if len(name) < 4:
        return False
    try:
        expected = generate_serial(name)
    except Exception:
        return False
    return serial == expected


def keygen(name: str) -> str:
    """
    Returns the valid serial for the given name.
    """
    return generate_serial(name)


# Quick self-test with the example from the writeup

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
