import ctypes
import struct


def name_hash(name, ebx_init):
    """
    Simulate the inner hash loop:
      MOV DL, BYTE PTR DS:[EAX]   ; dl = current char
      IMUL ECX, ECX, 48           ; ecx = ecx * 0x48
      SUB ECX, EDX                ; ecx = ecx - dl
      SUB ECX, 6F                 ; ecx = ecx - 0x6F
      MOV EDX, ECX
      XOR ECX, 0BACAF             ; ecx = ecx ^ 0xBACAAF  (writeup says 0BACAF)
      INC EAX
      DEC EBX
      CMP EBX, 0
      JNZ loop

    ebx_init = length of the string controlling iteration count
    Returns ECX (32-bit signed wrapping)
    """
    ecx = ctypes.c_int32(0)
    ebx = ctypes.c_int32(ebx_init)
    idx = 0
    while ebx.value != 0:
        # Read byte from string (if idx >= len, read 0 -- undefined, but approximate)
        if idx < len(name):
            dl = ord(name[idx]) if isinstance(name[idx], str) else name[idx]
        else:
            dl = 0  # ASSUMPTION: past end of string, byte is 0
        ecx = ctypes.c_int32(ecx.value * 0x48)
        ecx = ctypes.c_int32(ecx.value - dl)
        ecx = ctypes.c_int32(ecx.value - 0x6F)
        # edx = ecx (saved but only used in second call context)
        ecx = ctypes.c_int32(ecx.value ^ 0x0BACAF)
        idx += 1
        ebx = ctypes.c_int32(ebx.value - 1)
    return ecx.value


def combine(r1_val, r2_val):
    """
    004012D1 function result combination:
      eax = r1, ebx = r2
      edx = eax
      edx = edx ^ ebx          ; edx = r1 ^ r2
      edx = edx ^ 0xFFAC       ; edx = edx ^ 0xFFAC
      ebx = ebx ^ 0x553        ; ebx = r2 ^ 0x553
      eax = eax + ebx          ; eax = r1 + (r2 ^ 0x553)
      ebx = ebx + edx          ; ebx = (r2^0x553) + (r1^r2^0xFFAC)
      ebx = ebx - 1
      eax = eax + ebx
    Returns (eax, ebx) as 32-bit values
    """
    eax = ctypes.c_int32(r1_val)
    ebx = ctypes.c_int32(r2_val)
    edx = ctypes.c_int32(eax.value)
    edx = ctypes.c_int32(edx.value ^ ebx.value)
    edx = ctypes.c_int32(edx.value ^ 0xFFAC)
    ebx = ctypes.c_int32(ebx.value ^ 0x553)
    eax = ctypes.c_int32(eax.value + ebx.value)
    ebx = ctypes.c_int32(ebx.value + edx.value)
    ebx = ctypes.c_int32(ebx.value - 1)
    eax = ctypes.c_int32(eax.value + ebx.value)
    return eax.value, ebx.value


def check_equality(r1_final, r2_final):
    """
    00401346 function:
      if r1 != r2: fail
      else:
        ebx = r2 ^ 0x8E
        ebx = ebx + r1
        save as r2
    Returns (equal, final_r2)
    """
    if r1_final != r2_final:
        return False, None
    ebx = ctypes.c_int32(r2_final)
    ebx = ctypes.c_int32(ebx.value ^ 0x8E)
    ebx = ctypes.c_int32(ebx.value + r1_final)
    return True, ebx.value


def build_serial(r1_eax, r2_ebx):
    """
    ASSUMPTION: The two 32-bit results are formatted as hex strings (or decimal),
    then concatenated to form a 24-char string. Positions 3 and 13 (0-indexed) are
    replaced by '-', and the first 3 chars are replaced by 'KOS'.
    The writeup says 4th and 14th positions replaced by '-' (1-indexed = index 3 and 13),
    and first three letters replaced by 'KOS'.
    The exact formatting of the numbers into the string is not fully described.
    ASSUMPTION: format each as 8-char uppercase hex, concatenate = 16 chars,
    then pad or repeat to reach 24 chars.
    """
    # ASSUMPTION: format both values as 8-hex-digit uppercase strings, concatenate
    part1 = '%08X' % (r1_eax & 0xFFFFFFFF)
    part2 = '%08X' % (r2_ebx & 0xFFFFFFFF)
    raw = part1 + part2  # 16 chars
    # ASSUMPTION: repeat/extend to 24 chars
    raw = (raw * 2)[:24]  # 24 chars
    serial = list(raw)
    # Replace positions 3 and 13 (0-indexed) with '-'
    serial[3] = '-'
    serial[13] = '-'
    # Replace first 3 chars with 'KOS'
    serial[0] = 'K'
    serial[1] = 'O'
    serial[2] = 'S'
    return ''.join(serial)


def get_login_name():
    # ASSUMPTION: on non-Windows, we use a placeholder login name
    import os
    return os.getlogin()


def compute_hashes(name, login_name):
    name_len = len(name)
    # First call: hash of name, iterated name_len times
    r1 = name_hash(name, name_len)
    # Second call: hash of login_name, but BX comes from previous (name_len) if login shorter
    # writeup says EBX = strlen(name), not strlen(login_name)
    # ASSUMPTION: iteration count is still name_len (the bug described)
    r2 = name_hash(login_name, name_len)
    return r1, r2


def verify(name, serial):
    if len(name) <= 3 or len(name) > 0x13:
        return False
    if len(serial) != 0x18:
        return False
    # Check '-' at positions 3 and 13 (0-indexed)
    if serial[3] != '-' or serial[13] != '-':
        return False
    # Check 'KOS' prefix
    if not serial.startswith('KOS'):
        return False

    login_name = get_login_name()
    r1, r2 = compute_hashes(name, login_name)
    eax, ebx = combine(r1, r2)
    # For verify, we need the final results to match after combine
    # ASSUMPTION: the combine output (eax, ebx) are r1_final and r2_final for equality check
    equal, final_r2 = check_equality(eax, ebx)
    if not equal:
        return False
    expected = build_serial(eax, final_r2)
    return serial == expected


def keygen(name):
    if len(name) <= 3 or len(name) > 0x13:
        raise ValueError('Name must be 4-19 characters')
    login_name = get_login_name()
    r1, r2 = compute_hashes(name, login_name)
    eax, ebx = combine(r1, r2)
    # ASSUMPTION: after combine, eax goes back as r1, ebx as r2 into the equality function
    # But since eax and ebx will generally not be equal, the equality check fails
    # The keygen must produce a serial from these values regardless (as the C keygen does)
    # ASSUMPTION: skip equality check for keygen, just format the serial
    # The actual serial generation may differ; this is a best-effort reconstruction
    serial = build_serial(eax, ebx)
    return serial



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
