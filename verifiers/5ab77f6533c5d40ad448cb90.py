import hashlib
import struct

# ---------------------------------------------------------------------------
# Helpers that mirror the assembly-language / C helper routines
# ---------------------------------------------------------------------------

def _length_to_string(val):
    """Convert the (possibly 64-bit) integer to its decimal string representation."""
    return str(val & 0xFFFFFFFFFFFFFFFF)   # keep 64-bit range as in original


def _scramble_string(s):
    """
    ASSUMPTION: The exact scramble algorithm is not given in the writeup.
    The C source calls _ScrambleString(srcbuffer, len, destbuffer) which is
    an external symbol compiled from a separate object (procs.obj).
    We reverse it as a digit-reversal / character-shuffle here, but this is
    a GUESS.
    """
    # ASSUMPTION: scramble = reverse the string
    return s[::-1]


def _compute_checksum(name_bytes):
    """Product of all character values in the name."""
    result = 1
    for b in name_bytes:
        result *= b
    return result


def _compute_hash_input(checksum):
    """
    Mirrors the inline asm in keygen.core.c:
        mov  ecx, checksum
        lea  eax, [ecx*8]        ; eax = checksum * 8
        sub  eax, ecx            ; eax = checksum * 7
        shl  eax, 9              ; eax = checksum * 7 * 512 = checksum * 3584
        add  eax, ecx            ; eax = checksum * 3584 + checksum = checksum * 3585
        lea  edx, [eax+eax*8]   ; edx = eax * 9 = checksum * 32265
        lea  eax, [ecx+edx*8]   ; eax = checksum + edx*8 = checksum + checksum*258120 = checksum*258121
        lea  eax, [eax+eax*2]   ; eax = eax * 3 = checksum * 774363
        shl  eax, 1              ; eax = checksum * 1548726
        xor  eax, 0x12344321
    All arithmetic is 32-bit (mod 2^32).
    """
    ecx = checksum & 0xFFFFFFFF
    eax = (ecx * 8) & 0xFFFFFFFF
    eax = (eax - ecx) & 0xFFFFFFFF          # * 7
    eax = (eax << 9) & 0xFFFFFFFF           # * 7 * 512
    eax = (eax + ecx) & 0xFFFFFFFF          # * 3585
    edx = (eax + eax * 8) & 0xFFFFFFFF      # * 9  => eax*9
    eax = (ecx + edx * 8) & 0xFFFFFFFF      # ecx + edx*8
    eax = (eax + eax * 2) & 0xFFFFFFFF      # * 3
    eax = (eax << 1) & 0xFFFFFFFF           # * 2
    eax = (eax ^ 0x12344321) & 0xFFFFFFFF
    return eax


def _md5_4bytes(value_32):
    """MD5 of the 4-byte little-endian representation of value_32."""
    data = struct.pack('<I', value_32)
    return hashlib.md5(data).digest()   # 16 bytes


# ---------------------------------------------------------------------------
# RSA-64 parameters from the keygen source
# ---------------------------------------------------------------------------
# n and e are 64-bit hex values
RSA_N = 0xD1D17744CA3D0C09
RSA_E = 0xB54341B5A81ED9CF


def _rsa64_encrypt(value, e=RSA_E, n=RSA_N):
    """Compute value^e mod n (RSA public-key operation, 64-bit modulus)."""
    return pow(value, e, n)


def _bytes_to_big_hex(digest_bytes):
    """Convert MD5 digest (16 bytes) to a hex string, as MIRACL cotstr would."""
    return digest_bytes.hex().upper()


def _int_to_base60_str(value):
    """
    ASSUMPTION: MIRACL with IOBASE=60 produces a base-60 digit string.
    Base-60 digits are typically '0'-'9' then 'A'-'Z' then extra chars.
    We use uppercase alphanumeric here as an approximation.
    The exact digit alphabet for MIRACL base-60 is not documented in the writeup.
    """
    # ASSUMPTION: digit set is '0'-'9','A'-'Z','a'-'x' (60 chars)
    digits = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwx'
    if value == 0:
        return '0'
    result = []
    while value > 0:
        result.append(digits[value % 60])
        value //= 60
    return ''.join(reversed(result))


# ---------------------------------------------------------------------------
# 4-character segment derived from first 4 bytes of name
# ---------------------------------------------------------------------------
def _compute_name_segment(name_bytes):
    """
    From keygen.core.c:
        for (i=0;i<4;i++){
            bfSerial2[i]=(((szName[i]^5)*0xFE) & 9) + 0x30;
        }
    """
    result = []
    for i in range(4):
        b = name_bytes[i] if i < len(name_bytes) else 0
        val = (((b ^ 5) * 0xFE) & 9) + 0x30
        result.append(chr(val & 0xFF))
    return ''.join(result)


# ---------------------------------------------------------------------------
# Main keygen / verify
# ---------------------------------------------------------------------------

def keygen(name):
    """
    Generate a serial for the given name string, following keygen.core.c.

    Serial layout (concatenation):
        [scrambled_length_str][name_segment][md5_hex_of_hash_input][base60_rsa_of_checksum]-[base60_rsa_of_checksum...]

    ASSUMPTION: The exact serial format boundaries / separators are inferred
    from the source; the scramble function internals are unknown.
    """
    if len(name) < 5:
        raise ValueError("Name must be at least 5 characters")

    name_bytes = [ord(c) for c in name]

    # Step 1: modified length (length^6, 64-bit arithmetic)
    dtLength = len(name)
    dtLength = dtLength * dtLength * dtLength   # length^3
    dtLength = dtLength * dtLength              # (length^3)^2 = length^6
    # Keep in 64-bit range as the crackme uses __int64
    dtLength &= 0xFFFFFFFFFFFFFFFF

    # Step 2: convert to string and scramble
    len_str = _length_to_string(dtLength)
    scrambled = _scramble_string(len_str)
    serial = scrambled

    # Step 3: 4-char name segment
    name_seg = _compute_name_segment(name_bytes)
    serial += name_seg

    # Step 4: checksum = product of all character values
    checksum = _compute_checksum(name_bytes)
    checksum &= 0xFFFFFFFF   # 32-bit

    # Step 5: compute the 32-bit value to hash
    hash_input = _compute_hash_input(checksum)

    # Step 6: MD5 of the 4-byte hash_input
    md5_digest = _md5_4bytes(hash_input)

    # Step 7: append MD5 as hex (MIRACL cotstr in base-16)
    md5_hex = _bytes_to_big_hex(md5_digest)
    serial += md5_hex

    # Step 8: RSA-encrypt checksum, append in base-60
    # ASSUMPTION: checksum is taken as a positive integer, then powmod(M,e,n)
    checksum_rsa = _rsa64_encrypt(checksum)
    serial += "-"
    serial += _int_to_base60_str(checksum_rsa)

    return serial


def verify(name, serial):
    """
    Verify a (name, serial) pair by regenerating the serial and comparing.

    ASSUMPTION: Since the scramble function is unknown, verification is
    implemented by checking that the provided serial matches the generated one.
    This will only work correctly once _scramble_string is properly implemented.
    """
    if len(name) < 5:
        return False
    try:
        expected = keygen(name)
        return serial == expected
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Quick smoke-test
# ---------------------------------------------------------------------------

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
