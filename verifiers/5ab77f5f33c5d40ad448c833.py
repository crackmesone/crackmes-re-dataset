# Reverse-engineered keygen for keygenme_3_wr by warrock
# Based on the C# keygen source found in the solution writeup.
# The writeup source is encoded in a mangled encoding; key logic was extracted
# from readable fragments. Gaps are marked with # ASSUMPTION:

import hashlib
import struct

def _md5_modified(data: bytes) -> bytes:
    """Standard MD5 - the writeup mentions a 'modified MD5 routine with other magic constants'
    but the keygen itself calls MD5.GetMD5Bytes(buffer) which in the helper file
    (md5modified.cs) uses different magic constants.
    # ASSUMPTION: We use standard MD5 here; the actual crackme may use modified constants.
    """
    return hashlib.md5(data).digest()


def _compute_snr1(username: str) -> str:
    """First part of SN: iterate forward through username chars.
    For each char x: temp = char_value; temp += result; temp *= 0x7272;
    temp2 = temp * temp; temp = temp2 + temp; temp *= 0x4744; temp += temp
    result = temp
    After loop: snr_1 = hex(result)[last 4 hex digits]
    """
    result = 0
    for ch in username:
        temp = ord(ch)
        temp += result
        temp *= 0x7272
        temp2 = temp * temp
        temp = temp2 + temp
        temp *= 0x4744
        temp += temp
        result = temp
    str_result = format(result & 0xFFFFFFFF, '08x')
    snr_1 = ''
    if len(str_result) > 4:
        snr_1 = str_result[:4]
    return snr_1


def _compute_snr2(username: str) -> str:
    """Second part of SN: iterate backward through username chars.
    For each char x (reverse): temp = char_value; temp += 0x11;
    temp -= 0x5; temp *= 0x92; temp += temp; result += temp
    After loop: snr_2 = hex(result)[last 4 hex digits]
    # ASSUMPTION: Operations derived from partial readability of mangled source.
    """
    result = 0
    for ch in reversed(username):
        temp = ord(ch)
        temp += 0x11
        temp -= 0x5
        temp *= 0x92
        temp += temp
        result += temp
    str_result = format(result & 0xFFFFFFFF, '08x')
    snr_2 = ''
    if len(str_result) > 4:
        snr_2 = str_result[:4]
    return snr_2


def _compute_snr3(username: str) -> str:
    """Third part of SN: MD5-based.
    The writeup shows:
    - A special addstring (byte array) is appended to username bytes
    - The buffer = username_bytes + addstring_bytes
    - snr_3 = MD5_modified(buffer).hex()[:8]
    # ASSUMPTION: addstring and MD5 variant are approximated.
    """
    # The byte_addstring from the source (partially decoded):
    # {0x77,0x30,0x39,0x2F,0x26,0x37,0x32,0x30,0x28,0x3D,0x3D,0x29,0x21,0x26,0x3F,0x29,0x3D,0x28,0x2C}
    # ASSUMPTION: This is based on the visible hex values in the writeup
    byte_addstring = bytes([
        0x77, 0x30, 0x39, 0x2F, 0x26, 0x37, 0x32, 0x30,
        0x28, 0x3D, 0x3D, 0x29, 0x21, 0x26, 0x3F, 0x29,
        0x3D, 0x28, 0x2C
    ])
    enc = 'ascii'
    username_bytes = username.encode(enc)
    buffer = username_bytes + byte_addstring
    # ASSUMPTION: standard MD5; real crackme uses modified MD5
    md5_result = _md5_modified(buffer)
    str_result = md5_result.hex().upper()
    snr_3 = ''
    if len(str_result) > 8:
        snr_3 = str_result[:8]
    return snr_3


def _compute_snr4(username: str) -> str:
    """Fourth part of SN: iterate backward through username chars.
    # ASSUMPTION: Operations derived from partial decoding:
    result += temp; result += 0x299; result += 0x677;
    result += temp2 (accumulated); result *= 0x8329;
    temp2 = result; temp2 -= 0x33; temp2 *= result; temp2 += result
    """
    result = 0
    temp2 = 0
    for ch in reversed(username):
        temp = ord(ch)
        result += temp
        result += 0x299
        result += 0x677
        result += temp2
        result *= 0x8329
        temp2 = result
        temp2 -= 0x33
        temp2 *= result
        temp2 += result
    str_result = format(result & 0xFFFFFFFF, '08x')
    snr_4 = ''
    if len(str_result) > 4:
        snr_4 = str_result[:4]
    return snr_4


def _compute_snr5(username: str) -> str:
    """Fifth part of SN: iterate forward through username chars.
    # ASSUMPTION: Operations derived from partial decoding of EBX/EDX computations:
    EDX = char; EBX += EDX; EBX += EBX (was ECX); 
    EDX = EBX; EDX *= EBX; EBX ^= 0x10;
    EBX |= 0x44; EDX = EBX * 0x3737;
    EDX += 0x4343; EBX = EDX
    EBX += EDX; EBX *= EBX;
    """
    EBX = 0
    EBX2 = 0  # EBB (second register)
    for ch in username:
        EDX = ord(ch)
        EBX += EDX
        EBX += EBX2  # EBX was ECX in original
        EDX = EBX
        EDX *= EBX
        EBX ^= 0x10
        EBX |= 0x44
        EDX = (EBX * 0x3737) & 0xFFFFFFFF
        EDX += 0x4343
        EBX = EDX
        EBX = (EBX + EDX) & 0xFFFFFFFF
        EBX = (EBX * EBX) & 0xFFFFFFFF
        EBX2 = EBX
    str_result = format(EBX & 0xFFFFFFFF, '08x')
    snr_5 = ''
    if len(str_result) > 4:
        snr_5 = str_result[:4]
    return snr_5


def keygen(name: str) -> str:
    """Generate a serial for the given username."""
    if not (3 <= len(name) <= 30):
        raise ValueError('Username must be 3-30 chars')
    snr_1 = _compute_snr1(name)
    snr_2 = _compute_snr2(name)
    snr_3 = _compute_snr3(name)
    snr_4 = _compute_snr4(name)
    snr_5 = _compute_snr5(name)
    snr = f'{snr_1}-{snr_2}-{snr_3}-{snr_4}-{snr_5}'
    return snr.upper()


def verify(name: str, serial: str) -> bool:
    """Verify a serial for the given username."""
    try:
        expected = keygen(name)
        return serial.upper() == expected.upper()
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
