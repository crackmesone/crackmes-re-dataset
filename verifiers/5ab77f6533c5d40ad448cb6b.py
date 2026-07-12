import struct

def compute_name_hash(name: str) -> int:
    """Sum of ASCII bytes of the computer name (same as crackme init routine)."""
    return sum(ord(c) for c in name)


def verify_clipboard(clipboard_text: str, name: str) -> bool:
    """
    Step 1 check: subtract each byte of clipboard text (using len(name) bytes)
    from the name_hash; result must be zero.
    This means clipboard_text bytes (first len(name) of them) must sum to name_hash.
    The simplest valid clipboard content is the computer name itself.
    """
    name_hash = compute_name_hash(name)
    name_len = len(name)
    clip_bytes = clipboard_text.encode('ascii', errors='replace')
    # The asm reads ecx+esi-1 counting down from ecx=name_len to 1
    # effectively summing the first name_len bytes of clipboard
    if len(clip_bytes) < name_len:
        return False
    running = name_hash
    for i in range(name_len, 0, -1):
        running -= clip_bytes[i - 1]
    # imul eax,-1 / add eax,1 / imul eax,-1 / add eax,1  is identity for all values
    # i.e. ((-x)+1)*-1 + 1 = x  => no net change
    eax = running & 0xFFFFFFFF
    # treat as signed 32-bit
    if eax >= 0x80000000:
        eax -= 0x100000000
    eax = eax * -1
    eax = eax + 1
    eax = eax * -1
    eax = eax + 1
    return eax == 0


def verify_keyfile(key_bytes: bytes, name: str) -> bool:
    """
    Step 2 check: reg.key must be at least 8 bytes.
    Read first dword and second dword, XOR them, add dword_403342 (which is 0
    after a successful step1 with computer name in clipboard), compare to name_hash.
    dword_403342 is zero when clipboard == computername (sub loop zeroes it).
    """
    if len(key_bytes) < 8:
        return False
    name_hash = compute_name_hash(name)
    dword1 = struct.unpack_from('<I', key_bytes, 0)[0]
    dword2 = struct.unpack_from('<I', key_bytes, 4)[0]
    # dword_403342 is 0 when step1 passed with computer name in clipboard
    dword_403342 = 0  # ASSUMPTION: clipboard contained exactly the computer name
    eax = (dword1 ^ dword2) + dword_403342
    eax &= 0xFFFFFFFF
    return eax == (name_hash & 0xFFFFFFFF)


def verify(name: str, serial: bytes) -> bool:
    """
    Full verification:
      - clipboard must contain the computer name (we simulate that as given)
      - serial is the 8-byte reg.key content
    Returns True if both checks pass.
    """
    # Step 1: clipboard must be the computer name
    clipboard_ok = verify_clipboard(name, name)
    if not clipboard_ok:
        return False
    # Step 2: keyfile check
    return verify_keyfile(serial, name)


def keygen(name: str) -> bytes:
    """
    Generate an 8-byte reg.key for the given computer name.
    Strategy: set first 4 bytes = 0x00000000, second 4 bytes = name_hash
    because 0 XOR name_hash == name_hash.
    dword_403342 is 0 (clipboard == computer name), so result == name_hash. Pass.
    """
    name_hash = compute_name_hash(name)
    name_hash &= 0xFFFFFFFF
    part1 = 0x00000000
    part2 = part1 ^ name_hash  # == name_hash
    key_bytes = struct.pack('<II', part1, part2)
    return key_bytes

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
