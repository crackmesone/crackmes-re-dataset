import hashlib
import struct

def verify(name: str, serial: str) -> bool:
    """
    Verify a serial for a given name.
    
    The crackme works as follows:
    1. Append 'TccT' to the name
    2. Compute MD5 of the resulting string
    3. Extract bytes at offsets 2,3 / 6,7 / 10,11 / 14,15 of the MD5 digest
       (i.e., words at offsets 2, 6, 10, 14)
    4. Format them as hex uppercase: Hash1=md5[2:4], Hash2=md5[6:8], Hash3=md5[10:12], Hash4=md5[14:16]
    5. Concatenate to form a 16-char hex string
    6. The serial ends with 3 characters that can be anything (they are random in the keygen)
       but the basic/fixed ending is 'DIO'
    7. So the base serial is the 16 hex chars + 3 trailing chars
    
    For verification we check the first 16 hex chars match.
    The last 3 chars are random/variable so we only validate the core 16 chars.
    
    Note: The 'randomise' suffix (last part after the 16 hex chars) involves Tiger hash
    of system time converted to hex - this is fully random and not verifiable without
    the original crackme's check logic for those bytes.
    """
    if len(serial) < 16:
        return False
    
    # Step 1: name + 'TccT'
    input_str = (name + 'TccT').encode('ascii')
    
    # Step 2: MD5
    md5 = hashlib.md5(input_str).digest()
    
    # Step 3+4: Extract words at offsets 2, 6, 10, 14 (each 2 bytes)
    # Generation proc: movzx eax, word ptr MD5Digest+2h => bytes 2,3
    #                  movzx eax, word ptr MD5Digest+6h => bytes 6,7
    #                  movzx eax, word ptr MD5Digest+0Ah => bytes 10,11
    #                  movzx eax, word ptr MD5Digest+0Eh => bytes 14,15
    # HexToChar converts each byte to 2 hex chars, so 2 bytes -> 4 hex chars
    # Each Hash part is 4 hex chars
    
    def bytes_to_hex_upper(b):
        # HexToChar: for each byte, high nibble then low nibble, uppercase
        return ''.join('{:02X}'.format(x) for x in b)
    
    hash1 = bytes_to_hex_upper(md5[2:4])   # 4 chars
    hash2 = bytes_to_hex_upper(md5[6:8])   # 4 chars
    hash3 = bytes_to_hex_upper(md5[10:12]) # 4 chars
    hash4 = bytes_to_hex_upper(md5[14:16]) # 4 chars
    
    core = hash1 + hash2 + hash3 + hash4  # 16 chars
    
    # The serial consists of the 16 core chars + variable suffix (3 chars in basic mode = 'DIO')
    # ASSUMPTION: we check that the first 16 chars of the serial match
    serial_core = serial[:16].upper()
    return serial_core == core


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    
    Basic password uses fixed suffix 'DIO'.
    The last part (after the 16 hex core chars) in the keygen also appends
    2 more hex chars derived from a Tiger hash of randomized system time data,
    but since that's time-based and random, we use the minimal known-good suffix.
    
    From the C keygen source, basic password:
    - core 16 hex chars from md5[2:4]+md5[6:8]+md5[10:12]+md5[14:16]
    - suffix 'DIO'
    
    Total serial length in basic mode = 19 chars.
    """
    input_str = (name + 'TccT').encode('ascii')
    md5 = hashlib.md5(input_str).digest()
    
    hash1 = ''.join('{:02X}'.format(x) for x in md5[2:4])
    hash2 = ''.join('{:02X}'.format(x) for x in md5[6:8])
    hash3 = ''.join('{:02X}'.format(x) for x in md5[10:12])
    hash4 = ''.join('{:02X}'.format(x) for x in md5[14:16])
    
    core = hash1 + hash2 + hash3 + hash4
    
    # Basic suffix from C keygen: altEnd = "DIO" (default, method=0)
    # ASSUMPTION: The asm keygen uses a Tiger-hash derived random suffix + 2 chars
    # but the C keygen confirms 'DIO' as the fixed base suffix
    suffix = 'DIO'
    
    return core + suffix



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
