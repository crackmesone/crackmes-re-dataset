import ctypes
import socket

def ror32(val, bits):
    """Rotate right 32-bit value by bits positions."""
    val &= 0xFFFFFFFF
    return ((val >> bits) | (val << (32 - bits))) & 0xFFFFFFFF

def compute_hash(name_lower):
    """
    From Solution 1 (Delphi pseudocode) and Solution 3 (C++ keygen):
    - Start with ecx = 1 (sum = 1)
    - Iterate over characters of the lowercased name
    - The C++ keygen uses length = strlen(name)+2, iterates 'length' times
      but Solution 1 says only 6-char names are accepted and iterates 8 times.
    - We follow Solution 3 (C++ keygen): iterate len(name)+2 times,
      but the last character added is buffer[length-2] which is 0 (null terminator area).
      Actually: buffer has name chars, buffer[strlen] = 0 (null), buffer[strlen+1] = 0.
      So we iterate len(name)+2 times, with extra iterations reading 0 bytes.
    - Each iteration: sum += ord(char); ror(sum, 6); sum += 1
    - After loop: sum = ~sum (bitwise NOT, 32-bit)
    """
    # ASSUMPTION: name must be exactly 6 chars (per Solution 1 author's note)
    # Solution 3 (C++ keygen) uses length = strlen(buffer)+2 iterations
    # buffer[0..strlen-1] = name chars, buffer[strlen] = 0 (null), buffer[strlen+1] = 0
    name_bytes = [ord(c) for c in name_lower]
    # Pad with zeros for the +2 iterations
    name_bytes_padded = name_bytes + [0, 0]
    
    length = len(name_lower) + 2
    ecx = 1  # sum starts at 1
    
    index = 0
    remaining = length
    while remaining > 0:
        ecx = (ecx + name_bytes_padded[index]) & 0xFFFFFFFF
        ecx = ror32(ecx, 6)
        ecx = (ecx + 1) & 0xFFFFFFFF
        index += 1
        remaining -= 1
    
    ecx = (~ecx) & 0xFFFFFFFF
    return ecx

def get_computer_name():
    """Get the machine's computer name (as used in the serial)."""
    # ASSUMPTION: On non-Windows systems, we use socket.gethostname() as approximation
    try:
        import platform
        if platform.system() == 'Windows':
            buf = ctypes.create_string_buffer(256)
            size = ctypes.c_uint(256)
            ctypes.windll.kernel32.GetComputerNameA(buf, ctypes.byref(size))
            return buf.value.decode('ascii', errors='replace')
        else:
            # ASSUMPTION: On non-Windows, use hostname
            return socket.gethostname().upper()
    except Exception:
        return socket.gethostname().upper()

def keygen(name, computer_name=None):
    """
    Generate serial for given name.
    Serial = uppercase_hex(hash) + COMPUTER_NAME
    Note: Solution 1 says only 6-char names (including spaces) are accepted.
    The name is lowercased before processing.
    """
    if computer_name is None:
        computer_name = get_computer_name()
    
    name_lower = name.lower()
    # ASSUMPTION: Per Solution 1, only names of length 6 are valid in the original crackme.
    # Solution 3 handles any length but notes the same constraint implicitly.
    
    hash_val = compute_hash(name_lower)
    serial = '%08X%s' % (hash_val, computer_name)
    return serial

def verify(name, serial, computer_name=None):
    """
    Verify name/serial pair.
    The serial must equal: hex8(hash(lowercase(name))) + COMPUTER_NAME
    """
    if computer_name is None:
        computer_name = get_computer_name()
    
    expected = keygen(name, computer_name)
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
