import struct

# We need a Blowfish implementation. Using a pure-Python one.
# ASSUMPTION: The Blowfish key is NULL (empty/zero key as described in the writeup)
# ASSUMPTION: The name is encrypted with Blowfish (null key), result converted to hex ASCII
# ASSUMPTION: The serial generation loop uses the cipher bytes and a table

try:
    from Crypto.Cipher import Blowfish as _BF
    def blowfish_encrypt_null_key(data):
        # Pad data to multiple of 8 bytes
        padded = data
        remainder = len(data) % 8
        if remainder:
            padded = data + b'\x00' * (8 - remainder)
        cipher = _BF.new(b'\x00', _BF.MODE_ECB)
        result = b''
        for i in range(0, len(padded), 8):
            result += cipher.encrypt(padded[i:i+8])
        return result
except ImportError:
    def blowfish_encrypt_null_key(data):
        raise ImportError("pycryptodome required: pip install pycryptodome")

# The table bytes from szTable (DoKey.inc)
szTable = bytes([
    0x55,0x8B,0xEC,0x56,0x57,0x53,0x8B,0x5D,
    0x0C,0x8B,0x75,0x08,0x01,0x1D,0x10,0x9E,
    0x40,0x00,0xEB,0x40,0xA1,0x14,0x9E,0x40,
    0x00,0xB9,0x40,0x00,0x00,0x00,0x2B,0xC8,
    0x8D,0xB8,0xC0,0x9D,0x40,0x00,0x3B,0xCB,
    0x77,0x1E,0x2B,0xD9,0xF3,0xA4,0xE8,0xB5,
    0xF9,0xFF,0xFF,0x33,0xC0,0xA3,0x14,0x9E,
    0x40,0x00,0xBF,0xC0,0x9D,0x40,0x00,0xB9,
    0x10,0x00,0x00,0x00,0xF3,0xAB,0xEB,0x0C,
    0x8B,0xCB,0xF3,0xA4,0x01,0x1D,0x14,0x9E,
    0x40,0x00,0xEB,0x04,0x0B,0xDB,0x75,0xBC,
    0x5B,0x5F,0x5E,0xC9,0xC2,0x08,0x00,0x90,
    0x56,0x57,0x8B,0x0D,0x14,0x9E,0x40,0x00,
    0xC6,0x81,0xC0,0x9D,0x40,0x00,0x80,0x83,
    0xF9,0x38,0x72,0x18,0xE8,0x6F,0xF9,0xFF,
    0xFF,0x33,0xC0,0xA3,0x14,0x9E,0x40,0x00,
    0xBF,0xC0,0x9D,0x40,0x00,0xB9,0x10,0x00,
    0x00,0x00,0xF3,0xAB,0xA1,0x10,0x9E,0x40,
    0x00,0x33,0xD2,0x0F,0xA4,0xC2,0x03,0xC1,
    0xE0,0x03,0xA3,0xF8,0x9D,0x40,0x00,0x89,
    0x15,0xFC,0x9D,0x40,0x00,0xE8,0x3E,0xF9,
    0xFF,0xFF,0xB8,0x00,0x9E,0x40,0x00,0x5F,
    0x5E,0xC3,0xCC,0xCC,0xCC,0xCC,0xCC,0xCC,
    0x55,0x8B,0xEC,0x57,0x56,0x53,0x8B,0x5D,
    0x0C,0x8B,0x7D,0x10,0x85,0xDB,0x8B,0x75,
    0x08,0x74,0x36,0x0F,0xB6,0x06,0x8B,0xC8,
    0x83,0xC7,0x02,0xC1,0xE9,0x04,0x83,0xE0,
    0x0F,0x83,0xE1,0x0F,0x83,0xF8,0x0A,0x1B,
    0xD2,0x83,0xD0,0x00,0x8D,0x44,0xD0,0x37,
    0x83,0xF9,0x0A,0x1B,0xD2,0x83,0xD1,0x00,
    0xC1,0xE0,0x08,0x8D,0x4C,0xD1,0x37,0x0B,
    0xC1,0x46,0x66,0x89,0x47,0xFE,0x4B,0x75,
    0xCA,0x8B,0xC7,0xC6,0x07,0x00,0x2B,0x45,
    0x10,0x5B,0x5E,0x5F,0xC9,0xC2,0x0C,0x00,
])

