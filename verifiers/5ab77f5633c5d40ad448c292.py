# Reverse-engineered from therapy039s_crackme_2 writeup
# The writeup is somewhat unclear/incomplete, so several ASSUMPTION comments are included.

def name_to_derived(name):
    """
    Convert name bytes using the described algorithm:
    - seed ax = 0xDEAD (CC99 xor 1234)
    - Work through pairs of name bytes, xor-ing with ax seed
    - ror ax by 3 each pair iteration
    - If name length is odd, handle last byte with al
    Returns a list of derived bytes (dl, dh pairs per iteration).
    """
    import ctypes

    def ror16(val, n):
        val = val & 0xFFFF
        n = n % 16
        return ((val >> n) | (val << (16 - n))) & 0xFFFF

    ax = 0xDEAD
    name_bytes = [ord(c) for c in name]
    length = len(name_bytes)

    # ASSUMPTION: 'cl = length // 2' (shr cl,1), bl = length & 1 (adc bl,0 captures carry)
    half = length >> 1
    odd = length & 1

    # di points into name buffer; we iterate 'half' times (loop count = cl after shr)
    # Actually re-reading: mov bx,cx; mov cl,[05CF] = namelength
    # shr cl,1 -> cl = half count for loop
    # ASSUMPTION: loop counter is half (pairs of bytes)
    derived = []
    idx = 0  # offset into name_bytes (di starts at first char)

    dl = 0
    dh = 0
    for i in range(half):
        # xor [di], ax  -- xor word at di with ax (little-endian: lo byte at di, hi byte at di+1)
        b0 = name_bytes[idx] if idx < length else 0
        b1 = name_bytes[idx + 1] if idx + 1 < length else 0

        word_at_di = b0 | (b1 << 8)
        word_xored = word_at_di ^ ax
        name_bytes[idx] = word_xored & 0xFF
        if idx + 1 < length:
            name_bytes[idx + 1] = (word_xored >> 8) & 0xFF

        # mov dl,[di]; xor dl,[di+01]  -> dl = name_bytes[idx] ^ name_bytes[idx+1]
        dl = name_bytes[idx] ^ (name_bytes[idx + 1] if idx + 1 < length else 0)
        # mov dh,[di+01]; xor dh,[di]  -> dh = name_bytes[idx+1] ^ name_bytes[idx]
        dh = (name_bytes[idx + 1] if idx + 1 < length else 0) ^ name_bytes[idx]

        # ASSUMPTION: derived bytes are dl and dh per iteration
        derived.append(dl)
        derived.append(dh)

        # sub di,-02  -> di += 2
        idx += 2

        # ror ax,03
        ax = ror16(ax, 3)

    if odd:
        # xor dl,al (last byte case)
        al = ax & 0xFF
        last_b = name_bytes[idx] if idx < length else 0
        dl = last_b ^ al
        derived.append(dl)

    return derived


def keygen(name):
    """
    Generate serial for given name.
    Requirements:
    - name length > 5
    - serial length = 2 * name_length (hex chars, even)
    - The crackme XORs converted serial bytes with AA and compares with derived name bytes
    - 'or al,bl; inc al; jnz badboy' means (al | bl) + 1 == 0 mod 256 -> (al | bl) == 0xFF
      which means al == 0xFF and bl == 0xFF
    - ASSUMPTION: actual comparison is that derived_name_byte XOR serial_int_byte == 0xFF
      i.e. serial_int_byte = derived_name_byte ^ 0xFF = ~derived_name_byte & 0xFF
    - serial_int_byte XOR 0xAA = hex-decoded serial byte stored at 05BD
    - So hex-decoded serial byte = serial_int_byte ^ 0xAA = (derived ^ 0xFF) ^ 0xAA = derived ^ 0x55
    - ASSUMPTION: serial is hex string of those bytes
    """
    if len(name) <= 5:
        raise ValueError('Name must be more than 5 characters')

    derived = name_to_derived(name)

    # Each derived byte -> serial_byte = derived ^ 0x55, then represent as 2 hex chars
    # ASSUMPTION: serial length must be even = 2 * len(derived)
    serial_bytes = [(d ^ 0x55) for d in derived]

    serial = ''.join('{:02X}'.format(b) for b in serial_bytes)
    return serial


def verify(name, serial):
    """
    Verify name/serial pair.
    - name length > 5
    - serial length must be even and > 5 (actually > 10 since serial length > 5 and serial len = 2*name_len)
    - serial must be all hex chars
    - ASSUMPTION: serial is decoded from hex, then each byte XOR 0xAA, compared with derived name bytes
    - Check: (derived_byte | serial_int_byte) + 1 == 0 (mod 256)
      i.e. (derived_byte | serial_int_byte) == 0xFF
    """
    if len(name) <= 5:
        return False

    serial = serial.strip()
    if len(serial) % 2 != 0:
        return False
    if len(serial) <= 5:
        return False

    # Check all hex chars
    try:
        serial_raw = bytes.fromhex(serial)
    except ValueError:
        return False

    # XOR each serial byte with 0xAA to get serial_int bytes
    # ASSUMPTION: this is what 'strips ascii and stores as int after check xor with AA'
    serial_int = [(b ^ 0xAA) for b in serial_raw]

    derived = name_to_derived(name)

    if len(serial_int) != len(derived):
        return False

    for d, s in zip(derived, serial_int):
        # or al,bl; inc al; jnz badboy -> (d | s) must be 0xFF
        if (d | s) & 0xFF != 0xFF:
            return False

    return True



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
