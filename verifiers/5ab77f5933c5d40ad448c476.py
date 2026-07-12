# KeyGenMe #4 by CromaxX - Partial reconstruction
# Based on writeups by Taliesin and Cyclops from crackmes.de
#
# IMPORTANT: Both writeups confirm this crackme has a fundamental issue:
# At address 0x401616, MOVSX ECX, BYTE PTR SS:[EBP-14] loads a 'magic value'
# that depends on how the dialog was invoked (click vs Enter key).
# The value of CL changes the SHL/SAR operations, making consistent keygen
# only possible when 'Verify' button is CLICKED (not Enter pressed).
# When clicked, EBP-14 = 0x6E consistently.
#
# The writeups describe 8 intermediate results, subfunctions at 0x401290,
# 0x4012B6, 0x4012DA, 0x4012F4, 0x401324, but do NOT provide their
# disassembly. We cannot fully implement without knowing these subfunctions.
#
# ASSUMPTION: Magic value (EBP-14) = 0x6E when Verify is clicked.
# ASSUMPTION: Subfunction implementations are estimated from context clues only.

import struct
import ctypes

MAGIC_SHIFT = 0x6E  # ASSUMPTION: value when Verify button is clicked

def _to_signed32(n):
    """Convert to signed 32-bit integer."""
    n = n & 0xFFFFFFFF
    if n >= 0x80000000:
        n -= 0x100000000
    return n

def _to_u32(n):
    return n & 0xFFFFFFFF

# ASSUMPTION: These subfunctions are placeholders.
# Without their disassembly we cannot implement them correctly.
# The names are derived from the call pattern in the writeup.

def _sub_401290(a, b, c):
    # ASSUMPTION: some arithmetic/bitwise combination of three 32-bit values
    # Called with: (F0_val, F4_val, F0_val ^ F4_val)
    return _to_u32((a ^ b) + c)

def _sub_4012B6(a, b, c):
    # ASSUMPTION: another combination
    return _to_u32(a ^ b ^ c)

def _sub_4012DA(a, b):
    # ASSUMPTION: two-arg function
    return _to_u32(a + b)

def _sub_4012F4(a, b, c, d):
    # ASSUMPTION: four-arg function
    return _to_u32(a ^ b ^ c ^ d)

def _sub_401324(a):
    # ASSUMPTION: single-arg transformation (maybe byte-swap or rotate)
    # Context: applied to f0, f4, f8, fc, 100 after main computation
    a = _to_u32(a)
    # ASSUMPTION: rotate right by some amount, or reverse bytes
    return _to_u32(((a >> 8) | (a << 24)) & 0xFFFFFFFF)

