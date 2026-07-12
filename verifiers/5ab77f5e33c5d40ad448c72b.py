import ctypes
import struct

def atolnew(s: bytes) -> int:
    """Custom atol: treats every byte as digit by subtracting 48, including non-digit chars."""
    t = 0
    for b in s:
        if b == 0:
            break
        e = (b - 48) & 0xFF
        t = t * 10 + e
    # simulate C long (32-bit signed)
    t = ctypes.c_long(t).value
    return t

def wsprintf_lu(val: int) -> bytes:
    """Simulate wsprintf with %lu format (unsigned long, 32-bit)."""
    val = val & 0xFFFFFFFF
    return str(val).encode('ascii')

def checkit(string1: str, string2: str) -> bool:
    # Work with mutable byte arrays
    s1 = bytearray(string1.encode('latin-1'))
    s2 = bytearray(string2.encode('latin-1'))

    # Simple length checks
    if len(s1) <= 4:
        return False
    if len(s2) <= 4:
        return False

    string2_length = len(s2)

    # Convert string1 to lowercase (bitwise OR with 0x20)
    for i in range(len(s1)):
        s1[i] = s1[i] | 0x20

    # Compute differences: string2[i] = string1[i] - string2[i]
    # Only iterates over len(string2) characters
    diff = bytearray(10)
    for i in range(string2_length):
        val = (s1[i] - s2[i]) & 0xFF
        diff[i] = val
    # null-terminate
    if string2_length < 10:
        diff[string2_length] = 0

    # Zero enc_string
    enc_string = bytearray(10)

    count = string2_length

    # Main crypt routine
    while count:
        # atolnew(diff) * count
        # Build null-terminated bytes for atolnew
        diff_bytes = bytes(diff)
        r_long = atolnew(diff_bytes)
        # multiply by count (as unsigned 32-bit)
        r = ctypes.c_ulong(r_long * count).value

        # Convert r back to ascii string
        temp_str = wsprintf_lu(r)
        # Build temp as bytearray of length 10, null padded
        temp = bytearray(10)
        for i, b in enumerate(temp_str):
            if i >= 10:
                break
            temp[i] = b
        # remaining are already 0

        # AND each byte with 0x0f
        for i in range(10):
            if temp[i] == 0:
                break
            temp[i] = temp[i] & 0x0F

        # r = string2_length / 2
        r_half = string2_length // 2
        i_idx = r_half
        l_idx = 0
        loop_r = r_half

        while loop_r:
            enc_string[l_idx] = (enc_string[l_idx] + temp[l_idx] + temp[i_idx]) & 0xFF
            enc_string[l_idx] = enc_string[l_idx] & 0x0F
            l_idx += 1
            i_idx += 1
            loop_r -= 1

        count -= 1

    # Check the answer
    r_half = string2_length // 2
    for i in range(r_half):
        if enc_string[i] != string2_length:
            return False
    return True


def verify(name: str, serial: str) -> bool:
    """Verify name/serial pair."""
    return checkit(name, serial)


def keygen(name: str):
    """Brute-force keygen: tries serials starting from 100000 upward."""
    if len(name) <= 4:
        raise ValueError('Name must be more than 4 characters')
    j = 99999
    while True:
        j += 1
        serial = str(j)
        if checkit(name, serial):
            return serial
        # Safety limit to avoid infinite loop in tests
        if j > 10_000_000:
            return None



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
