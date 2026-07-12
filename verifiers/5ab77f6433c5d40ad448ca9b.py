import random
import struct

# Crackme_9 by jube - key validation algorithm
# Based on writeup by crackmes.de
#
# Key format: B1-B2-B3-B4-B5-B6-B7
# Each block is a decimal integer (>=0)
# Name is NOT used in validation (noted explicitly in writeup)
#
# Constraints:
# 1. Serial must have exactly 6 dashes (7 blocks)
# 2. Serial must NOT start with '-'
# 3. Each block is a decimal number (chars 0-9)
#
# Check 1: The loop over blocks 1(eax), 5(ebx/B5->edx in code), 7(edx)
#   Starting from eax=7th_block, edx=1st_block(after xchg), ebx=5th_block
#   Loop runs ecx=0x0ABCDE (703710) times doing:
#     ROL eax,1; XOR ah,bl; ROR ebx,3; ROL eax,2; ADD eax,ecx; ROL eax,2; ADD eax,edx
#   Final eax must == 0x0B7C28CC
#
# Check 2 (XOR key construction for code patch):
#   xor1 = B1 ^ B4 must == 0x37AD0AE9  (ASSUMPTION: from writeup '37ad0ae9', note Pascal source has '37ad6ae9' - using '37AD0AE9' from text description)
#   xor2 = B2 ^ B5 must == 0x4F80F0AE  (ASSUMPTION: from writeup '4f80f0ae', Pascal has '4f86f0ae' - using text)
#   xor3 = B3 ^ B6 must == 0x51B3014B
#   B5 == 0 (stated: 'the 5th key is 0')
#   B2 == 0x4F80F0AE (since B5=0, B2 xor 0 = 0x4F80F0AE)
#   B4 = B1 ^ 0x37AD0AE9
#   B3 and B6 are random but B3 ^ B6 = 0x51B3014B

# ASSUMPTION: XOR constants from text description (slight discrepancy with Pascal source noted)
XOR1_TARGET = 0x37AD0AE9
XOR2_TARGET = 0x4F80F0AE
XOR3_TARGET = 0x51B3014B
FINAL_EAX   = 0x0B7C28CC

MASK32 = 0xFFFFFFFF

def ror32(val, n):
    val &= MASK32
    return ((val >> n) | (val << (32 - n))) & MASK32

def rol32(val, n):
    val &= MASK32
    return ((val << n) | (val >> (32 - n))) & MASK32

def xor_ah(eax, ebx):
    """XOR AH (bits 8-15) of eax with BL (bits 0-7) of ebx"""
    ah = (eax >> 8) & 0xFF
    bl = ebx & 0xFF
    ah = ah ^ bl
    eax = (eax & 0xFFFF00FF) | ((ah & 0xFF) << 8)
    return eax & MASK32

def forward_check1(b1, b5, b7):
    """
    Simulate the loop from the crackme.
    Inputs: b1=1st block, b5=5th block, b7=7th block
    After XCHG eax,edx: eax=b7, edx=b1
    ebx = b5
    Loop ecx from 1 to 703710 (0x0ABCDE)
    """
    eax = b7 & MASK32
    edx = b1 & MASK32
    ebx = b5 & MASK32
    for ecx in range(1, 0x0ABCDE + 1):
        eax = rol32(eax, 1)
        eax = xor_ah(eax, ebx)
        ebx = ror32(ebx, 3)
        eax = rol32(eax, 2)
        eax = (eax + ecx) & MASK32
        eax = rol32(eax, 2)
        eax = (eax + edx) & MASK32
    return eax

def reverse_check1(b1, b5_target=0):
    """
    Reverse the loop to find b7 given b1 and b5.
    b5 must be 0 per writeup ('the 5th key is 0, so the 2nd key is 4f80f0ae')
    # ASSUMPTION: ebx=0 throughout reverse (because b5=0 and ror(0,3)=0)
    Starting eax = FINAL_EAX, reverse 703710 iterations.
    """
    eax = FINAL_EAX
    edx = b1 & MASK32
    ebx = b5_target & MASK32
    # We need to reverse ebx state - precompute forward ebx states
    # Since ebx=0 and ror(0,3)=0 always, ebx stays 0 if b5=0
    # So xor_ah with bl=0 is a no-op
    for ecx in range(0x0ABCDE, 0, -1):
        eax = (eax - edx) & MASK32
        eax = ror32(eax, 2)
        eax = (eax - ecx) & MASK32
        eax = ror32(eax, 2)
        # reverse xor_ah (xor is its own inverse)
        # ebx at this iteration: we need to know ebx *before* ror in forward direction
        # Since b5=0 => ebx always 0 => bl=0 => xor_ah is no-op
        eax = xor_ah(eax, ebx)  # no-op if ebx=0
        eax = ror32(eax, 1)
    return eax  # this is b7

def verify(name, serial):
    """Verify the serial against the crackme algorithm. Name is not used."""
    parts = serial.split('-')
    if len(parts) != 7:
        return False
    # Each part must be a non-negative decimal integer (digits only)
    for p in parts:
        if not p.isdigit():
            return False
    # Serial must not start with '-'
    if serial.startswith('-'):
        return False
    # Parse blocks as integers
    try:
        blocks = [int(p) for p in parts]
    except ValueError:
        return False
    b1, b2, b3, b4, b5, b6, b7 = blocks
    # Check XOR constraints
    if (b1 ^ b4) != XOR1_TARGET:
        return False
    if (b2 ^ b5) != XOR2_TARGET:
        return False
    if (b3 ^ b6) != XOR3_TARGET:
        return False
    # Check the loop result
    result = forward_check1(b1, b5, b7)
    if result != FINAL_EAX:
        return False
    return True

def keygen(name):
    """
    Generate a valid serial.
    Per writeup:
      b5 = 0
      b2 = XOR2_TARGET ^ b5 = XOR2_TARGET ^ 0 = XOR2_TARGET
      b1 = any value such that b7 > 0 and b4 > 0
      b4 = b1 ^ XOR1_TARGET
      b3 = random, b6 = b3 ^ XOR3_TARGET
      b7 = reverse_check1(b1, b5=0)
    """
    b5 = 0
    b2 = XOR2_TARGET ^ b5  # = 0x4F80F0AE = 1334243502
    # Pick random b1 (must be > 0 as unsigned 32-bit; and b7 must be > 0)
    # ASSUMPTION: b1 can be any positive 32-bit integer
    while True:
        b1 = random.randint(1, 0xFFFFFFFF)
        b4 = (b1 ^ XOR1_TARGET) & MASK32
        if b4 == 0:
            continue
        b7 = reverse_check1(b1, b5)
        if b7 == 0:
            continue
        # Verify forward
        if forward_check1(b1, b5, b7) != FINAL_EAX:
            continue
        break
    b3 = random.randint(1, 0xFFFFFFFF)
    b6 = (b3 ^ XOR3_TARGET) & MASK32
    if b6 == 0:
        b3 += 1
        b6 = (b3 ^ XOR3_TARGET) & MASK32
    serial = f"{b1}-{b2}-{b3}-{b4}-{b5}-{b6}-{b7}"
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
