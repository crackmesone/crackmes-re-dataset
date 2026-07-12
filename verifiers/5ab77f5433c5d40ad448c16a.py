# E2 (NTT) block cipher - partial reconstruction from MASM source
# The writeup shows a full E2 cipher implementation in MASM assembly.
# The crackme uses E2 encryption/decryption to validate name/serial.
# However, the EXACT check condition (what plaintext, what key, what comparison)
# is NOT shown in the truncated writeup. Only the cipher primitives are provided.
#
# ASSUMPTION: The crackme uses the name as the key and encrypts a fixed plaintext,
# then compares the result to the serial (or vice versa).
# Without the actual crackme binary logic showing the comparison, we cannot
# implement a correct verify() or keygen().

# Below is a best-effort Python implementation of the E2 cipher core
# based on the MASM source provided, with the verify/keygen stubs.

E2_SBOX = [
    0xe1,0x42,0x3e,0x81,0x4e,0x17,0x9e,0xfd,0xb4,0x3f,0x2c,0xda,0x31,0x1e,0xe0,0x41,
    0xcc,0xf3,0x82,0x7d,0x7c,0x12,0x8e,0xbb,0xe4,0x58,0x15,0xd5,0x6f,0xe9,0x4c,0x4b,
    0x35,0x7b,0x5a,0x9a,0x90,0x45,0xbc,0xf8,0x79,0xd6,0x1b,0x88,0x02,0xab,0xcf,0x64,
    0x09,0x0c,0xf0,0x01,0xa4,0xb0,0xf6,0x93,0x43,0x63,0x86,0xdc,0x11,0xa5,0x83,0x8b,
    0xc9,0xd0,0x19,0x95,0x6a,0xa1,0x5c,0x24,0x6e,0x50,0x21,0x80,0x2f,0xe7,0x53,0x0f,
    0x91,0x22,0x04,0xed,0xa6,0x48,0x49,0x67,0xec,0xf7,0xc0,0x39,0xce,0xf2,0x2d,0xbe,
    0x5d,0x1c,0xe3,0x87,0x07,0x0d,0x7a,0xf4,0xfb,0x32,0xf5,0x8c,0xdb,0x8f,0x25,0x96,
    0xa8,0xea,0xcd,0x33,0x65,0x54,0x06,0x8d,0x89,0x0a,0x5e,0xd9,0x16,0x0e,0x71,0x6c,
    0x0b,0xff,0x60,0xd2,0x2e,0xd3,0xc8,0x55,0xc2,0x23,0xb7,0x74,0xe2,0x9b,0xdf,0x77,
    0x2b,0xb9,0x3c,0x62,0x13,0xe5,0x94,0x34,0xb1,0x27,0x84,0x9f,0xd7,0x51,0x00,0x61,
    0xad,0x85,0x73,0x03,0x08,0x40,0xef,0x68,0xfe,0x97,0x1f,0xde,0xaf,0x66,0xe8,0xb8,
    0xae,0xbd,0xb3,0xeb,0xc6,0x6b,0x47,0xa9,0xd8,0xa7,0x72,0xee,0x1d,0x7e,0xaa,0xb6,
    0x75,0xcb,0xd4,0x30,0x69,0x20,0x7f,0x37,0x5b,0x9d,0x78,0xa3,0xf1,0x76,0xfa,0x05,
    0x3d,0x3a,0x44,0x57,0x3b,0xca,0xc7,0x8a,0x18,0x46,0x9c,0xbf,0xba,0x38,0x56,0x1a,
    0x92,0x4d,0x26,0x29,0xa2,0x98,0x10,0x99,0x70,0xa0,0xc5,0x28,0xc1,0x6d,0x14,0xac,
    0xf9,0x5f,0x4f,0xc4,0xc3,0xd1,0xfc,0xdd,0xb2,0x59,0xe6,0xb5,0x36,0x52,0x4a,0x2a,
]

def _u32(x):
    return x & 0xFFFFFFFF

def _bswap(x):
    return ((x & 0xFF) << 24) | (((x >> 8) & 0xFF) << 16) | (((x >> 16) & 0xFF) << 8) | ((x >> 24) & 0xFF)

def _rol32(x, n):
    n &= 31
    return _u32((x << n) | (x >> (32 - n)))

def _ror32(x, n):
    return _rol32(x, 32 - n)

