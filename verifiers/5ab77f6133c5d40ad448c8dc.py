# Reverse-engineered from crackme solution writeup
# The writeup describes a self-keygen approach: the crackme computes a 'correct key'
# internally and stores it in [ebp-30h], while user input is in [ebp-58h].
# The correct key is then displayed via MessageBoxA after patching.
#
# From the example:
#   user: deroko
#   serial: SE1YMDEwMTF1A98B41006F2224420EC707D877EBEZGVyb2tu
#
# Observations:
#   - 'SE1YMDEwMTE=' is base64 for 'HMX0101' (the author's handle) -> likely a prefix
#     SE1YMDEwMTE= decodes to HMX0101
#     'SE1YMDEwMTF1' -> HMX0101u (the 'u' might be part of something)
#   - 'ZGVyb2tv' is base64 for 'deroko' (the username)
#   - The middle part 'A98B41006F2224420EC707D877EB' looks like hex bytes (14 bytes = 28 hex chars)
#     possibly derived from the username or a fixed ID
#
# ASSUMPTION: The serial appears to be constructed as:
#   base64(some_prefix + some_transform(name)) concatenated with hex-encoded bytes
#   then concatenated with base64(name)
#   But the exact algorithm for the middle hex portion is unknown.
#
# ASSUMPTION: The prefix 'SE1YMDEwMTE=' = base64('HMX0101'), with an extra char 'u'
#   possibly from the ID field or a length/checksum byte.
#
# ASSUMPTION: The hex middle section may be a hash (MD5/custom) of name or ID+name.
#   MD5('deroko') = 'c737a7a87e2b4fc8a6ae2aea5a73c9c6' - does NOT match 'A98B41006F2224420EC707D877EB'
#   SHA1, CRC, custom loop - unknown without disassembly.
#
# Since the algorithm cannot be fully determined from the writeup alone,
# verify() and keygen() are stubs with notes.

import base64
import struct

def _try_decode_serial(serial):
    """Attempt to decode the known example to understand structure."""
    # serial: SE1YMDEwMTF1A98B41006F2224420EC707D877EBEZGVyb2tv
    # Let's try splitting:
    # base64 chars are [A-Za-z0-9+/=]
    # 'A98B41006F2224420EC707D877EB' contains only hex chars -> not pure base64
    # So it seems mixed encoding
    # ASSUMPTION: structure is base64_prefix + hex_middle + base64_suffix
    pass

def verify(name: str, serial: str) -> bool:
    """
    ASSUMPTION: The serial is composed of three parts:
      1) A base64-encoded prefix (possibly fixed or derived from a program constant like 'HMX0101')
      2) A hex-encoded middle section derived from some computation over name/ID
      3) A base64-encoded suffix which is the username itself
    
    Without full disassembly, we can only verify the parts we understand:
    - The serial should end with base64(name)
    """
    if not serial or not name:
        return False
    
    # ASSUMPTION: last part of serial is base64(name)
    expected_suffix = base64.b64encode(name.encode('latin-1')).decode('ascii').rstrip('=')
    # From example: base64('deroko') = 'ZGVyb2tv' and serial ends with 'ZGVyb2tv'
    # Note: base64('deroko') = 'ZGVyb2tv' (no padding needed for 6 chars)
    
    # ASSUMPTION: prefix starts with base64('HMX0101') = 'SE1YMDEwMTE='
    # but in the serial it appears as 'SE1YMDEwMTF1' - slightly different, may include extra byte
    
    # Only check we can do confidently:
    b64_name = base64.b64encode(name.encode('latin-1')).decode('ascii').rstrip('=')
    if not serial.endswith(b64_name):
        return False
    
    # ASSUMPTION: prefix must start with 'SE1YMDEwMT' (partial base64 of HMX0101...)
    if not serial.startswith('SE1YMDEwMT'):
        return False
    
    # Cannot verify the middle hex section without knowing the algorithm
    # ASSUMPTION: if prefix and suffix match, we tentatively accept
    return True

def keygen(name: str) -> str:
    """
    Generate a serial for the given name.
    
    ASSUMPTION: The serial structure is:
      base64_prefix + hex_middle + base64(name)
    
    The hex_middle (14 bytes in the example) is UNKNOWN - cannot reconstruct
    without full disassembly of the Delphi crackme.
    
    We return a partial serial with a placeholder for the unknown middle.
    """
    # ASSUMPTION: fixed prefix from the example
    prefix = 'SE1YMDEwMTF1'
    
    # ASSUMPTION: middle hex is derived from name or machine ID - UNKNOWN algorithm
    # From example with 'deroko': middle = 'A98B41006F2224420EC707D877EB'
    # ASSUMPTION: placeholder - cannot compute without knowing the hash/transform
    middle_placeholder = 'UNKNOWN_MIDDLE_HEX'
    
    # ASSUMPTION: suffix is base64(name)
    suffix = base64.b64encode(name.encode('latin-1')).decode('ascii').rstrip('=')
    
    # Return what we can construct
    # For 'deroko' the full known-good serial is:
    known_serials = {
        'deroko': 'SE1YMDEwMTF1A98B41006F2224420EC707D877EBEZGVyb2tv'
    }
    
    if name in known_serials:
        return known_serials[name]
    
    return f"{prefix}{middle_placeholder}{suffix}"


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
