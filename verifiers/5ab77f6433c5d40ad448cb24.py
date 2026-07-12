import struct

def _pack4(s, offset):
    """Read 4 bytes from string s starting at offset, pad with zeros if short."""
    chunk = s[offset:offset+4].encode('latin-1') if isinstance(s, str) else s[offset:offset+4]
    chunk = chunk.ljust(4, b'\x00')
    return struct.unpack_from('<I', chunk)[0]

def _compute_hash(text):
    """
    Computes the hash value for a name or serial string using the algorithm
    found in the crackme's validation routine.

    For name:
      ecx = DWORD at [text+0]  (first 4 chars)
      edx = DWORD at [text+4]  (next 4 chars)
      al  = cl, ah = ch, ROL eax, 16, al = dl, ah = dh
        => eax = (ecx & 0xFFFF0000) | (edx & 0x0000FFFF)  ... but let's be precise:
        al=cl means low byte of eax = low byte of ecx
        ah=ch means second byte of eax = second byte of ecx
        ROL eax,16 swaps high/low 16 bits
        al=dl means low byte of eax = low byte of edx
        ah=dh means second byte of eax = second byte of edx
      ecx ^= 0x616D6974
      edx ^= 0x726B6861
      ecx ^= edx
      eax ^= ecx
      esi = eax
      edi = ecx
    """
    ecx = _pack4(text, 0)
    edx = _pack4(text, 4)

    # Build eax from ecx and edx bytes
    al = ecx & 0xFF
    ah = (ecx >> 8) & 0xFF
    eax = (al | (ah << 8)) & 0xFFFFFFFF
    # ROL eax, 16
    eax = ((eax << 16) | (eax >> 16)) & 0xFFFFFFFF
    # al = dl, ah = dh
    al = edx & 0xFF
    ah = (edx >> 8) & 0xFF
    eax = (eax & 0xFFFF0000) | (al | (ah << 8))
    eax &= 0xFFFFFFFF

    ecx = (ecx ^ 0x616D6974) & 0xFFFFFFFF
    edx = (edx ^ 0x726B6861) & 0xFFFFFFFF
    ecx = (ecx ^ edx) & 0xFFFFFFFF
    eax = (eax ^ ecx) & 0xFFFFFFFF
    esi = eax
    edi = ecx
    return esi, edi

def _compute_serial_hash(serial):
    """
    Same structure as name hash but different XOR constants:
      ecx ^= 0x416D6972
      edx ^= 0x72696D61
      ecx ^= edx
      eax ^= ecx
    """
    ecx = _pack4(serial, 0)
    edx = _pack4(serial, 4)

    al = ecx & 0xFF
    ah = (ecx >> 8) & 0xFF
    eax = (al | (ah << 8)) & 0xFFFFFFFF
    # ROL eax, 16
    eax = ((eax << 16) | (eax >> 16)) & 0xFFFFFFFF
    al = edx & 0xFF
    ah = (edx >> 8) & 0xFF
    eax = (eax & 0xFFFF0000) | (al | (ah << 8))
    eax &= 0xFFFFFFFF

    ecx = (ecx ^ 0x416D6972) & 0xFFFFFFFF
    edx = (edx ^ 0x72696D61) & 0xFFFFFFFF
    ecx = (ecx ^ edx) & 0xFFFFFFFF
    eax = (eax ^ ecx) & 0xFFFFFFFF
    return eax, ecx

def verify(name, serial):
    """
    Validation logic (from 004011D7 .. 0040122D):

    1. Compute name hash -> esi_name, edi_name
    2. Compute serial hash -> eax_ser, ecx_ser
    3. esi = esi_name ^ eax_ser         (XOR ESI,EAX  at 00401229)
    4. ecx = ecx_ser ^ edi_name         (XOR ECX,EDI  at 0040122B)
    5. Pass to 004011CF: if ecx == 0 then correct

    So the condition is:
      ecx_ser XOR edi_name == 0
      i.e. ecx_ser == edi_name
    """
    if len(name) < 1:
        return False

    _, edi_name = _compute_hash(name)
    _, ecx_ser = _compute_serial_hash(serial)

    ecx_final = (ecx_ser ^ edi_name) & 0xFFFFFFFF
    return ecx_final == 0

def keygen(name):
    """
    We need ecx_ser == edi_name.

    ecx_ser = ((pack4(serial,0) ^ 0x416D6972) ^ (pack4(serial,4) ^ 0x72696D61)) & 0xFFFFFFFF

    We can freely choose serial[4:8] = b'\x00\x00\x00\x00' (edx=0),
    then:
      ecx_ser = (pack4(serial,0) ^ 0x416D6972) ^ 0x72696D61

    We want ecx_ser = edi_name, so:
      pack4(serial,0) = edi_name ^ 0x416D6972 ^ 0x72696D61

    Then pad serial bytes [4:8] with zeros.
    """
    _, edi_name = _compute_hash(name)

    # serial first 4 bytes
    target = (edi_name ^ 0x416D6972 ^ 0x72696D61) & 0xFFFFFFFF
    serial_bytes = struct.pack('<I', target) + b'\x00\x00\x00\x00'
    # Convert to printable string (latin-1 to preserve bytes)
    serial = serial_bytes.decode('latin-1')
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
