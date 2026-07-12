import ctypes
import struct

# Key used in CryptName
KEY = "8D2A6W0P9G7$1N3@"

def calc_csum1(serial: str) -> int:
    """CalcCsum1: checksums the serial string.
    The assembly loop is: csum = csum + csum + (csum << 2) + ord(ch) - 0x30
    i.e. csum = csum * 5 + (ord(ch) - 0x30) -- but wait, let's trace:
    movl i -> ecx
    eax = 0 (xor eax,eax means edx=0 after movb)
    edx = csum (saved)
    csum = csum + csum  (addl edx, csum)
    ecx = csum (copy)
    ecx <<= 2
    csum += ecx  => csum = csum*2 + csum*2*4 = ... let me re-read
    Actually:
      edx = csum
      csum = csum + edx  => csum *= 2  (addl %5, %0 where %5=edx=old_csum)
      ecx = csum
      ecx <<= 2           => ecx = csum*4
      csum += ecx         => csum = csum + csum*4 = csum*5
    Wait, after addl %5, %0: csum = csum + old_csum = 2*old_csum
    Then movl %0, %2 => ecx = 2*old_csum
    shl $2, %2 => ecx = 8*old_csum
    addl %2, %0 => csum = 2*old_csum + 8*old_csum = 10*old_csum
    Then addl %3, %0 => csum += eax (char byte)
    subl $0x30, %0 => csum -= 0x30
    So: csum = 10*csum + ord(ch) - 0x30
    This is essentially atoi!
    """
    csum = ctypes.c_uint32(0)
    for ch in serial:
        val = ctypes.c_uint32(csum.value * 10 + ord(ch) - 0x30)
        csum = val
    return csum.value

def calc_csum2(name: str) -> int:
    """CalcCsum2: repeatedly hashes name until result >= 0x3B9ACA00.
    Loop over pairs of consecutive chars:
      esi = name[ecx] ^ name[ecx+1]
      edi += esi
      edi *= 2
      edi = rol(edi, cl+1)  -- cl is the index after inc
      edi += esi + carry (adc adds carry from the rol)
    Outer loop repeats until edi >= 0x3B9ACA00.
    # ASSUMPTION: The 'adc' carry comes from the rol operation overflowing 32 bits.
    # ASSUMPTION: 'cl' in 'rol %cl, %edi' is the value of ecx after 'inc %ecx',
    #             so it's (i+1) & 0xff for position i (0-indexed).
    """
    def rol32(val, n):
        n = n & 31
        if n == 0:
            return val & 0xFFFFFFFF
        return ((val << n) | (val >> (32 - n))) & 0xFFFFFFFF

    edi = ctypes.c_uint32(0)
    name_bytes = [ord(c) for c in name] + [0]  # null-terminated
    
    while True:
        ecx = 0
        i = 0
        while True:
            edx = name_bytes[ecx] if ecx < len(name_bytes) else 0
            esi = edx
            ecx += 1
            edx2 = name_bytes[ecx] if ecx < len(name_bytes) else 0
            esi = (esi ^ edx2) & 0xFFFFFFFF
            
            # add %esi, %edi
            add_result = edi.value + esi
            carry_add = 1 if add_result > 0xFFFFFFFF else 0
            edi = ctypes.c_uint32(add_result)
            
            # imul $2, %edi
            edi = ctypes.c_uint32(edi.value * 2)
            
            # rol %cl, %edi  (cl = ecx & 0xff)
            cl = ecx & 0xff
            before_rol = edi.value
            edi = ctypes.c_uint32(rol32(before_rol, cl))
            # carry from rol: the last bit shifted out of bit 31
            # For rol, carry = bit (32-cl) of original (the last bit that wrapped)
            # ASSUMPTION: carry = (before_rol >> (32 - (cl & 31))) & 1 if cl&31 != 0 else (before_rol & 1)
            if cl & 31 != 0:
                carry_rol = (before_rol >> (32 - (cl & 31))) & 1
            else:
                carry_rol = (before_rol >> 31) & 1  # ASSUMPTION
            
            # adc %esi, %edi
            adc_result = edi.value + esi + carry_rol
            edi = ctypes.c_uint32(adc_result)
            
            if edx2 == 0:
                break
        
        if edi.value >= 0x3B9ACA00:
            return edi.value

