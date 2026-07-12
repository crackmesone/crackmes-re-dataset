import struct

def compute_serial(name: str) -> int:
    """
    Implements the name hash algorithm described in the writeups.
    
    Loop over each character (1-indexed counter starting at 1):
        hash = 0
        for i, ch in enumerate(name, start=1):
            eax = ord(ch) ^ 0x7D3
            eax = (eax * i) & 0xFFFFFFFF  # imul edi (counter)
            hash = (hash + eax) & 0xFFFFFFFF
            hash = (hash - 0x1D) & 0xFFFFFFFF
    
    Then:
        hash = hash * len(name)  (signed 32-bit)
        hash = hash // ord(name[0])  (signed integer division)
        hash = hash * hash
        hash = hash + 0x15
    
    Return hash as signed 32-bit integer (decimal string).
    """
    # Use signed 32-bit arithmetic via ctypes-style wrapping
    def to_signed32(n):
        n = n & 0xFFFFFFFF
        if n >= 0x80000000:
            n -= 0x100000000
        return n

    name_hash = 0  # (ebp-08), starts at 0

    for i, ch in enumerate(name, start=1):
        # eax = ord(ch) ^ 0x7D3
        eax = ord(ch) ^ 0x7D3
        # imul edi (counter = i): signed multiply eax * i, keep lower 32 bits
        eax = to_signed32(eax * i)
        # add to hash
        name_hash = to_signed32(name_hash + eax)
        # sub 0x1D
        name_hash = to_signed32(name_hash - 0x1D)

    # multiply hash by name length
    name_hash = to_signed32(name_hash * len(name))

    # divide by first character value (signed integer division)
    first_char_val = ord(name[0])
    # Python integer division truncates toward zero for signed (idiv behavior)
    import math
    if first_char_val == 0:
        raise ValueError("First character cannot be null")
    # idiv in x86 truncates toward zero
    name_hash = int(name_hash / first_char_val)  # truncate toward zero
    name_hash = to_signed32(name_hash)

    # multiply by itself
    name_hash = to_signed32(name_hash * name_hash)

    # add 0x15 (21 decimal)
    name_hash = to_signed32(name_hash + 0x15)

    return name_hash


COMMAND_HARDCODED = bytes([0xD3, 0xA5, 0xB2, 0xA9, 0xA1, 0xAC, 0xC3, 0xA8,
                            0xA5, 0xA3, 0xAB, 0x00])

def decode_command_bytes(data: bytes) -> str:
    """
    Reverse the command encoding:
        encoded_byte = (ord(ch) XOR 0xE0) + 0x20
    So: ch = (encoded_byte - 0x20) XOR 0xE0
    """
    result = []
    for b in data:
        if b == 0:
            break
        t = (b - 0x20) ^ 0xE0
        result.append(chr(t))
    return ''.join(result)


# The required command string (decoded from hardcoded bytes)
REQUIRED_COMMAND = decode_command_bytes(COMMAND_HARDCODED)  # Should be 'SerialCheck'


def verify_command(command: str) -> bool:
    """
    Encode the command string and compare to hardcoded bytes.
    encoding: for each char: (ord(ch) XOR 0xE0) + 0x20
    """
    hardcoded = [0xD3, 0xA5, 0xB2, 0xA9, 0xA1, 0xAC, 0xC3, 0xA8,
                 0xA5, 0xA3, 0xAB, 0x00]
    # Build encoded version of command (null-terminated)
    encoded = []
    for ch in command:
        encoded.append(((ord(ch) ^ 0xE0) + 0x20) & 0xFF)
    encoded.append(0x00)  # null terminator
    # Compare first 12 bytes
    if len(encoded) != len(hardcoded):
        return False
    return encoded == hardcoded


def verify(name: str, serial: str, command: str = 'SerialCheck') -> bool:
    """
    Full verification:
    1. Command must encode to the hardcoded bytes (= 'SerialCheck')
    2. Serial must match the computed name hash as a decimal string
    Note: The crackme checks on KeyChange of command box, so all fields
    must be filled before typing the last char of command.
    """
    if not name:
        return False
    if not verify_command(command):
        return False
    expected_serial = compute_serial(name)
    try:
        entered = int(serial)
    except ValueError:
        return False
    return entered == expected_serial


def keygen(name: str) -> str:
    """
    Generate the valid serial for a given name.
    Returns the serial as a decimal string.
    Also prints the required command.
    """
    serial = compute_serial(name)
    return str(serial)



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
