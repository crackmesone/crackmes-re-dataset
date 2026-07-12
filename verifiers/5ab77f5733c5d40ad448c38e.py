import hashlib
import struct

# ASSUMPTION: The full serial construction algorithm involves MD5 of name,
# XOR with 'High Proof Cosmic Milk' (first 16 bytes), then complex table
# manipulations and FPU squaring. Only partial algorithm is reconstructible
# from the writeup. The writeup describes but does not fully detail the
# table construction and serial derivation steps.

HIGH_PROOF = b'High Proof Cosmic Milk'

def md5_of_name(name: str) -> bytes:
    """Compute MD5 hash of the name string."""
    return hashlib.md5(name.encode('latin-1')).digest()  # 16 bytes

def xor_with_high_proof(hash_buf: bytearray) -> bytearray:
    """
    XOR first 16 bytes of hash buffer with 'High Proof Cosmic Milk'.
    Loop runs 0x10 (16) times.
    From writeup:
      ecx = 0x10
      XOR BYTE PTR DS:[EBX+ESI], AL  ; XOR MD5[i] with HIGH_PROOF[i] for i in 0..15
    """
    result = bytearray(hash_buf)
    for i in range(0x10):
        result[i] ^= HIGH_PROOF[i]
    return result

def get_magic_value(name: str) -> int:
    """
    After MD5 and XOR, there is FPU work:
      PUSH ECX
      FILD DWORD PTR SS:[ESP]   ; load integer into FPU
      POP ECX
      FLD ST                    ; duplicate
      FMULP ST(1),ST            ; square it
      FISTP QWORD PTR DS:[402831] ; store as 64-bit int

    ASSUMPTION: ECX at the PUSH ECX point contains some derived value
    from the XOR'd hash buffer. We assume it's the first 4 bytes of
    the XOR'd buffer interpreted as a little-endian 32-bit integer.
    The magic value = ecx * ecx (squared).
    """
    md5_buf = bytearray(md5_of_name(name))
    xored = xor_with_high_proof(md5_buf)
    # ASSUMPTION: ECX is derived from first 4 bytes of xored buffer
    ecx = struct.unpack_from('<I', bytes(xored[:4]))[0]
    magic = ecx * ecx  # FPU square: FMULP ST(1),ST
    return magic

def verify(name: str, serial: str) -> bool:
    """
    Known checks from writeup:
    1. Serial must be exactly 35 characters long.
    2. Name is MD5 hashed.
    3. MD5 hash XORed with 'High Proof Cosmic Milk' (first 16 bytes).
    4. FPU squaring of some derived value -> magic qword stored at [402831].
    5. Final check: FCOMPP compares two FPU values; must be equal.

    ASSUMPTION: The serial encodes the magic value somehow.
    The exact encoding of the serial from the magic value is NOT described
    in the writeup (author says 'see keygen code for details' but the keygen
    asm is truncated). We implement what we can verify:
    - Length check
    - ASSUMPTION: The serial (as ASCII digits or hex) encodes the magic
      64-bit squared value in some subset of the 35 characters.
    
    Without the full keygen assembly, we cannot implement the real serial
    encoding. We return True only if length is 35 AND the magic-derived
    portion matches. Since we can't determine the encoding, this is partial.
    """
    if len(serial) != 35:
        return False
    
    magic = get_magic_value(name)
    
    # ASSUMPTION: We cannot reconstruct the full table-based serial encoding.
    # A real verify would decode the serial back to the magic value and compare.
    # Placeholder: always return False if we can't verify the magic.
    # This signals the algorithm is only partially recovered.
    _ = magic  # used in real check
    
    # ASSUMPTION: Cannot implement full check without complete assembly listing
    raise NotImplementedError(
        "Full serial encoding algorithm not recoverable from writeup. "
        "Length check passes (35 chars), but serial <-> magic mapping is unknown."
    )

def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.

    From the writeup:
    1. MD5 the name.
    2. XOR first 16 bytes with 'High Proof Cosmic Milk'.
    3. Derive ECX from xored buffer (ASSUMPTION: first 4 bytes as uint32).
    4. Compute magic = ecx^2 as 64-bit integer.
    5. Construct 35-char serial from magic.

    ASSUMPTION: Serial construction from magic value uses table manipulations
    described as 'Seed', 'RAND', 'CreateBig', 'MessUpBigTable', 'Fix6a', 'Do6a'
    in the keygen source. Since the full assembly is truncated, we cannot
    reconstruct exact encoding. We return a placeholder of correct length.
    """
    magic = get_magic_value(name)
    
    # ASSUMPTION: The magic value is somehow encoded into the 35-char serial.
    # The keygen uses random seeds and table manipulations not fully shown.
    # As a best-effort placeholder: encode magic as hex (16 chars) + padding.
    magic_hex = format(magic & 0xFFFFFFFFFFFFFFFF, '016X')
    
    # ASSUMPTION: Pad to 35 chars with zeros (real padding/encoding unknown)
    serial = magic_hex + '0' * (35 - len(magic_hex))
    serial = serial[:35]  # ensure exactly 35 chars
    
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
