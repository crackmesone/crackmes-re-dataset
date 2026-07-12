import struct
import base64

# We need a CAST-128 (CAST5) implementation.
# Using the 'pycryptodome' library (Crypto.Cipher.CAST).
# pip install pycryptodome

try:
    from Crypto.Cipher import CAST
    PYCRYPTODOME = True
except ImportError:
    PYCRYPTODOME = False

# ASSUMPTION: The CAST-128 key used is derived from data at 0x4052E0 in the original binary.
# The writeup shows a specific encrypted output for 'Guetta':
#   CAST128 encrypt('Guetta') = 9E5D8251CA64B116h
# and for 'DRACULA':
#   CAST128 encrypt('DRACULA') = 6BB3572EA1BA59ADh
# The key is hardcoded in the crackme at address 0x4052E0 (16 bytes).
# We do NOT have the exact key bytes from the writeup.
# We will attempt to recover the key by brute-forcing against the known test vectors.
# Since we can't recover the key from the writeup alone, we mark the key as ASSUMPTION.

# ASSUMPTION: The CAST-128 key is 16 bytes of unknown value embedded in the crackme.
# Without the actual binary we cannot know the key. We note the known pairs:
#   name='Guetta'  -> CAST output = 9E5D8251CA64B116 (8 bytes, big-endian)
#   name='DRACULA' -> CAST output = 6BB3572EA1BA59ADh
# The name is zero-padded or truncated to 8 bytes as CAST block size is 8 bytes.

KNOWN_KEY = None  # Cannot determine without binary

# ASSUMPTION: The name is taken as-is (ASCII), padded with zeros to 8 bytes for CAST-128 block.

def cast128_encrypt_block(data8, key16):
    """Encrypt exactly 8 bytes with CAST-128 using a 16-byte key."""
    if not PYCRYPTODOME:
        raise RuntimeError("pycryptodome is required: pip install pycryptodome")
    cipher = CAST.new(key16, CAST.MODE_ECB)
    return cipher.encrypt(data8)


def custom_base64_encode(data8):
    """Standard base64 encoding of 8 bytes -> 12 char string (with possible padding)."""
    return base64.b64encode(data8).decode('ascii')


def extract_serial(b64_result):
    """Extract every other byte (indices 0,2,4,6,8,10) from base64 result.
    The writeup says: 'print one byte on two of BASE64 result for the serial'.
    Serial must be 6 chars.
    From example: BASE64 = 'nl2CUcpksRY=' -> Serial = 'n2UpsY' (chars at index 0,2,4,6,8,10).
    """
    # Only take chars at even indices
    serial_chars = [b64_result[i] for i in range(0, len(b64_result), 2)]
    # Take first 6
    serial = ''.join(serial_chars[:6])
    return serial


def keygen(name, key16=KNOWN_KEY):
    """
    Generate serial for given name.
    Requires the 16-byte CAST-128 key from the crackme binary.
    
    Algorithm:
    1. Take name as ASCII bytes, use first 8 bytes (zero-pad if shorter)
    2. Encrypt with CAST-128 (ECB mode, 16-byte key) -> 8 bytes
    3. Base64-encode the 8 bytes -> ~12 char string
    4. Take every other character (indices 0,2,4,...) -> serial (6 chars)
    """
    if key16 is None:
        raise ValueError(
            "CAST-128 key is unknown (not in writeup). "
            "You must extract the 16-byte key from the crackme binary at address 0x4052E0."
        )
    
    # Prepare 8-byte block from name
    name_bytes = name.encode('ascii', errors='replace')
    # ASSUMPTION: name is zero-padded to 8 bytes (CAST block size)
    block = (name_bytes + b'\x00' * 8)[:8]
    
    # Step 1: CAST-128 encrypt
    cast_out = cast128_encrypt_block(block, key16)
    
    # Step 2: Base64 encode
    b64 = custom_base64_encode(cast_out)
    
    # Step 3: Extract every other byte
    serial = extract_serial(b64)
    
    return serial


def verify(name, serial, key16=KNOWN_KEY):
    """
    Verify serial for given name.
    Returns True if serial matches the expected value.
    """
    if key16 is None:
        raise ValueError(
            "CAST-128 key is unknown. Extract it from binary at 0x4052E0."
        )
    try:
        expected = keygen(name, key16)
    except Exception:
        return False
    
    # Serial must be at least 6 chars
    if len(serial) < 6:
        return False
    
    # Compare
    return serial == expected


# ---- Verification against known example (assembly-level comparison logic) ----
# The assembly loop at 0x403E9B-0x403EC4 does:
#   for i in 0..5:
#     BL = serial_byte[i]          (from GetDlgItemText overwriting buffer at 0x4052E0)
#     DL = BL + 1                  (INC DL)
#     BH = BL
#     BL = BL - DL                 -> BL = BL - (BL+1) = -1 = 0xFF
#     BL = BL + 1                  -> BL = 0
#     EDX = ZeroExtend(BL) = 0
#     BH = CAST_buffer[EDX + EAX*2 + 0x40527C]  = CAST_buffer[0 + i*2]
#     BL = serial_byte XOR CAST_byte
#     if BL != 0: fail
# Wait, let's re-analyze:
#   BL = serial[i]
#   DL = BL; INC DL -> DL = serial[i]+1
#   BH = BL = serial[i]
#   SUB BL, DL -> BL = serial[i] - (serial[i]+1) = -1 = 0xFF
#   INC BL -> BL = 0
#   EDX = 0
#   BH2 = CAST_buffer[EDX + EAX*2] = CAST_buffer[i*2]  (base64 result stored at 0x40527C? No...)
# ASSUMPTION: There's a buffer confusion in the writeup. 
# The base64 output and CAST output buffers may be swapped in the comparison.
# The net effect: serial[i] XOR cast_output[i*2] == 0
# meaning serial[i] == cast_output_base64[i*2] (every other char of base64)
# This is consistent with the stated algorithm.


def demo():
    print("cryptok_keygenme_1 keygen")
    print("NOTE: CAST-128 key must be extracted from binary at address 0x4052E0")
    print()
    print("Known test vectors from writeup:")
    print("  name='Guetta'  -> CAST128=9E5D8251CA64B116h -> BASE64='nl2CUcpksRY=' -> serial='n2UpsY'")
    print("  name='DRACULA' -> CAST128=6BB3572EA1BA59ADh -> BASE64='a7NX...'     -> serial='aN' (buggy)")
    print()
    print("To use: provide key16 (16 bytes from binary) to keygen(name, key16)")



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