MASK32 = 0xFFFFFFFF

def _to_signed32(v):
    v = v & 0xFFFFFFFF
    if v >= 0x80000000:
        v -= 0x100000000
    return v

def _to_u32(v):
    return v & 0xFFFFFFFF

def compute_serial(name_bytes):
    """
    Implements the key generation loop from the crackme.
    name_bytes: the raw name as bytes
    """
    # Encrypt name with Blowfish (null key)
    cipher_bytes = blowfish_encrypt_null_key(name_bytes)

    # ebx = name_length * 2 (this is what 'imul eax,2 / mov ebx,eax' does
    # after the ascii-hex transform returns name_len*2)
    name_len = len(name_bytes)
    ebx = name_len * 2  # result of transform into ascii (each byte -> 2 hex chars)

    # Initial edx = 0x00524544
    edx = 0x00524544
    ecx = 0
    # The loop index goes from 0 to ebx-1 (ecx < ebx)
    # But ebx changes inside the loop: mov ebx, eax (after sub)
    # We need to save the original ebx for the table index and loop bound
    original_ebx = ebx

    # ASSUMPTION: The loop runs ecx from 0 to original_ebx-1 (ecx increments each iter)
    # but ebx is overwritten with eax each iteration (used for IMUL and next table index).
    # The CMP ecx,ebx uses the *current* ebx (which was just set to eax from SUB).
    # This means the loop may terminate early or run differently.
    # We'll implement it as faithfully as possible.

    push_stack = []
    current_ebx = original_ebx

    for _ in range(original_ebx):  # safety limit
        # MOVZX eax, byte ptr [ecx + CipherBuff]
        eax = cipher_bytes[ecx % len(cipher_bytes)]
        # MOV dl, byte ptr [ebx + szTable]  -- ebx here is current_ebx
        # ASSUMPTION: table index uses current_ebx at this point
        table_idx = current_ebx % len(szTable)
        dl = szTable[table_idx]
        # edx low byte is replaced; reconstruct edx with new dl
        edx = (edx & 0xFFFFFF00) | dl
        # ADD eax, edx
        eax = _to_u32(eax + edx)
        # IMUL eax, eax, 0x407AF0
        eax = _to_u32(eax * 0x407AF0)
        # ADD edx, eax
        edx = _to_u32(edx + eax)
        # SUB eax, 0x587370
        eax = _to_u32(eax - 0x587370)
        # PUSH eax
        push_stack.append(eax)
        # INC ecx
        ecx += 1
        # CMP ecx, ebx  (current_ebx)
        # MOV ebx, eax
        current_ebx = eax
        # XOR eax, eax
        eax = 0
        # IMUL ebx, ebx, 0x4076F0
        current_ebx = _to_u32(current_ebx * 0x4076F0)
        # AND eax, 0x4076F0
        eax = eax & 0x4076F0
        # JNZ -> loop back if eax != 0 (but eax was just XOR'd to 0, AND 0x4076F0 = 0)
        # ASSUMPTION: JNZ is effectively 'loop while ecx < original_ebx'
        # because eax after XOR eax,eax and AND eax,... is always 0.
        # So the loop runs original_ebx times.
        if ecx >= original_ebx:
            break

    # After the loop, PUSH edx then format: "%.8X%.8X"
    # The two pushes to wsprintf are: push eax (last computed), push edx
    # wsprintf(FinalSerial, "%.8X%.8X", edx_val, eax_val)
    # The stack order: push eax first, push edx second, then format, then buf
    # wsprintf args (left to right after buf/fmt): edx_val, eax_val
    # But x86 cdecl pushes right-to-left, so "%.8X%.8X" first arg = edx, second = last eax
    last_eax = push_stack[-1] if push_stack else 0
    serial = "%08X%08X" % (edx, last_eax)
    return serial


def verify(name: str, serial: str) -> bool:
    name_bytes = name.encode('ascii', errors='replace')
    expected = keygen(name)
    return serial.upper() == expected.upper()


def keygen(name: str) -> str:
    name_bytes = name.encode('ascii', errors='replace')
    return compute_serial(name_bytes)



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
