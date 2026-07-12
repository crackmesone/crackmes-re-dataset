# KeygenMe 0.78 by bswap
# Reconstructed from TiGa's solution writeup
#
# The crackme:
# 1. Reads a Name (min 4 chars, max 16 chars)
# 2. Reads a serial key (displayed as XXXX-XXXX-XXXX hex, 12 hex chars -> 6 bytes)
#    but the serial input field is 16 chars; the ID key shown is XXXX-XXXX-XXXX
# 3. The serial input (16 hex chars) is decoded into 8 bytes -> two DWORDs (Result1, Result2)
#    by treating each pair of hex chars as a byte (little-endian store as DWORDs)
# 4. A loop runs 0x2003 times doing:
#       eax ^= 0x2003
#       eax, ebx = ebx, eax   (xchg)
#       ebx += 1
#       eax = bswap(eax)
#    (with some fake/nop-equivalent instructions on ecx/edx)
# 5. After the loop the result is compared against a value derived from the Name and IDKEY
#    (the exact Name->expected comparison is NOT fully shown in the truncated writeup)
#
# ASSUMPTION: The loop starts with eax=Result1, ebx=Result2, ecx=0, edx=0
# ASSUMPTION: The 'fake' ops on ecx/edx do not affect eax/ebx meaningfully
# ASSUMPTION: The final check compares transformed (eax,ebx) against something computed
#             from the Name string; the exact name hash is NOT shown (writeup truncated)
# ASSUMPTION: The serial input is exactly 16 hex chars (no dashes during input)
# ASSUMPTION: The keygen target is: given Name, find serial such that after the loop
#             eax,ebx match the name-derived expected values (we invert the loop)

import struct

def bswap32(x):
    """Byte-swap a 32-bit value."""
    x &= 0xFFFFFFFF
    return ((x & 0xFF) << 24) | ((x & 0xFF00) << 8) | ((x >> 8) & 0xFF00) | ((x >> 24) & 0xFF)

def forward_loop(eax, ebx):
    """Run the loop 0x2003 times as described in the writeup."""
    eax &= 0xFFFFFFFF
    ebx &= 0xFFFFFFFF
    for esi in range(1, 0x2003 + 1):
        eax = (eax ^ 0x2003) & 0xFFFFFFFF
        # xchg eax, ebx
        eax, ebx = ebx, eax
        # inc ebx
        ebx = (ebx + 1) & 0xFFFFFFFF
        # bswap eax
        eax = bswap32(eax)
        # fake ops: xor ecx,2003 / dec edx / xchg edx,ecx are on separate regs, no effect
        if esi == 0x2003:
            break
    return eax, ebx

def inverse_loop(eax, ebx):
    """
    Invert the loop to find the original (Result1, Result2) given final (eax, ebx).
    Each iteration (forward):
        eax ^= 0x2003
        eax, ebx = ebx, eax
        ebx += 1
        eax = bswap(eax)
    Inverse of one step (going backwards):
        eax = bswap(eax)          # undo bswap (bswap is its own inverse)
        ebx -= 1                  # undo inc ebx
        eax, ebx = ebx, eax       # undo xchg
        eax ^= 0x2003             # undo xor
    """
    eax &= 0xFFFFFFFF
    ebx &= 0xFFFFFFFF
    for _ in range(0x2003):
        # undo bswap eax
        eax = bswap32(eax)
        # undo inc ebx
        ebx = (ebx - 1) & 0xFFFFFFFF
        # undo xchg eax, ebx
        eax, ebx = ebx, eax
        # undo xor eax, 0x2003
        eax = (eax ^ 0x2003) & 0xFFFFFFFF
    return eax, ebx

def decode_serial_hex(serial_hex):
    """
    Decode a 16-char hex string into two DWORDs (Result1, Result2).
    Input like '1234567890ABCDEF':
      bytes: 12 34 56 78 90 AB CD EF
      Result1 = dword at offset 0 (little-endian) = 0x78563412
      Result2 = dword at offset 4 (little-endian) = 0xEFCDAB90
    """
    if len(serial_hex) != 16:
        return None, None
    serial_hex = serial_hex.upper()
    raw = bytes(int(serial_hex[i:i+2], 16) for i in range(0, 16, 2))
    result1 = struct.unpack_from('<I', raw, 0)[0]
    result2 = struct.unpack_from('<I', raw, 4)[0]
    return result1, result2

def encode_serial_hex(result1, result2):
    """Encode two DWORDs back to a 16-char hex string."""
    raw = struct.pack('<II', result1 & 0xFFFFFFFF, result2 & 0xFFFFFFFF)
    return raw.hex().upper()

# ASSUMPTION: The name-based expected value computation is NOT fully shown in the writeup.
# The writeup was truncated before showing what the loop output is compared against.
# We provide a placeholder that must be filled in with the real name hash.
def name_to_expected(name):
    """
    ASSUMPTION: Compute the expected (eax, ebx) from the name.
    The actual algorithm was NOT shown in the truncated writeup.
    This is a PLACEHOLDER - replace with the real implementation.
    """
    # ASSUMPTION: simple sum-based hash as placeholder
    h = 0
    for c in name:
        h = ((h * 0x21) + ord(c)) & 0xFFFFFFFF
    # ASSUMPTION: second dword is also derived from name somehow
    h2 = 0
    for c in reversed(name):
        h2 = ((h2 * 0x1F) ^ ord(c)) & 0xFFFFFFFF
    return h, h2

def verify(name, serial):
    """
    Verify a name/serial pair.
    serial should be 16 hex chars (no dashes), e.g. '1234567890ABCDEF'
    or with dashes stripped if entered as XXXX-XXXX-XXXX.
    """
    if len(name) < 4:
        return False
    # Strip dashes if present
    serial_clean = serial.replace('-', '').replace(' ', '').upper()
    if len(serial_clean) != 16:
        return False
    try:
        result1, result2 = decode_serial_hex(serial_clean)
    except ValueError:
        return False
    if result1 is None:
        return False
    # Run the forward loop
    eax, ebx = forward_loop(result1, result2)
    # ASSUMPTION: compare against name-derived expected values
    exp_eax, exp_ebx = name_to_expected(name)
    return eax == exp_eax and ebx == exp_ebx

def keygen(name):
    """
    Generate a serial for the given name.
    ASSUMPTION: inverts the loop using the (placeholder) name hash.
    """
    if len(name) < 4:
        raise ValueError('Name must be at least 4 characters')
    # Get expected output of the loop
    exp_eax, exp_ebx = name_to_expected(name)
    # Invert the loop to get Result1, Result2
    result1, result2 = inverse_loop(exp_eax, exp_ebx)
    # Encode as hex serial
    serial_hex = encode_serial_hex(result1, result2)
    # Format as XXXX-XXXX-XXXX (12 chars from first 12 hex digits)
    # ASSUMPTION: the display format is XXXX-XXXX-XXXX but input may be full 16 hex chars
    return serial_hex


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
