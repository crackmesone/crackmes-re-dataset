# Reverse-engineered algorithm for Defender crackme by eldad_eilam
# Based on ZaiRoN's writeup
#
# Key facts from the writeup:
# 1. Name: only A-Z, a-z, space characters
# 2. Serial: exactly 16 hex chars (0-9, A-F)
# 3. Serial is split into two 8-char halves => two DWORDs: serial_1 (first 8), serial_2 (last 8)
# 4. A value 'valName' is computed over the name characters
# 5. fixed_dword = (valName * volumeNumber) - serial_2
# 6. The fixed_dword is used as a decryption key for a code block
# 7. The crackme is MACHINE DEPENDENT (uses volume serial number)
#
# The writeup does NOT fully describe:
#   - The exact algorithm to compute valName from the name
#   - What constitutes a 'correct' decryption (the check at 401D50)
#   - How serial_1 is validated
#   - The exact decryption loop details for the protected block
#
# ASSUMPTION: valName is computed by some accumulation over name character ordinals
# ASSUMPTION: The decryption scheme is: newDword = fixed_dword ^ Dword(cur) ^ Dword(cur-4)
# ASSUMPTION: A correct decryption is verified by a sentinel value / jump at end of decrypted block
# ASSUMPTION: serial_2 is interpreted as a little-endian 32-bit integer from the last 8 hex chars
# ASSUMPTION: serial_1 usage is not described; it may be part of a separate check not detailed in writeup

import struct
import ctypes
import sys

def compute_val_name(name: str) -> int:
    """
    ASSUMPTION: The exact valName algorithm is not described in the writeup.
    ZaiRoN says 'some simple operations over the name' between 402AC7 and 402B51.
    A common pattern is a running hash; we implement a placeholder.
    Without reversing the binary this cannot be determined from the writeup alone.
    """
    # ASSUMPTION: simple additive/multiplicative hash over character values
    val = 0
    for ch in name:
        # ASSUMPTION: typical rol/accumulate pattern
        val = ((val * 0x21) + ord(ch)) & 0xFFFFFFFF
    return val

def get_volume_serial() -> int:
    """
    Returns the volume serial number of the C: drive (Windows only).
    On non-Windows systems returns 0 (keygen will not produce correct serials).
    """
    try:
        import ctypes
        vsn = ctypes.c_ulong(0)
        ctypes.windll.kernel32.GetVolumeInformationW(
            'C:\\\\', None, 0, ctypes.byref(vsn), None, None, None, 0
        )
        return vsn.value
    except Exception:
        # ASSUMPTION: return 0 if not on Windows / cannot determine
        return 0

def serial_to_dwords(serial: str):
    """
    Convert a 16-character hex serial into two 32-bit integers.
    serial_1 = first 8 hex chars (big-endian integer)
    serial_2 = last 8 hex chars (big-endian integer)
    """
    s = serial.upper()
    serial_1 = int(s[0:8], 16)
    serial_2 = int(s[8:16], 16)
    return serial_1, serial_2

def validate_name(name: str) -> bool:
    """Name must contain only A-Z, a-z, or space."""
    for ch in name:
        if not (ch.isalpha() or ch == ' '):
            return False
    return len(name) > 0

def validate_serial_format(serial: str) -> bool:
    """Serial must be exactly 16 characters, each 0-9 or A-F."""
    if len(serial) != 16:
        return False
    for ch in serial.upper():
        if ch not in '0123456789ABCDEF':
            return False
    return True

# Encrypted block from 401E32 to 401EB6 (size ~ 0x84 bytes = 33 dwords)
# ASSUMPTION: We cannot reconstruct the actual encrypted bytes without the binary.
# The decryption check would verify that the decrypted block ends with a specific
# jump instruction back to the encrypt/decrypt dispatcher.
ENCRYPTED_BLOCK = None  # ASSUMPTION: binary data not available from writeup

