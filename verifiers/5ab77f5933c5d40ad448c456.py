#!/usr/bin/env python3
"""
Bispoo Crackme#1 - Serial Validator & Keygen

Algorithm reconstructed from multiple solution write-ups.

The serial generation works as follows:
1. For each character in the username (1-indexed, i from 1..len):
   - Take the ASCII value of the character
   - Multiply by i (IMUL EAX, ESI where ESI starts at 1)
   - Add i
   - SHL by 0xBA (186)
   - SHR by 0xBE (190)  -- net effect: SHR by 4 (190-186=4), but operates on 32-bit register
   - XOR with i
   - ADD 0x32 (50)
   - Store the byte in key buffer
   - Accumulate sum in EDX

2. After loop:
   - Multiply EDX by the DWORD at key[0] (little-endian 4 bytes of the key buffer)
   - NOT the result (bitwise complement, 32-bit)
   - The serial is the decimal string of that value

Note: All operations are 32-bit (C uint32 semantics), except the final result
which may be interpreted as signed or unsigned depending on sign.
"""

import struct


def _compute_key_bytes(name: str):
    """Compute the key byte array from username."""
    key = []
    edx = 0  # accumulator
    for i, ch in enumerate(name, start=1):
        eax = ord(ch) & 0xFFFFFFFF
        esi = i
        eax = (eax * esi) & 0xFFFFFFFF
        eax = (eax + esi) & 0xFFFFFFFF
        # SHL EAX, 0xBA then SHR EAX, 0xBE
        # On x86, shift count is masked to 5 bits for 32-bit shifts
        # 0xBA & 0x1F = 26, 0xBE & 0x1F = 30
        shl_count = 0xBA & 0x1F  # = 26
        shr_count = 0xBE & 0x1F  # = 30
        eax = (eax << shl_count) & 0xFFFFFFFF
        eax = (eax >> shr_count) & 0xFFFFFFFF
        eax = (eax ^ esi) & 0xFFFFFFFF
        # ADD AL, 0x32 (only low byte)
        al = ((eax & 0xFF) + 0x32) & 0xFF
        eax = (eax & 0xFFFFFF00) | al
        key.append(al)
        edx = (edx + eax) & 0xFFFFFFFF
    return key, edx


def _generate_serial(name: str) -> str:
    """Generate serial for the given name."""
    if len(name) < 4 or len(name) > 15:
        raise ValueError("Name must be between 4 and 15 characters.")

    key, edx = _compute_key_bytes(name)

    # The key buffer as DWORD (little-endian first 4 bytes)
    # ASSUMPTION: key_dword is the 32-bit little-endian interpretation of first 4 bytes
    # pad if fewer than 4 chars (shouldn't happen given min length 4)
    key_bytes = bytes(key[:4]).ljust(4, b'\x00')
    key_dword = struct.unpack('<I', key_bytes)[0]

    # IMUL EDX, key_dword
    result = (edx * key_dword) & 0xFFFFFFFF

    # NOT result (32-bit)
    result = (~result) & 0xFFFFFFFF

    # The Delphi keygen uses num2 := NOT num2, then checks if > 0
    # In Delphi, integers are signed 32-bit, so NOT of a positive number is negative
    # ASSUMPTION: The crackme compares as signed 32-bit integer printed as decimal
    # Convert to signed 32-bit
    if result >= 0x80000000:
        result_signed = result - 0x100000000
    else:
        result_signed = result

    # The Delphi code shows: if num2 > 0 then serial = inttostr(num2)
    # else serial = aux1(inttostr(num2)) which does hex encoding
    # ASSUMPTION: Most names produce a negative result; the aux1 path (hex of negative decimal)
    # is less common. We implement both paths.
    if result_signed > 0:
        return str(result_signed)
    else:
        # aux1 path: convert to decimal string, then XOR each char with 0xDE and hex-encode
        # From Delphi aux1: for each char, aux2 = ord(c) XOR 3735927486 AND 255
        # 3735927486 = 0xDEADBABE, so AND 255 -> XOR with 0xBE
        # if aux2 == 147 (0x93) then aux2 = 136 (0x88)
        s = str(result_signed)
        result_str = ''
        for c in s:
            v = (ord(c) ^ 0xBE) & 0xFF
            if v == 147:
                v = 136
            result_str += format(v, '02X')
        return result_str


def keygen(name: str) -> str:
    """Generate a valid serial for the given name."""
    return _generate_serial(name)


def verify(name: str, serial: str) -> bool:
    """Verify that the serial matches the expected serial for the given name."""
    if len(name) < 4 or len(name) > 15:
        return False
    try:
        expected = _generate_serial(name)
        return serial.strip() == expected.strip()
    except Exception:
        return False



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
