import ctypes
import struct

# ============================================================
# Reconstruction of znycuk's #1 CrackMe keygen algorithm
# Based on the keygen source (Keygen.asm) by red477
# ============================================================
#
# The crackme uses:
#   1. Computer name (GetComputerName)
#   2. Username (GetUserName)
# Both padded to at least 4 chars with 'ZNY' if shorter.
#
# initB1(p1=computerName_dword, p2=userName_dword) fills
# array aB[8] (8 DWORDs, indices 0..7)
#
# Then the 4-char serial name is processed char-by-char to
# produce 4 WORDs formatted as "%.4X-%.4X-%.4X-%.4X"
# ============================================================

def _to_uint32(v):
    return v & 0xFFFFFFFF

def _ror32(v, n):
    v = _to_uint32(v)
    n = n % 32
    return _to_uint32((v >> n) | (v << (32 - n)))

def _neg32(v):
    return _to_uint32((-v) & 0xFFFFFFFF)

def _shl32(v, n):
    return _to_uint32(v << n)

def initB1(p1, p2):
    """Fill aB array (8 DWORDs) from p1 (computerName dword) and p2 (userName dword).
    aB layout: for cl in 0,1 and si in 0,1,2,3:
      index = 2*si + cl  => but stored as [aB + eax*4] where eax = 2*si + cl
    So aB[2*si + cl] = result after si operations on (p2 if cl==0 else p1)
    """
    aB = [0] * 8
    for cl in range(2):
        edx = p2 if cl == 0 else p1
        for si in range(4):
            if si == 0:
                edx = _to_uint32(edx ^ 0xABDEADAB)
            elif si == 1:
                edx = _neg32(edx)
            elif si == 2:
                edx = _shl32(edx, 3)
            elif si == 3:
                edx = _ror32(edx, 1)
            idx = 2 * si + cl
            aB[idx] = _to_uint32(edx)
    return aB

def _pad4(s, pad='ZNY'):
    """Pad string to at least 4 chars using 'ZNY' characters."""
    if len(s) < 4:
        needed = 4 - len(s)
        s = s + pad[:needed]
    return s

def _get_dword(s):
    """Take first 4 bytes of string as little-endian DWORD."""
    b = s.encode('ascii', errors='replace')[:4]
    b = b.ljust(4, b'\x00')
    return struct.unpack('<I', b)[0]

def _compute_key_word(ch, aB_val):
    """
    Per-character key computation from the dlgproc loop:
      al = byte(ch) & 0xF0; rol al,4 => top nibble
      if al == 3: bl = al
      else: bl = al - 4

      al = byte(ch) & 0x0F
      if al <= 7: bh = 0 else bh = 1

      eax = 2 * bh + bl  => index into aB
      eax = aB[index]
      eax = ror(eax, 8)   => 32-bit ror by 8
      xor ah, byte(ch)
      xor al, byte(ch)
      ror al, 4
      ror ah, 4
      swap al and ah
      result = movzx ax  => lower 16 bits
    """
    c = ord(ch) & 0xFF

    # top nibble
    al_top = (c & 0xF0) >> 4  # rol by 4 of (c & 0xF0) in 8-bit = top nibble
    if al_top == 3:
        bl = al_top
    else:
        bl = (al_top - 4) & 0xFF

    # bottom nibble => bh
    al_bot = c & 0x0F
    bh = 0 if al_bot <= 7 else 1

    # index
    idx = (2 * bh + bl) & 0xFF
    # ASSUMPTION: if idx >= 8, behavior undefined; we clamp
    idx = idx % 8

    eax = aB_val[idx]
    # ror eax, 8
    eax = _ror32(eax, 8)

    # extract bytes: eax as 4 bytes
    b0 = eax & 0xFF          # al
    b1 = (eax >> 8) & 0xFF   # ah
    b2 = (eax >> 16) & 0xFF
    b3 = (eax >> 24) & 0xFF

    # xor ah, c
    b1 = (b1 ^ c) & 0xFF
    # xor al, c
    b0 = (b0 ^ c) & 0xFF

    # ror al, 4  (8-bit ror by 4)
    b0 = ((b0 >> 4) | (b0 << 4)) & 0xFF
    # ror ah, 4
    b1 = ((b1 >> 4) | (b1 << 4)) & 0xFF

    # swap al and ah
    al_new = b1
    ah_new = b0

    # movzx eax, ax
    result = (ah_new << 8) | al_new
    return result & 0xFFFF

def keygen(name, computer_name=None, user_name=None):
    """
    Generate key for a 4-char name.
    computer_name and user_name default to 'ZNY' padding if not given.
    ASSUMPTION: since we can't call GetComputerName/GetUserName in Python portably,
    we default to 'ZNY' padded strings. Pass actual values for real use.
    """
    if len(name) != 4:
        raise ValueError("Name must be exactly 4 characters")

    # Pad computer name and user name
    if computer_name is None:
        # ASSUMPTION: default to empty string (will be padded with ZNY)
        computer_name = ''
    if user_name is None:
        user_name = ''

    cn = _pad4(computer_name)
    un = _pad4(user_name)

    p1 = _get_dword(cn)  # computerName dword
    p2 = _get_dword(un)  # userName dword

    aB = initB1(p1, p2)

    key_parts = []
    for i in range(4):
        w = _compute_key_word(name[i], aB)
        key_parts.append(w)

    serial = '{:04X}-{:04X}-{:04X}-{:04X}'.format(*key_parts)
    return serial

def verify(name, serial, computer_name=None, user_name=None):
    """
    Verify name/serial pair.
    ASSUMPTION: computer_name and user_name must match the target machine.
    """
    if len(name) != 4:
        return False
    # Check serial format: 4 groups of 4 hex chars separated by '-'
    parts = serial.upper().split('-')
    if len(parts) != 4:
        return False
    for p in parts:
        if len(p) != 4:
            return False
        try:
            int(p, 16)
        except ValueError:
            return False
    expected = keygen(name, computer_name=computer_name, user_name=user_name)
    return serial.upper() == expected.upper()


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
