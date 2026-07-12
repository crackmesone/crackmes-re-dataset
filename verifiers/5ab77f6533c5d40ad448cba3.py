# Reconstruction of j!m_key1 serial validation algorithm
# Based on multiple solution writeups

# The lookup table for name encryption
# Characters: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz'
INAME = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz'

ITABLE = [
    0x13, 0x14, 0x15, 0x16,
    0x17, 0x18, 0x25, 0x26,
    0x27, 0x28, 0x29, 0x2A,
    0x2B, 0x2C, 0x2D, 0x2E,
    0x2F, 0x35, 0x38, 0x39,
    0x3A, 0x3B, 0x3C, 0x3E,
    0x3F, 0x47, 0x4A, 0x4B,
    0x4C, 0x4E, 0x4F, 0x59,
    0x5C, 0x5E, 0x5F, 0x6A,
    0x6B, 0x6F, 0x7C, 0x7D,
    0x8E, 0x8F, 0x9F, 0x13,
    0x14, 0x15, 0x16, 0x17,
    0x18, 0x25, 0x26, 0x27,
    0x28
]


def encrypt_name(name):
    """Encrypt the name using the lookup table."""
    result = []
    for ch in name:
        pos = INAME.find(ch)
        if pos == -1:
            return None  # Invalid character
        result.append(ITABLE[pos])
    return result


def check_triplet(enc_byte, d1, d2, d3):
    """
    Check if a triplet of serial digits satisfies the equation for an encrypted name byte.
    d1, d2, d3 are the raw digit values (0-9) after subtracting 0x30 from serial chars.

    Assembly trace:
      esi = enc_byte (signed)
      edx = d1  (serial[i*3+0] - 0x30)
      eax = d2  (serial[i*3+1] - 0x30)
      ecx = d3  (serial[i*3+2] - 0x30)

      edi = eax         ; d2
      edi = edi + edi   ; 2*d2
      edi = edi + edi*4 ; 10*d2
      eax = edi         ; A = 10*d2
      eax = eax + ecx  ; A = 10*d2 + d3
      ecx = edx        ; B = d1
      edx = edx + eax  ; edx = d1 + 10*d2 + d3
      eax = eax * ecx  ; eax = (10*d2 + d3) * d1

      ecx = esi & 0x0F          ; low nibble of enc_byte
      ecx = ecx * edx           ; ecx = (enc_byte & 0x0F) * (d1 + 10*d2 + d3)
      edx = ecx                 ; edx = above

      esi = esi >> 4 (arithmetic), then & 0x0F  ; high nibble
      esi = esi * eax           ; esi = high_nibble * (10*d2 + d3) * d1
      eax = esi

      cmp eax, edx  --> must be equal
      test eax, eax --> must be non-zero
    """
    A = 10 * d2 + d3          # 10*d2 + d3
    edx_val = d1 + A          # d1 + 10*d2 + d3
    eax_product = A * d1      # (10*d2 + d3) * d1

    low_nibble = enc_byte & 0x0F
    lhs = low_nibble * edx_val   # (enc & 0xF) * (d1 + 10*d2 + d3)

    # Arithmetic right shift by 4, then mask low nibble
    # For a signed byte value:
    high_nibble = (enc_byte >> 4) & 0x0F
    rhs = high_nibble * eax_product  # ((enc >> 4) & 0xF) * (10*d2+d3)*d1

    return (lhs == rhs) and (lhs != 0)


def verify(name, serial):
    """
    Verify a name/serial pair.
    Returns True if valid.
    """
    # Validate name: only letters and spaces
    for ch in name:
        if ch not in INAME:
            return False

    ln = len(name)
    if ln < 1:
        return False

    # Serial length must be 3 * len(name)
    if len(serial) != 3 * ln:
        return False

    # Encrypt name
    enc = encrypt_name(name)
    if enc is None:
        return False

    # Check each triplet
    for i in range(ln):
        enc_byte = enc[i]
        s0 = serial[i * 3 + 0]
        s1 = serial[i * 3 + 1]
        s2 = serial[i * 3 + 2]

        # Serial chars are digits 0x30-0x39 (ASCII '0'-'9' and up)
        # The program subtracts 0x30 from each serial character
        # ASSUMPTION: Serial characters can be any printable ASCII,
        # but the solver uses digits 0-9 meaning values 0x30-0x39
        d1 = ord(s0) - 0x30
        d2 = ord(s1) - 0x30
        d3 = ord(s2) - 0x30

        if not check_triplet(enc_byte, d1, d2, d3):
            return False

    return True


def keygen(name):
    """
    Generate a valid serial for the given name.
    Uses brute force over digit values 0-9 for each triplet.
    Returns serial string or None if no solution found.
    """
    # Validate name
    for ch in name:
        if ch not in INAME:
            return None

    ln = len(name)
    if ln < 1:
        return None

    # Cap at 14 characters (max serial check loop is up to name length)
    # ASSUMPTION: The crackme caps the name used at 14 chars based on SOLU.PAS
    effective_name = name[:14] if ln > 14 else name
    enc = encrypt_name(effective_name)
    if enc is None:
        return None

    serial_parts = []
    for i, enc_byte in enumerate(enc):
        found = False
        # Brute force d1, d2, d3 in range 0-9
        for d2 in range(9, -1, -1):
            for d1 in range(9, -1, -1):
                for d3 in range(9, -1, -1):
                    if check_triplet(enc_byte, d1, d2, d3):
                        serial_parts.append(
                            chr(d1 + 0x30) + chr(d2 + 0x30) + chr(d3 + 0x30)
                        )
                        found = True
                        break
                if found:
                    break
            if found:
                break
        if not found:
            return None

    return ''.join(serial_parts)



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
