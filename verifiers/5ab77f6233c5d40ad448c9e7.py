# Reverse-engineered keygen for 'keygenme by versus' (Borland Delphi)
# Based on disassembly dump from the solution writeup.
#
# Summary of the algorithm (from disassembly):
#
# 1. Read name from Edit1, serial from Edit2.
# 2. Compute name_len = len(name)  (stored at [ebp-$08] via TWinControl.WMFontChange = GetTextLen)
# 3. Starting with ecx=1, esi=0, loop over name characters (skipping first 2? cmp eax,2 / jl skip):
#      eax = ord(name[ecx-1+1])  -- i.e. name[ecx]  (1-based, ecx starts at 1)
#      esi += eax
#      esi ^= ecx
#      ecx++
#      dec name_len; jnz loop
#    After loop: last_eax = ord of last char processed, stored at [ebp-$0C]
#    Then: esi *= 10   => stored at [ebp-$10]  (this is the 'hash')
#
# ASSUMPTION: The loop processes all characters starting from index 1 (ecx starts at 1,
#   loop condition cmp eax(=len),2 / jl skip means if len<2 skip entirely).
#   The movzx reads byte ptr [ecx+eax-1] where eax=[ebp-$04]=len, so it reads name[ecx+len-1]
#   which wraps; more likely it's name[ecx-1] using ecx as 1-based index with
#   [ebp-$04] holding pointer. ASSUMPTION: treat as name[i] for i in 1..len-1.
#
# 4. Convert esi*10 to decimal string => serial_prefix_str
#
# 5. Serial validation loop (ecx=1):
#    For each position in serial_str vs serial_prefix_str:
#      s_char = ord(serial[ecx-1])  XOR 0x14 + 0x26  => s_val
#      p_char = ord(prefix[ecx-1]) XOR 0x14 + 0x43 - 0x1D  => p_val  (= ord(prefix[ecx-1]) + 0x12 ... wait)
#      Actually: p_val = ord(prefix[ecx-1]) XOR 0x14 + 0x43 - 0x1D
#               = ord(prefix[ecx-1]) ^ 20 + 67 - 29
#               = ord(prefix[ecx-1]) ^ 20 + 38
#      s_val  = ord(serial[ecx-1])  ^ 20 + 38
#      So the comparison cmp edx,eax means p_val == s_val
#      => (ord(prefix[i]) ^ 20 + 38) == (ord(serial[i]) ^ 20 + 38)
#      => ord(prefix[i]) == ord(serial[i])  (the XOR/add cancel)
#      UNLESS edx == [ebp-$1C] = 0x5F = 95 = '_' sentinel
#
# 6. When p_val == 0x5F (sentinel '_'), a special check kicks in:
#    next_serial_char + last_name_char (from [ebp-$0C]) mod 10 must == 6
#    Then serial must continue with literal '-ALG'
#    Then 0x15 mod 10 must == remainder stored (0x15=21, 21%10=1... ASSUMPTION)
#    Finally result=1 => valid
#
# ASSUMPTION: The serial format is: <hash_digits>-ALG  with a special digit inserted
#   at a '_'-marked position based on the prefix string from the hash.
#   The '_' (0x5F) is initialized at [ebp-$1C] and seems to mark end-of-prefix.
#
# Based on the string references '***-' and '-***' and the literal bytes checked
#   0x2D('-'), 0x41('A'), 0x4C('L'), 0x47('G'), the serial ends with '-ALG'.
#
# ASSUMPTION: serial format is  XXXXXXD-ALG  where XXXXXX are digits derived from hash
#   and D is a digit such that (D_ord + last_name_char_ord) % 10 == 6

def compute_hash(name):
    """Compute the hash value from the name."""
    if len(name) < 2:
        return 0, 0
    ecx = 1
    esi = 0
    name_len = len(name)
    last_eax = 0
    # Loop: runs name_len times (dec name_len; jnz)
    for _ in range(name_len):
        # movzx eax, byte ptr [ecx + name_ptr - 1]  => name[ecx-1] (0-based: name[ecx-1])
        # ASSUMPTION: indexing is 0-based as name[ecx-1] with ecx starting at 1
        idx = ecx - 1
        if idx >= len(name):
            break
        eax = ord(name[idx])
        esi = (esi + eax) & 0xFFFFFFFF
        esi = (esi ^ ecx) & 0xFFFFFFFF
        last_eax = eax
        ecx += 1
    esi = (esi * 10) & 0xFFFFFFFF
    return esi, last_eax


