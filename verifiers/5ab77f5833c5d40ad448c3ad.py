# Reverse-engineered keygen for 'a_keygenme' by lesco
# Based on writeup by barcode_ - many details are ambiguous or missing
# Significant portions marked with # ASSUMPTION:

import ctypes
import struct

# The encoding array referenced in the disassembly as byte_4050F0
# The writeup says: 'Ghd3iHRaSkL,;-Z' but this is only 15 chars - need 16 for nibble encoding
# ASSUMPTION: the array is exactly 'Ghd3iHRaSkL,;-Z0' padded to 16 chars
ENCODE_ARRAY = b'Ghd3iHRaSkL,;-Z0'

# ASSUMPTION: Array_Size_8 referenced in the disassembly is an 8-element array
# The writeup does not reveal its contents - using placeholder zeros
# ASSUMPTION:
ARRAY_SIZE_8 = [0, 0, 0, 0, 0, 0, 0, 0]


def encode_name(name: bytes) -> bytes:
    """Convert each byte of name into two nibble-encoded bytes using ENCODE_ARRAY."""
    result = []
    for b in name:
        high = (b >> 4) & 0x0F
        low = b & 0x0F
        result.append(ENCODE_ARRAY[high])
        result.append(ENCODE_ARRAY[low])
    return bytes(result)


def _u32(x):
    return x & 0xFFFFFFFF


def compute_hash_for_name(encoded_name: bytes, start_ebx: int) -> int:
    """Simulate the first loop (loc_401445) which processes the kg-name (name field)."""
    # ASSUMPTION: loop iterates over indices 0..len(encoded_name)-1
    # ebx starts at 0x62387DEA as shown in disassembly
    ebx = _u32(start_ebx)
    n = len(encoded_name)
    for i in range(n):
        char_val = encoded_name[i]  # movsx byte -> sign extend
        if char_val > 127:
            char_val -= 256
        # imul eax, eax  => char_val^2
        eax = char_val * char_val
        # lea ecx, [eax + eax*2] => eax*3
        ecx = _u32(eax * 3)
        # shl ecx, 3 => *8
        ecx = _u32(ecx << 3)
        # sub ecx, eax => ecx = eax*24 - eax = eax*23
        ecx = _u32(ecx - _u32(eax))
        # xor edx, edx; mov edi, 7; div edi => eax = i // 7, edx = i % 7
        quot = i // 7
        edx = i % 7
        # not eax
        eax_not = _u32(~ecx)
        # imul eax, ecx
        eax2 = _u32(eax_not * ecx)
        # shl eax, 2
        eax2 = _u32(eax2 << 2)
        # mov edx, Array_Size_8[edx*4]
        # ASSUMPTION: edx selects from ARRAY_SIZE_8
        arr_val = ARRAY_SIZE_8[edx % 8]
        edx2 = _u32(arr_val + ecx)
        ecx2 = _u32(ecx)
        xored = _u32(edx2 ^ eax2)
        xored = _u32(xored ^ ebx)
        xored = _u32(xored ^ _u32(i))  # xor edx, esi (esi=i)
        ebx = xored
    return ebx


def compute_hash_for_username(encoded_username: bytes, ebx_in: int) -> int:
    """Simulate the second loop (loc_4014A5) which processes the username."""
    # ASSUMPTION: loop is similar to above but with slightly different operations
    ebx = _u32(ebx_in)
    n = len(encoded_username)
    for i in range(n):
        char_val = encoded_username[i]
        if char_val > 127:
            char_val -= 256
        # imul ecx, ecx  => ^2
        ecx = char_val * char_val
        # imul ecx, ecx  => ^4 (imul twice unlike name loop which does it once)
        ecx = _u32(ecx * ecx)
        # shl ecx, 3 => *8
        ecx = _u32(ecx << 3)
        eax = ecx
        # not eax
        eax_not = _u32(~eax)
        # imul eax, ecx
        eax2 = _u32(eax_not * ecx)
        # xor edx, edx; div ebp(7) => edx = i%7
        edx = i % 7
        arr_val = ARRAY_SIZE_8[edx % 8]
        edx2 = _u32(arr_val + ecx)
        # shl eax, 2
        eax2 = _u32(eax2 << 2)
        xored = _u32(edx2 ^ eax2)
        # xor edx, edi where edi = esi+0x42 = i+0x42
        edi = _u32(i + 0x42)
        xored = _u32(xored ^ edi)
        ebx = _u32(ebx ^ xored)
    return ebx


def get_windows_username() -> str:
    """Try to get Windows username; fall back to environment."""
    try:
        import os
        return os.environ.get('USERNAME', os.environ.get('USER', 'User'))
    except Exception:
        return 'User'


def serial_from_ebx(ebx: int) -> str:
    """Convert final EBX value to a serial string representation."""
    # ASSUMPTION: serial is the hex representation of EBX
    return '%08X' % _u32(ebx)


def keygen(name: str) -> str:
    """Generate serial for the given name."""
    username = get_windows_username()
    encoded_name = encode_name(name.encode('ascii', errors='replace'))
    encoded_username = encode_name(username.encode('ascii', errors='replace'))
    # ASSUMPTION: combined encoded string = encoded_name + encoded_username
    # First loop processes name, second processes username
    ebx = compute_hash_for_name(encoded_name, 0x62387DEA)
    ebx = compute_hash_for_username(encoded_username, ebx)
    return serial_from_ebx(ebx)


def verify(name: str, serial: str) -> bool:
    """Check if serial matches the generated serial for name."""
    if not name:
        return False
    if not serial:
        return False
    expected = keygen(name)
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