def compute_serial_raw(name):
    """
    Reconstruct the serial generation algorithm.
    Phase 1: Loop over name bytes, XOR each with 0xC50711, accumulate.
    Phase 2: Use accumulated value plus last-char-modified to derive 8 results.
    Phase 3: sprintf some results to decimal string, increment each byte by 2.
    """
    # Phase 1: Accumulate XOR sum
    # The loop increments each name character (INC BYTE PTR [EDX]) and
    # XORs with 0xC50711, adding result to accumulator.
    name_bytes = list(name.encode('ascii', errors='replace'))
    
    acc_f0 = 0  # EBP-F0 accumulator
    
    for i in range(len(name_bytes)):
        ch = name_bytes[i]
        ecx = ch ^ 0x00C50711
        ecx = _to_u32(ecx)
        acc_f0 = _to_u32(acc_f0 + ecx)
        # INC BYTE PTR [EDX] - increment the character in place
        name_bytes[i] = (name_bytes[i] + 1) & 0xFF

    # After loop: use last char (incremented) XOR'd with acc
    # At 004015FF: EAX = address of last name byte (already incremented)
    # MOVSX EDX, BYTE PTR [EAX] = last byte value (incremented)
    last_byte = name_bytes[len(name_bytes) - 1] if name_bytes else 0
    edx = _to_signed32(last_byte)
    
    # XOR eax(=acc_f0) with edx
    f0 = _to_u32(acc_f0)
    eax = _to_u32(f0 ^ (edx & 0xFF))
    
    # SHL EAX, CL then SAR EAX, CL
    # ASSUMPTION: magic_shift = 0x6E = 110. SHL by 110 mod 32 = 14, SAR by 14
    # Actually x86 SHL uses CL mod 32, so 0x6E % 32 = 14
    shift_amount = MAGIC_SHIFT % 32
    eax_shl = _to_u32(eax << shift_amount)
    # SAR (arithmetic right shift) by CL (same CL = length of name at 401622)
    # ASSUMPTION: at 401622 ECX = EBP-EC = length of name
    sar_amount = len(name) % 32
    eax_signed = _to_signed32(eax_shl)
    f4 = _to_u32(eax_signed >> sar_amount) if sar_amount > 0 else _to_u32(eax_signed)

    # INC f0
    f0 = _to_u32(f0 + 1)

    # f8 = sub_401290(f0, f4, f4 ^ f0)
    f8 = _sub_401290(f0, f4, _to_u32(f4 ^ f0))

    # fc = sub_4012B6(f0, f4, f4 ^ f0)
    fc = _sub_4012B6(f0, f4, _to_u32(f4 ^ f0))

    # r100 = sub_4012DA(f8, fc)
    r100 = _sub_4012DA(f8, fc)

    # r104 = (r100 & f8) ^ fc
    r104 = _to_u32((r100 & f8) ^ fc)

    # r108 = sub_4012B6(f8, fc, r100)
    r108 = _sub_4012B6(f8, fc, r100)

    # r10c = sub_4012F4(f8, fc, r104, r108)
    r10c = _sub_4012F4(f8, fc, r104, r108)

    # Apply sub_401324 to f0, f4, f8, fc, r100
    f0  = _sub_401324(f0)
    f4  = _sub_401324(f4)
    f8  = _sub_401324(f8)
    fc  = _sub_401324(fc)
    r100 = _sub_401324(r100)

    # ASSUMPTION: The 6 values used in sprintf are f0, f4, f8, fc, r100, r104 (or similar)
    # sprintf formats them as decimal with "CromaxX" magic letters mixed in
    # Then each byte of result is incremented by 2
    results = [f0, f4, f8, fc, r100, r104]
    return results

def verify(name, serial):
    """
    Attempt to verify name/serial pair.
    ASSUMPTION: We compare generated serial to provided serial.
    Due to missing subfunction implementations, this will not be accurate.
    """
    if not name or not serial:
        return False
    try:
        generated = keygen(name)
        return generated == serial
    except Exception:
        return False

def keygen(name):
    """
    Generate a serial for the given name.
    ASSUMPTION: sprintf format uses 6 results as unsigned decimals,
    possibly with 'CromaxX' prefix/suffix or interleaved.
    Each byte of the resulting string is then incremented by 2.
    """
    results = compute_serial_raw(name)
    
    # ASSUMPTION: sprintf produces a string of decimal numbers
    # Based on writeup: 'Some of those results (along with some magic letters
    # i.e. CromaxX) are sent to sprintf function to turn the hex to decimal'
    # ASSUMPTION: format is something like "%u%u%u%u%u%u" or similar
    raw_str = ''.join(str(r & 0xFFFFFFFF) for r in results)
    
    # Each byte of result increased by 2 (writeup: 'Each byte of the result
    # is then increased by 2 for the key (3 for the compare)')
    # ASSUMPTION: 'key' means what we show user, 'compare' is what crackme
    # stores internally. We produce the 'key' version (+2).
    serial_bytes = [(ord(c) + 2) & 0xFF for c in raw_str]
    serial = ''.join(chr(b) for b in serial_bytes)
    
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
