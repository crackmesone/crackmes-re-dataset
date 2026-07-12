#!/usr/bin/env python3
"""
xor_crackme0 by 0x00786f72

From the writeup:
1. Serial must be 28 hex characters long (28 chars -> 14 bytes when hex-decoded,
   but the writeup says '28 long' for the serial string and it gets hex-decoded,
   so 28 hex chars = 14 bytes... actually the writeup says length must be a
   4-multiple check, and serial_bytes have length=10 passed to VM_Hash.)
   # ASSUMPTION: Serial is 28 hex characters (14 bytes), first 20 hex chars = 10 bytes
   # hashed, last 8 hex chars = last DWORD (4 bytes)

2. serial_10byte_hash + serial_last_word = name_hash
   where serial_last_word is the last WORD (2 bytes) of the serial bytes,
   and name_hash is computed from the name.

   The writeup says "serial_hash + serial_lastDW = name_hash" but also says
   "even not dword" - the comparison is word-sized (16-bit).
   # ASSUMPTION: serial_last_word is last 2 bytes (WORD) of the hex-decoded serial.

VM Hash analysis from writeup (Hash 1 sub-procedure and Hash 3 sub-procedure):

Hash procedure called twice (once for name, once for serial bytes).
From the VM disassembly:

Hash 1 sub (@00):
  wR9 ^= 0x28ED
  wR9 ^= 0xABCD
  wR1 = 0x018E
  wR6 = wR1  (wR6 = 0x018E)
  CALL @34  (rotate subroutine)
  wR1 = 0x0DA0
  wR1 ^= wR10
  wR6 ^= wR1
  wR10 = wR6
  JUMP @68 (exit_VM)

Rotate sub (@34):
  wR0 |= 1
  if wR6 & 1 != 0: skip next
  wR0 &= ~1
  wR1 = 4
  Loop @44:
    wR0 &= ~1
    wR6 = RCR(wR6, 1) using Cf from wR0 bit0
    if wR0 bit0 == 0: OR wR6, 0x8000  (i.e., if no carry, set high bit)
    wR1 += -1
    if wR1 == 0: skip JUMP back
    JUMP @44
  wR1 = wR6
  RET

Hash 3 sub (@6C):
  wR25 = 0x1234
  wR9 ^= 0x0EDA
  wR1 = ~wR9 (XOR -1)
  wR1 ^= 0xF125
  wR7 = wR1
  wR1 = wR10
  wR1 += 0xF126
  wR1 += 0x0EDA
  wR9 = wR1
  wR10 = wR7
  exit_VM

# ASSUMPTION: The full hash loop iterates over each character of the input,
# calling sub-procedures per character. The exact loop structure and which
# sub-procedures are called per iteration is not fully shown.
# We implement what we can deduce from the writeup.
"""

def ror16(val, n, carry_in=0):
    """Rotate right 16-bit with carry (RCR)"""
    val &= 0xFFFF
    for _ in range(n):
        new_carry = val & 1
        val = (val >> 1) | (carry_in << 15)
        carry_in = new_carry
    return val & 0xFFFF, carry_in

def rotate_sub(wR6):
    """VM subroutine @34: rotate wR6 right by 4 with carry semantics"""
    # wR0 bit0 = carry flag
    # Initial: set wR0 bit0 = 1
    carry = 1
    # if wR6 & 1 != 0: keep carry=1, else carry=0
    if (wR6 & 1) == 0:
        carry = 0
    wR1 = 4
    while True:
        carry = 0  # AND wR0, NOT 1
        # RCR wR6 by 1 using carry
        new_carry = wR6 & 1
        wR6 = ((wR6 >> 1) | (carry << 15)) & 0xFFFF
        carry = new_carry
        # if carry == 0: OR wR6, 0x8000
        if carry == 0:
            wR6 = (wR6 | 0x8000) & 0xFFFF
        wR1 = (wR1 + 0xFFFF) & 0xFFFF  # ADD wR1, -1
        if wR1 == 0:
            break  # skip jump = exit loop
        # else JUMP back to @44
    return wR6

