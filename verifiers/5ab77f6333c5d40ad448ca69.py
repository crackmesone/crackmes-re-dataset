# Reverse-engineered key validation for 'puzzle' crackme by mindless
# Based on partial writeup information. The crackme uses:
#   - Multi-threaded architecture with events
#   - Runtime-decrypted functions (custom XOR + Rijndael/AES 128-bit CFB8 mode)
#   - A 'little keygenme algo' described as very weak
#
# The solution writeup (solution.txt) mentions AES 128-bit CFB8 mode and a keygen.exe
# The encrypt.cpp file appears to be garbled (wrong encoding), but we can extract some constants.
# The writeup mentions patching offset 0x40213F and that the algo is 'very weak'.
#
# ASSUMPTION: Based on the garbled encrypt.cpp and solution.txt, the algorithm:
#   1. Takes the username
#   2. Applies some transformation (likely sum/hash of character values)
#   3. The serial is compared against a computed value
#
# The solution.txt references AES CFB8 mode with a key derived from some constants.
# Without a clean copy of encrypt.cpp or the binary, we cannot fully reconstruct.
#
# From the garbled encrypt.cpp we can partially see:
#   - An S-box or key schedule table with bytes like 0x55, 0x8B, 0xEC, 0x83, ...
#   - key[0] = 0x453C62AB (or similar 32-bit constant)
#   - key[1] = 0x0EE93412DE
#   - key[2] = 0x69707321
#   - key[3] = 0x0ACAB2424A  
#   - AES context setup: aes_setkey_enc(&ctx, (unsigned char*)key, 128)
#   - aes_crypt_cfb(&ctx, AES_ENCRYPT, 104, &iv_off, IV, (unsigned char*)fbytes, result)
#   - fbytes[64] = 0xEB  // modify JE to JMP
#
# ASSUMPTION: The key schedule and IV are hardcoded constants in the binary.
# ASSUMPTION: The username is processed through some simple arithmetic to produce
#             a numeric serial that is then verified.
#
# From the TUTORIAL.txt (ForFun solution), the algorithm involves:
#   - Reading username and password
#   - Spawning threads that communicate via events
#   - One main verification thread at 0x4023C7
#   - atoi() is called on the password (serial is numeric)
#   - memcmp() is used for final comparison

def _username_hash(name):
    """Simple hash of username bytes - ASSUMPTION: this is the core of the 'very weak' algo"""
    # ASSUMPTION: sum of ASCII values with some mixing
    val = 0
    for i, c in enumerate(name):
        val += ord(c) * (i + 1)
    return val

def _username_hash_v2(name):
    """Alternative: XOR-based hash - ASSUMPTION"""
    val = 0
    for c in name:
        val = ((val << 5) ^ ord(c)) & 0xFFFFFFFF
    return val

def verify(name: str, serial: str) -> bool:
    """
    Attempt to verify name/serial pair.
    
    ASSUMPTION: The serial is a decimal number (atoi is called on it)
    ASSUMPTION: The serial is derived from a simple hash of the username
    
    The actual algorithm uses AES-128-CFB8 to decrypt verification code at runtime,
    but the underlying check is described as 'very weak' and likely just arithmetic
    on username characters.
    
    Without a clean copy of the binary or encrypt.cpp, this is a best-effort reconstruction.
    """
    try:
        serial_num = int(serial.strip())
    except ValueError:
        return False
    
    # ASSUMPTION: primary check - sum-based
    expected_v1 = _username_hash(name.strip())
    if serial_num == expected_v1:
        return True
    
    # ASSUMPTION: secondary check - xor-based  
    expected_v2 = _username_hash_v2(name.strip())
    if serial_num == expected_v2:
        return True
    
    # ASSUMPTION: simple sum of chars
    simple_sum = sum(ord(c) for c in name.strip())
    if serial_num == simple_sum:
        return True
    
    return False

def keygen(name: str) -> str:
    """
    Generate a serial for the given username.
    
    ASSUMPTION: Returns the sum-based hash as the serial.
    This is highly speculative without the actual binary analysis.
    """
    # ASSUMPTION: primary algorithm
    return str(_username_hash(name.strip()))


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
