import hashlib
import struct

# ============================================================
# qpt^J's KeyGenMe 1  -  verify / keygen
# Based on the two write-ups (KernelJ + alex_ls)
# ============================================================
#
# Serial format:  <7-digit decimal>-<hex string>
#
# Part 1 (7 digits):
#   decimal_number XOR 0x5050  ==  address_of_good_boy_code
#   The good-boy address found by KernelJ is 0x4018AD (creates
#   an infinite loop but is the only referenced "success" path
#   visible in the write-up).  alex_ls gives 4210535 as the
#   correct first part, which corresponds to:
#   4210535 XOR 0x5050 == 0x404517  (approx; see note below)
#   We use the value from alex_ls directly: 4210535
#
# Part 2 (hex string):
#   - Name is upper-cased
#   - SHA-1 of a fixed 0x40-byte buffer of code at 0x00401030
#     (digest is constant regardless of name):
#       DIGEST = 705693D58259B1FD1259DB0CC62A6ABCC518E9AC
#   - A key-buffer is built by concatenating:
#       UPPERCASE_NAME
#       + SHA1_KEY1 (= first 4 bytes of digest as hex)
#       + SHA1_KEY3
#       + SHA1_KEY2
#       + SHA1_KEY5
#       + SHA1_KEY4
#       + constant_string ("wmsdbklfdhajpishgovmboaeyrjl;amjkl;afbl...")
#       + ... (20 lstrcatA calls total, most are filler/fake)
#   - First 0x40 bytes of that buffer are run through a
#     block-cipher at 0x0402B0B (unknown; ripped by alex_ls)
#   - First 0x20 bytes of the result become part 2
#   - Each DWORD (except 2nd, 4th, 6th, 8th) is XOR-ed with
#     0x12345678 and converted to uppercase hex chars
#
# ASSUMPTION: The block cipher at 0x0402B0B is not described in
#   detail in any write-up.  We cannot implement it from the
#   available text.  The keygen below implements everything
#   that IS described and marks the cipher as a stub.
#
# ASSUMPTION: The exact 20 lstrcatA strings and their order are
#   only partially given.  We use what is shown.
#
# ASSUMPTION: The SHA-1 keys (SHA1_KEY1..5) are the five 4-byte
#   chunks of the constant digest split into hex strings.
# ============================================================

# --- Constants derived from write-up ---

# Constant SHA-1 digest of 0x40 bytes of code at 0x00401030
# (does NOT depend on the user name)
SHA1_DIGEST_HEX = "705693D58259B1FD1259DB0CC62A6ABCC518E9AC"

# Split into 5 x 8-hex-char keys (4 bytes each)
_dwords = [SHA1_DIGEST_HEX[i*8:(i+1)*8] for i in range(5)]
SHA1_KEY1 = _dwords[0]  # 705693D5
SHA1_KEY2 = _dwords[1]  # 8259B1FD
SHA1_KEY3 = _dwords[2]  # 1259DB0C
SHA1_KEY4 = _dwords[3]  # C62A6ABC
SHA1_KEY5 = _dwords[4]  # C518E9AC

# Constant string appended (first fragment shown in write-up)
CONSTANT_STR = "wmsdbklfdhajpishgovmboaeyrjl;amjkl;afbl"

# Good-boy first-part value (from alex_ls write-up)
FIRST_PART = "4210535"


def _build_key_buffer(name: str) -> bytes:
    """
    Build the 0x40-byte key buffer that is fed to the block cipher.
    Order of concatenation (from write-up, only 20 of many lstrcatA
    are significant):
      UPPERCASE_NAME + KEY1 + KEY3 + KEY2 + KEY5 + KEY4 + CONSTANT
    We pad / truncate to 0x40 bytes.
    ASSUMPTION: remaining lstrcatA calls use zero/filler bytes.
    """
    buf = name.upper()
    buf += SHA1_KEY1
    buf += SHA1_KEY3
    buf += SHA1_KEY2
    buf += SHA1_KEY5
    buf += SHA1_KEY4
    buf += CONSTANT_STR
    # Encode to bytes, pad/truncate to 0x40
    raw = buf.encode('ascii', errors='replace')
    raw = raw[:0x40].ljust(0x40, b'\x00')
    return raw


def _block_cipher_stub(data: bytes) -> bytes:
    """
    ASSUMPTION: The actual block cipher at 0x0402B0B is not described
    in the write-up (alex_ls says 'i just ripped some code').  This
    function is a stub that returns the input unchanged.
    Replace with the real cipher if/when it is reverse-engineered.
    """
    # ASSUMPTION: identity function — real cipher unknown
    return data


def _encode_second_part(cipher_out: bytes) -> str:
    """
    From alex_ls:
      'Every double word of a key is xored by 12345678h and converted
       to chars except 2nd, 4th, 6th, 8th dword.'
    We process the first 0x20 (32) bytes = 8 DWORDs.
    DWORDs are indexed 1-based: 1,3,5,7 are XOR-ed; 2,4,6,8 are not.
    Each DWORD is formatted as 8 uppercase hex chars.
    ASSUMPTION: 'except' means those DWORDs are output as-is (no XOR).
    """
    result = ""
    for i in range(8):
        dw = struct.unpack_from('<I', cipher_out, i * 4)[0]
        one_based = i + 1
        if one_based not in (2, 4, 6, 8):  # XOR these
            dw ^= 0x12345678
        result += format(dw, '08X')
    return result


def _compute_second_part(name: str) -> str:
    key_buf = _build_key_buffer(name)
    # Run through (unknown) block cipher
    cipher_out = _block_cipher_stub(key_buf)
    # Take first 0x20 bytes
    cipher_out = cipher_out[:0x20].ljust(0x20, b'\x00')
    return _encode_second_part(cipher_out)


def verify(name: str, serial: str) -> bool:
    """
    Verify a name/serial pair.
    Serial format: '<7-digit decimal>-<hex string>'
    """
    if '-' not in serial:
        return False
    dash_idx = serial.index('-')
    part1 = serial[:dash_idx]
    part2 = serial[dash_idx + 1:]

    # --- Check part 1 ---
    # Must be numeric, at least 7 chars (serial total > 10 chars)
    if not part1.isdigit():
        return False
    # The XOR with 0x5050 must yield a valid code address (not checked
    # here beyond being non-zero).
    # ASSUMPTION: we only verify it matches the expected constant.
    if part1 != FIRST_PART:
        return False

    # --- Check part 2 ---
    expected_part2 = _compute_second_part(name)
    # ASSUMPTION: because the block cipher is a stub, this comparison
    # will only be meaningful when the real cipher is plugged in.
    return part2.upper() == expected_part2.upper()


def keygen(name: str) -> str:
    """
    Generate a serial for the given name.
    ASSUMPTION: Part 2 is only correct when the real block cipher
    is implemented in _block_cipher_stub.
    """
    part2 = _compute_second_part(name)
    return f"{FIRST_PART}-{part2}"



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