def keygen(name):
    """Generate a valid serial for the given name."""
    if len(name) < 2:
        # ASSUMPTION: name must be at least 2 characters
        return None

    hash_val, last_char_ord = compute_hash(name)
    # Convert hash to decimal string (this is the 'prefix' used in serial comparison)
    prefix_str = str(hash_val)

    # The serial comparison loop:
    # s_val = ord(serial[i]) ^ 0x14 + 0x26
    # p_val = ord(prefix[i]) ^ 0x14 + 0x43 - 0x1D = ord(prefix[i]) ^ 0x14 + 0x26
    # => serial[i] must equal prefix[i] for normal chars
    # When p_val == 0x5F (sentinel), special handling:
    #   next serial byte + last_char_ord must satisfy (x + last_char_ord) % 10 == 6
    #   then serial must end with '-ALG'
    #
    # ASSUMPTION: The '_' sentinel in [ebp-$1C]=0x5F is compared against p_val.
    # p_val = ord(prefix[i]) ^ 0x14 + 0x26
    # 0x5F = 95 => ord(prefix[i]) ^ 0x14 + 0x26 = 95 => ord(prefix[i]) ^ 0x14 = 69 => ord(prefix[i]) = 69^20 = 81 = 'Q'
    # ASSUMPTION: this sentinel triggers when prefix string is exhausted (p_char==0 check at 004581FC/00458205)
    # The jz at 004581FF checks if serial or prefix lengths are 0 => fail
    # The jz at 00458221 checks if p_char==0 (null terminator = end of prefix string)
    # So when prefix string ends, we need the special '-ALG' suffix.
    # The check: (ord(serial[ecx]) + last_char_ord) % 10 == 6
    # We need a digit d such that (d + last_char_ord) % 10 == 6

    # Find required digit after prefix
    d = (6 - last_char_ord) % 10
    digit_char = chr(ord('0') + d)

    serial = prefix_str + digit_char + '-ALG'
    return serial


def verify(name, serial):
    """Verify if serial is valid for name."""
    if len(name) < 2:
        return False
    if not serial:
        return False

    hash_val, last_char_ord = compute_hash(name)
    prefix_str = str(hash_val)

    # Simulate the comparison loop
    ecx = 1  # 1-based index
    prefix_bytes = prefix_str.encode('ascii') + b'\x00'
    serial_bytes = serial.encode('ascii') + b'\x00'

    while True:
        # Check lengths
        if ecx > len(serial_bytes) - 1 or ecx > len(prefix_bytes) - 1:
            return False

        s_byte = serial_bytes[ecx - 1]
        p_byte = prefix_bytes[ecx - 1]

        if p_byte == 0:
            return False
        if s_byte == 0:
            return False

        s_val = (s_byte ^ 0x14) + 0x26
        p_val = (p_byte ^ 0x14) + 0x43 - 0x1D  # = (p_byte ^ 0x14) + 0x26

        SENTINEL = 0x5F  # '_' = 95, but this is compared against p_val not p_byte
        # ASSUMPTION: sentinel check is on p_val
        if p_val == SENTINEL:
            # Special branch at 00458238
            # Check: (serial[ecx] + last_char_ord) % 10 == 6
            if ecx >= len(serial_bytes) - 1:
                return False
            next_s = serial_bytes[ecx]  # ecx is already incremented implicitly
            if (next_s + last_char_ord) % 10 != 6:
                return False
            ecx += 1
            # Check literal '-'
            if ecx >= len(serial_bytes) - 1 or serial_bytes[ecx] != 0x2D:
                return False
            ecx += 1
            # Check 'A'
            if ecx >= len(serial_bytes) - 1 or serial_bytes[ecx] != 0x41:
                return False
            ecx += 1
            # Check 'L'
            if ecx >= len(serial_bytes) - 1 or serial_bytes[ecx] != 0x4C:
                return False
            ecx += 1
            # Check 'G'
            if ecx >= len(serial_bytes) - 1 or serial_bytes[ecx] != 0x47:
                return False
            # Final check: 0x15 % 10 == 1... ASSUMPTION: this always passes (21%10=1, stored but not further validated here)
            # The result is set to 1 => valid
            return True
        else:
            if p_val != s_val:
                return False
            ecx += 1



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