def _f_function(eax, edx, sbox):
    # Apply sbox to each byte of eax (4 bytes), rotating
    def apply_sbox_word(w):
        result = 0
        for _ in range(4):
            b = w & 0xFF
            b = sbox[b]
            result = (result >> 8) | (b << 24)
            w = _rol32(w, 8) if False else _ror32(w, 8)  # ASSUMPTION: xlatb acts on AL
            # Actually: xlatb substitutes AL via sbox, then rol eax,8 moves next byte to AL
            # Let's redo properly
        return result

    # xlatb substitutes AL (low byte), then rol eax,8 brings next byte to AL position
    def sbox_word(w):
        for i in range(4):
            al = w & 0xFF
            al = sbox[al]
            w = (w & 0xFFFFFF00) | al
            w = _rol32(w, 8)
        return w

    eax = sbox_word(eax)
    edx = sbox_word(edx)

    # xor edx, eax; rol edx, 16; xor eax, edx; rol edx, 16; ror eax, 8; xor edx, eax; rol eax, 8; xor eax, edx
    edx = _u32(edx ^ eax)
    edx = _rol32(edx, 16)
    eax = _u32(eax ^ edx)
    edx = _rol32(edx, 16)
    eax = _ror32(eax, 8)
    edx = _u32(edx ^ eax)
    eax = _rol32(eax, 8)
    eax = _u32(eax ^ edx)
    return eax, edx

def _mod_inv(x):
    # Modular inverse mod 2^32 (used in key schedule)
    # ASSUMPTION: modInv computes multiplicative inverse mod 2^32
    x = _u32(x | 1)  # ensure odd
    # Extended Euclidean for mod 2^32
    # Use the iterative method shown in assembly
    # Simplified: use pow(x, -1, 2**32) in Python 3.8+
    try:
        return pow(int(x), -1, 2**32)
    except Exception:
        return 1

def e2_set_key(password_bytes, key_size=128):
    # ASSUMPTION: password_bytes is bytes of length key_size//8
    sbox = E2_SBOX
    lk = [0] * 8   # e2_tempkey (edi), 8 dwords
    lout = [0] * 8  # e2_subkey (ebp)
    internal_key = [0] * 88  # e2_internalKey

    # Load key
    key_dwords = key_size // 32
    for i in range(key_dwords):
        chunk = password_bytes[i*4:(i+1)*4]
        if len(chunk) < 4:
            chunk = chunk + b'\x00' * (4 - len(chunk))
        val = int.from_bytes(chunk, 'big')  # bswap = big-endian read
        lk[i % 8] = _u32(val)

    if key_size == 128:
        lk[4] = 0x582ED330
        lk[5] = 0x84499EB8
        lk[6] = 0xECCF5709
        lk[7] = 0x2E5000D8
    elif key_size == 192:
        lk[6] = 0xECCF5709
        lk[7] = 0x2E5000D8
    # 256: all 8 dwords from key

    lout[6] = 0x01234567
    lout[7] = 0x89ABCDEF

    # ASSUMPTION: G_function and the key schedule loop are approximated below
    # The full key schedule is complex; this is a partial stub.
    # Full implementation would require careful port of the assembly.

    # Stub: return zeroed internal key (not functional)
    # ASSUMPTION: Cannot fully reconstruct key schedule without running binary
    return internal_key

def verify(name: str, serial: str) -> bool:
    # ASSUMPTION: The crackme encrypts a fixed block with name as key
    # and checks against serial. Exact plaintext and comparison unknown.
    # This is a STUB - cannot verify without the full binary logic.
    #
    # ASSUMPTION: serial is 16 hex bytes (32 hex chars) representing encrypted block
    # ASSUMPTION: name is padded/truncated to 16 bytes as E2 key
    name_bytes = name.encode('ascii', errors='replace')[:16].ljust(16, b'\x00')
    # ASSUMPTION: fixed plaintext block
    # plaintext = b'\x00' * 16
    # Without full E2 encrypt working, we cannot compute the ciphertext.
    # Returning False as stub.
    return False

def keygen(name: str) -> str:
    # ASSUMPTION: keygen would encrypt fixed plaintext with name as key
    # and return hex-encoded ciphertext as serial.
    # Cannot implement without full E2 encrypt.
    raise NotImplementedError("Full E2 key schedule not reconstructed from truncated writeup")


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