def final_check_tmpcsum(csum2: int) -> int:
    """Compute tmpcsum from csum2.
    mov edi, csum2
    shr $0x10, edi  => edi = csum2 >> 16
    mov eax, edi
    xor al, ah      => swap/xor low two bytes of eax
    xchg al, ah     => swap al and ah
    mov edx, csum2
    xchg dl, dh     => swap low two bytes of edx
    shl $0x10, edx  => edx = (swapped low word of csum2) << 16
    xor eax, edx
    add eax, eax    => eax *= 2
    tmpcsum = eax
    """
    edi = (csum2 >> 16) & 0xFFFF
    eax = edi
    # xor al, ah: al = eax & 0xFF, ah = (eax >> 8) & 0xFF
    al = eax & 0xFF
    ah = (eax >> 8) & 0xFF
    al_new = al ^ ah
    eax = (eax & 0xFFFF0000) | (ah << 8) | al_new
    # xchg al, ah
    al2 = eax & 0xFF
    ah2 = (eax >> 8) & 0xFF
    eax = (eax & 0xFFFF0000) | (al2 << 8) | ah2
    
    edx = csum2 & 0xFFFFFFFF
    # xchg dl, dh
    dl = edx & 0xFF
    dh = (edx >> 8) & 0xFF
    edx = (edx & 0xFFFF0000) | (dl << 8) | dh
    # shl $0x10, edx
    edx = (edx << 16) & 0xFFFFFFFF
    # xor edx, eax
    eax = eax ^ edx
    # add eax, eax
    eax = (eax + eax) & 0xFFFFFFFF
    return eax

def crypt_name(name: str) -> str:
    """CryptName: produce a 16-char crypted name.
    First loop (0..15):
      idx = i % len(name)
      cl = name[idx] ^ key[i]
      cryptedName[i] = cl
    
    Second loop processes cryptedName in pairs:
      For even index i: cryptedName[i] = (cryptedName[i] & 0x0f) + 0x30
      For odd index i:  cryptedName[i] = (cryptedName[i] & 0x0f) + 0x41
    """
    name_lower = name.lower()
    crypted = [0] * 16
    n = len(name_lower)
    if n == 0:
        n = 1  # avoid division by zero
    
    for i in range(16):
        idx = i % n
        cl = ord(name_lower[idx]) ^ ord(KEY[i])
        crypted[i] = cl & 0xFF
    
    # Second pass
    i = 0
    while i < 16:
        crypted[i] = (crypted[i] & 0x0f) + 0x30
        i += 1
        if i < 16:
            crypted[i] = (crypted[i] & 0x0f) + 0x41
            i += 1
    
    return ''.join(chr(c) for c in crypted)

def keygen_easy(name: str) -> str:
    """Generate serial for easy mode: serial is numeric string whose atoi = tmpcsum."""
    csum2 = calc_csum2(name)
    tmpcsum = final_check_tmpcsum(csum2)
    return str(tmpcsum)

def keygen_hard(name: str) -> str:
    """Generate serial for hard mode.
    The crypted name (reversed, with a fixup on bit2) is the serial.
    From main():
      for i from 0x0f down to 1:
        if (cryptedName[i] & 4) == 0:
          cryptedName[i] += 4
          break
      serial = cryptedName reversed
    # ASSUMPTION: FinalHard check requires mustBe4 == 4, but we just replicate
    # the keygen output code as shown in main().
    """
    crypted = list(crypt_name(name))
    
    # fixup loop
    for i in range(0x0f, 0, -1):
        if (ord(crypted[i]) & 4) == 0:
            crypted[i] = chr(ord(crypted[i]) + 4)
            break
    
    # reverse
    serial = ''.join(reversed(crypted))
    return serial

def verify(name: str, serial: str) -> bool:
    """Verify a serial for a given name.
    Easy mode: serial (as integer via custom checksum) must equal tmpcsum derived from name.
    Hard mode: serial must match crypted-name-based serial.
    # ASSUMPTION: We check both modes; either passing counts as valid.
    """
    # Easy mode check
    try:
        csum1 = calc_csum1(serial)
        csum2 = calc_csum2(name)
        tmpcsum = final_check_tmpcsum(csum2)
        if csum1 == tmpcsum:
            return True
    except Exception:
        pass
    
    # Hard mode check
    try:
        expected_hard = keygen_hard(name)
        if serial == expected_hard:
            return True
    except Exception:
        pass
    
    return False

def keygen(name: str) -> str:
    """Return easy-mode serial (numeric)."""
    return keygen_easy(name)


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