def hash1_sub(wR9, wR10):
    """VM Hash 1 sub-procedure @00"""
    wR9 = (wR9 ^ 0x28ED) & 0xFFFF
    wR9 = (wR9 ^ 0xABCD) & 0xFFFF
    wR6 = 0x018E
    # CALL @34
    wR6 = rotate_sub(wR6)
    wR1 = 0x0DA0
    wR1 = (wR1 ^ wR10) & 0xFFFF
    wR6 = (wR6 ^ wR1) & 0xFFFF
    wR10 = wR6
    return wR9, wR10

def hash3_sub(wR9, wR10):
    """VM Hash 3 sub-procedure @6C"""
    wR9 = (wR9 ^ 0x0EDA) & 0xFFFF
    wR1 = (~wR9) & 0xFFFF  # XOR -1
    wR1 = (wR1 ^ 0xF125) & 0xFFFF
    wR7 = wR1
    wR1 = wR10
    wR1 = (wR1 + 0xF126) & 0xFFFF
    wR1 = (wR1 + 0x0EDA) & 0xFFFF
    wR9 = wR1
    wR10 = wR7
    return wR9, wR10

# ASSUMPTION: The VM_Hash function iterates over bytes of input,
# calling hash subs for each byte. The exact sequence of sub calls
# per byte is unknown. We assume hash1_sub is called per byte with
# wR9 initialized to the byte value and wR10 accumulated.
# This is a best-guess reconstruction.

def vm_hash(data_bytes):
    """
    # ASSUMPTION: Hash accumulates wR9 and wR10 across all bytes.
    # wR9 starts as first byte, wR10 starts as 0.
    # Each byte: wR9 XOR= byte, then hash1_sub called, then hash3_sub called.
    # Final result is (wR9 + wR10) & 0xFFFF (word-sized).
    """
    wR9 = 0
    wR10 = 0
    for b in data_bytes:
        wR9 = (wR9 ^ b) & 0xFFFF
        wR9, wR10 = hash1_sub(wR9, wR10)
        wR9, wR10 = hash3_sub(wR9, wR10)
    # ASSUMPTION: final hash = wR9 XOR wR10 or wR9 + wR10
    return (wR9 + wR10) & 0xFFFF

def verify(name, serial):
    """
    Verify name/serial pair.
    
    From writeup:
    1. serial must be 28 chars long
    2. serial is hex-encoded: convert to bytes
    3. first 10 bytes used for serial hash (20 hex chars)
    4. last word (last 2 bytes / 4 hex chars) is serial_last_word
    5. serial_hash + serial_last_word == name_hash (word arithmetic)
    """
    if len(serial) != 28:
        return False
    # Check all hex
    try:
        serial_bytes = bytes.fromhex(serial)
    except ValueError:
        return False
    # 14 bytes total: first 10 bytes hashed, last 4 bytes contain last_word
    # ASSUMPTION: last WORD = last 2 bytes (bytes 12-13 = serial_bytes[12:14])
    serial_10 = serial_bytes[:10]
    # ASSUMPTION: last word is bytes[12:14] little-endian
    last_word = serial_bytes[12] | (serial_bytes[13] << 8)
    
    name_bytes = name.encode('latin-1') if isinstance(name, str) else name
    name_h = vm_hash(name_bytes)
    serial_h = vm_hash(serial_10)
    
    return ((serial_h + last_word) & 0xFFFF) == name_h

def keygen(name):
    """
    Generate a serial for the given name.
    
    serial_last_word = name_hash - serial_hash
    We choose serial_10 = first 10 bytes arbitrarily (e.g., all zeros),
    compute needed last_word, then pad remaining 2 bytes.
    ASSUMPTION: bytes 10-11 of serial_bytes can be anything (using 0000).
    """
    name_bytes = name.encode('latin-1') if isinstance(name, str) else name
    name_h = vm_hash(name_bytes)
    
    # Choose first 10 serial bytes
    serial_10 = bytes(10)  # all zeros
    serial_h = vm_hash(serial_10)
    
    last_word = (name_h - serial_h) & 0xFFFF
    
    # Construct 14-byte serial: 10 bytes + 2 padding + 2 byte last_word (LE)
    serial_bytes = serial_10 + bytes(2) + bytes([last_word & 0xFF, (last_word >> 8) & 0xFF])
    serial = serial_bytes.hex().upper()
    return serial


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