def decrypt_block(encrypted_bytes: bytes, fixed_dword: int) -> bytes:
    """
    Decryption scheme from writeup:
    newDword = fixed_dword ^ Dword(curAddress) ^ Dword(curAddress-4)
    
    'Dword(curAddress-4)' is the ORIGINAL dword before modification (prev_dword starts at 0).
    """
    result = bytearray(encrypted_bytes)
    prev_dword = 0
    for i in range(0, len(encrypted_bytes) - 3, 4):
        cur_dword = struct.unpack_from('<I', encrypted_bytes, i)[0]
        new_dword = (fixed_dword ^ cur_dword ^ prev_dword) & 0xFFFFFFFF
        struct.pack_into('<I', result, i, new_dword)
        prev_dword = cur_dword  # use original value
    return bytes(result)

def check_decrypted_block_valid(decrypted: bytes) -> bool:
    """
    ASSUMPTION: A correctly decrypted block ends with a JMP instruction
    back to the encrypt/decrypt dispatcher (as described in writeup).
    We check for a near JMP opcode (0xE9) near the end of the block.
    Without the binary, we cannot verify the exact expected bytes.
    """
    # ASSUMPTION: last instruction is E9 xx xx xx xx (near jmp)
    if len(decrypted) >= 5:
        return decrypted[-5] == 0xE9
    return False

def verify(name: str, serial: str, volume_number: int = None) -> bool:
    """
    Verify name/serial pair.
    NOTE: This crackme is machine-dependent (uses volume serial number).
    Provide volume_number explicitly or it will be read from the system.
    """
    # Format checks
    if not validate_name(name):
        return False
    if not validate_serial_format(serial):
        return False
    
    serial_1, serial_2 = serial_to_dwords(serial)
    
    if volume_number is None:
        volume_number = get_volume_serial()
    
    val_name = compute_val_name(name)
    
    # fixed_dword = (valName * volumeNumber) - serial_2  (mod 2^32)
    fixed_dword = (val_name * volume_number - serial_2) & 0xFFFFFFFF
    
    # ASSUMPTION: Without the actual encrypted block bytes we cannot
    # perform the real decryption check. The real check would decrypt
    # bytes at 401E32..401EB6 and verify the result is valid code.
    if ENCRYPTED_BLOCK is None:
        # Cannot verify without binary data
        # ASSUMPTION: return True only for format compliance as fallback
        print("[!] Cannot perform real check: encrypted block bytes not available")
        print(f"    val_name     = 0x{val_name:08X}")
        print(f"    volume_num   = 0x{volume_number:08X}")
        print(f"    serial_2     = 0x{serial_2:08X}")
        print(f"    fixed_dword  = 0x{fixed_dword:08X}")
        return False
    
    decrypted = decrypt_block(ENCRYPTED_BLOCK, fixed_dword)
    return check_decrypted_block_valid(decrypted)

def keygen(name: str, volume_number: int = None) -> str:
    """
    Generate a valid serial for the given name.
    
    From the writeup:
      fixed_dword = (valName * volumeNumber) - serial_2  (mod 2^32)
    
    For a correct serial, the decrypted block must contain valid code
    ending with a JMP. Since we don't have the encrypted block, we
    demonstrate the relationship:
    
      serial_2 = (valName * volumeNumber - desired_fixed_dword) mod 2^32
    
    ASSUMPTION: desired_fixed_dword is the one that correctly decrypts
    the block -- we cannot determine it without the binary.
    
    ASSUMPTION: serial_1 (first 8 hex chars) may be arbitrary or have
    a separate constraint not described in the writeup.
    """
    if not validate_name(name):
        raise ValueError(f"Invalid name: {name!r}")
    
    if volume_number is None:
        volume_number = get_volume_serial()
    
    val_name = compute_val_name(name)
    
    # ASSUMPTION: desired_fixed_dword must be determined from the binary.
    # Without it, we cannot produce correct serial_2.
    # Placeholder: we set serial_2 such that fixed_dword = 0
    # (almost certainly wrong without the binary)
    # serial_2 = (valName * volumeNumber) mod 2^32  when fixed_dword=0
    # ASSUMPTION: this is just a structural demonstration
    desired_fixed_dword = 0  # ASSUMPTION: unknown without binary
    
    serial_2 = (val_name * volume_number - desired_fixed_dword) & 0xFFFFFFFF
    serial_1 = 0x00000000  # ASSUMPTION: unknown constraint on serial_1
    
    serial = f"{serial_1:08X}{serial_2:08X}"
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
