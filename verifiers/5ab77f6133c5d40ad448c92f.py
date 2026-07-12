import os
import ctypes

def _compute_serial(username: str) -> str:
    """
    Reimplements the sub_4012F8 logic from the crackme.
    For each DWORD-sized chunk (but the writeup iterates byte by byte via ecx),
    the assembly actually reads a DWORD at Buffer[ecx] each iteration and writes back.
    However, looking carefully at the keygen C code (main.c), it steps ecx (v0) by 1
    each time and reads *(DWORD*)&Buffer[v0], which is a sliding 4-byte window.
    The actual computation per iteration:
      edx = *(DWORD*)Buffer[ecx]  (little-endian 4 bytes)
      edx += 3
      edx |= 2
      eax = 2
      eax -= 5  => eax = -3 (0xFFFFFFFD as unsigned)
      eax |= edx
      eax += edx
      edx = eax
      => simplified: v1 = ((val + 3) | 2) | 0xFFFFFFFD + ((val+3)|2)
         but from the C keygen: v1 = ((*(DWORD*)&Buffer[v0] + 3) | 2) - 1
    The C keygen (main.c) simplifies the asm to: v1 = ((dword + 3) | 2) - 1
    Let's verify with asm:
      edx = buf[ecx] (dword)
      edx += 3
      edx |= 2        => edx = (buf+3)|2
      eax = 2
      eax -= 5        => eax = -3
      eax |= edx      => eax = edx | 0xFFFFFFFF...FD, but since edx >= 2, eax = edx | (-3)
      # -3 in 32-bit = 0xFFFFFFFD, oring with edx>=2 means all high bits set => large number
      # Wait, the C code says ((x+3)|2)-1, let's trust the C keygen author's decompilation
      eax += edx
    Actually trusting the C keygen decompilation: v1 = ((dword+3)|2) - 1
    But that doesn't match asm exactly. Let's re-derive:
      eax=2, eax-=5 => eax = 2-5 = -3 (signed) = 0xFFFFFFFD (unsigned 32-bit)
      eax |= edx  where edx=(buf+3)|2
      For typical ASCII chars (0x20-0x7F): buf+3 in range 0x23-0x82, |2 still in that range
      0xFFFFFFFD | edx: since 0xFFFFFFFD has all bits set except bit1,
        result = 0xFFFFFFFD | edx
      eax += edx => (0xFFFFFFFD | edx) + edx
    For a byte value b (treating the DWORD read as just the low byte for simplicity when
    upper bytes are 0 or null):
      edx = b + 3
      edx |= 2
      eax = 0xFFFFFFFD
      eax |= edx  = 0xFFFFFFFD | (b+3|2)
      eax += edx
    This gets complicated with DWORD reads. The C keygen author simplified it.
    ASSUMPTION: Trust the C keygen: v1 = ((dword_at_buf + 3) | 2) - 1
    But since we operate on a string, treat each position as reading a 4-byte little-endian
    int from the buffer. We'll implement it byte-by-byte matching the C code iteration.
    """
    # Build a mutable byte buffer from username (null-terminated, size 260)
    buf = bytearray(260)
    name_bytes = username.encode('ascii', errors='replace')
    for i, b in enumerate(name_bytes):
        buf[i] = b
    # pcbBuffer = length of username (number of bytes written by GetUserNameA includes null)
    # GetUserNameA sets pcbBuffer to len+1 (includes null terminator)
    pcbBuffer = len(name_bytes) + 1

    v0 = 0
    while True:
        # Read DWORD at buf[v0] little-endian
        dword_val = int.from_bytes(buf[v0:v0+4], 'little')
        # C keygen formula: v1 = ((dword_val + 3) | 2) - 1
        inner = (dword_val + 3) | 2
        v1 = (inner - 1) & 0xFFFFFFFF
        # if inner - 1 < 0x20 break before writing
        if inner - 1 < 0x20:
            break
        # Write v1 back as DWORD little-endian
        buf[v0:v0+4] = v1.to_bytes(4, 'little')
        v0 += 1
        # After increment, check v1 again
        if v1 < 0x20:
            break
        if v0 == pcbBuffer:
            break

    # Set buf[3] = '-' (ASCII 45)
    buf[3] = 45

    # The serial is buf as a null-terminated string
    result = buf[:buf.index(0)].decode('ascii', errors='replace') if 0 in buf else buf.decode('ascii', errors='replace')
    return result


def _get_windows_username() -> str:
    """Get the Windows session username if on Windows."""
    try:
        buf = ctypes.create_string_buffer(260)
        size = ctypes.c_ulong(260)
        ctypes.windll.kernel32.GetUserNameA(buf, ctypes.byref(size))
        return buf.value.decode('ascii', errors='replace')
    except Exception:
        return os.environ.get('USERNAME', os.environ.get('USER', 'User'))


def keygen(name: str) -> str:
    """
    Generate the serial for the given username.
    The crackme uses the Windows session username (GetUserNameA),
    NOT the name entered in the dialog. The serial input is compared against
    the computed value derived from the OS username.
    If name is provided, we use it as the username.
    """
    return _compute_serial(name)


def verify(name: str, serial: str) -> bool:
    """
    The crackme:
    1. Reads the serial from the input dialog (name param here is the Windows username).
    2. Gets the Windows username via GetUserNameA.
    3. Transforms the username with sub_4012F8.
    4. Compares transformed username with entered serial byte-by-byte.
    
    Here we treat 'name' as the Windows username and 'serial' as what the user entered.
    """
    expected = _compute_serial(name)
    return serial == expected



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
