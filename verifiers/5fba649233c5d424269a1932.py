import struct

def _email_valid(email: str) -> bool:
    """Validate email: must have at least 5 chars, '@' not in first pos,
    at least 2 chars after '@', a '.' after '@' with at least 2 chars after it."""
    if len(email) < 5:
        return False
    at_pos = email.find('@', 1)  # '@' must not be at index 0
    if at_pos == -1:
        return False
    after_at = email[at_pos + 1:]
    if len(after_at) < 2:
        return False
    dot_pos = after_at.find('.')
    if dot_pos == -1:
        return False
    after_dot = after_at[dot_pos + 1:]
    if len(after_dot) < 1:
        return False
    # The assembly checks ecx (remaining count) > 2 after finding '.'
    # which means there must be at least 2 chars after the dot
    # ASSUMPTION: based on assembly 'cmp ecx,2 / jle fQuit' after finding '.'
    # ecx is the remaining repne scas count; need at least 1 char after dot
    # Looking more carefully: after '@' scan, ecx must be > 2 (jle fQuit means <=2 fails)
    # after '.' scan, ecx must be > 2 as well
    # This means domain part needs enough chars. We'll mirror the C asm logic.
    return True


def _email_valid_asm(email: str) -> bool:
    """More faithful recreation of the assembly email validation."""
    n = len(email)
    if n < 5:
        return False
    # repne scas starting at index 1 looking for '@' (0x40)
    # ecx starts at n (nb_c), we start scanning from index 1
    ecx = n
    idx = 1
    found_at = -1
    while ecx > 0:
        if email[idx] == '@':
            found_at = idx
            ecx -= 1
            break
        ecx -= 1
        idx += 1
        if idx >= n:
            break
    if found_at == -1:
        return False
    # after repne scas, ecx is remaining; cmp ecx,2 / jle fQuit
    if ecx <= 2:
        return False
    # inc edi (move past '@'), scan for '.' (0x2E)
    idx = found_at + 1
    # ecx is still the remaining count from previous scan
    found_dot = -1
    while ecx > 0:
        if idx >= n:
            break
        if email[idx] == '.':
            found_dot = idx
            ecx -= 1
            break
        ecx -= 1
        idx += 1
    if found_dot == -1:
        return False
    # cmp ecx,2 / jle fQuit
    if ecx <= 2:
        return False
    return True


def _gen_serial(email: str) -> str:
    """Generate serial from email using the assembly algorithm."""
    # Read first 4 bytes of email as little-endian DWORD
    # Pad with zeros if email shorter than 4 chars (shouldn't happen with valid email)
    raw = email[:4].encode('ascii', errors='replace')
    raw = raw.ljust(4, b'\x00')
    eax = struct.unpack('<I', raw)[0]
    
    # xor eax, 0x12345678
    eax = (eax ^ 0x12345678) & 0xFFFFFFFF
    
    result = [''] * 8
    
    for ecx in range(8):
        # rol eax, 4
        eax = ((eax << 4) | (eax >> 28)) & 0xFFFFFFFF
        # mov bl, al; and ebx, 15
        nibble = eax & 0x0F
        if nibble <= 9:
            ch = chr(nibble + 48)  # '0'..'9'
        else:
            ch = chr(nibble + 55)  # 'A'..'F'
        result[ecx] = ch
    
    # Final fixup: and eax,15; add al,71; mov byte ptr[szSr+7],al
    # After 8 rotations of 4 bits each = 32 bits = full rotation, eax is back to XOR'd value
    # and eax,15 -> last nibble of eax
    last_nibble = eax & 0x0F
    # add al, 71 (0x47)
    last_char = chr((last_nibble + 0x47) & 0xFF)
    result[7] = last_char
    
    return ''.join(result)


def keygen(name: str) -> str:
    """Generate a valid serial for the given email address."""
    if not _email_valid_asm(name):
        raise ValueError(f"Invalid email address: {name}")
    return _gen_serial(name)


def verify(name: str, serial: str) -> bool:
    """Verify that serial matches the one generated for the given email."""
    if not _email_valid_asm(name):
        return False
    expected = _gen_serial(name)
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
