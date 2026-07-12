import hashlib
import struct

# ASSUMPTION: The 'calc' function inside 'keygenme.dat' library is not available.
# Based on the writeup, the algorithm is:
# 1. Validate name length: 6 <= len(name) <= 10
# 2. Hash the name using MD2
# 3. Pass the MD2 hash to the 'calc' function (from keygenme.dat DLL) to get serial bytes
# 4. Serial is displayed as 20 hex chars (10 bytes -> 20 hex chars)
# 5. User serial is compared byte-by-byte (10 bytes) against generated serial
#
# The critical unknown is what 'calc' does to the MD2 hash.
# ASSUMPTION: Based on the solution description mentioning 3DES and the DLL,
# 'calc' likely performs 3DES encryption on the MD2 hash using some hardcoded key.
# We do NOT have that key or the exact calc implementation.
#
# We implement what we know for certain and mark the gap.

def md2(data):
    """Pure Python MD2 hash implementation."""
    if isinstance(data, str):
        data = data.encode('ascii')
    
    # MD2 S-box (pi_subst)
    S = [
        41, 46, 67, 201, 162, 216, 124, 1, 61, 54, 84, 161, 236, 240, 6, 19,
        98, 167, 5, 243, 192, 199, 115, 140, 152, 147, 43, 217, 188, 76, 130, 202,
        30, 155, 87, 60, 253, 212, 224, 22, 103, 66, 111, 24, 138, 23, 229, 18,
        190, 78, 196, 214, 218, 158, 222, 73, 160, 251, 245, 142, 187, 47, 238, 122,
        169, 104, 121, 145, 21, 178, 7, 63, 148, 194, 16, 137, 11, 34, 95, 33,
        128, 127, 93, 154, 90, 144, 50, 39, 53, 62, 204, 231, 191, 247, 151, 3,
        255, 25, 48, 179, 72, 165, 181, 209, 215, 94, 146, 42, 172, 86, 170, 198,
        79, 184, 56, 210, 150, 164, 125, 182, 118, 252, 107, 226, 156, 116, 4, 241,
        69, 157, 112, 89, 100, 113, 135, 32, 134, 91, 207, 101, 230, 45, 168, 2,
        27, 96, 37, 173, 174, 176, 185, 246, 28, 70, 97, 105, 52, 64, 126, 15,
        85, 71, 163, 35, 221, 81, 175, 58, 195, 92, 249, 206, 186, 197, 234, 38,
        44, 83, 13, 110, 133, 40, 132, 9, 211, 223, 205, 244, 65, 129, 77, 82,
        106, 220, 55, 200, 108, 193, 171, 250, 36, 225, 123, 8, 12, 189, 177, 74,
        120, 136, 149, 139, 227, 99, 232, 109, 233, 203, 213, 254, 59, 0, 29, 57,
        242, 239, 183, 14, 102, 88, 208, 228, 166, 119, 114, 248, 235, 117, 75, 10,
        49, 68, 80, 180, 143, 237, 31, 26, 219, 153, 141, 51, 159, 17, 131, 20
    ]
    
    # Step 1: Append padding bytes
    msg = bytearray(data)
    pad_len = 16 - (len(msg) % 16)
    msg.extend([pad_len] * pad_len)
    
    # Step 2: Append checksum
    C = bytearray(16)
    L = 0
    for i in range(len(msg) // 16):
        for j in range(16):
            c = msg[i * 16 + j]
            C[j] ^= S[c ^ L]
            L = C[j]
    msg.extend(C)
    
    # Step 3: Initialize MD buffer
    X = bytearray(48)
    
    # Step 4: Process message in 16-byte blocks
    for i in range(len(msg) // 16):
        for j in range(16):
            X[16 + j] = msg[i * 16 + j]
            X[32 + j] = X[16 + j] ^ X[j]
        t = 0
        for j in range(18):
            for k in range(48):
                t = X[k] ^ S[t]
                X[k] = t
            t = (t + j) % 256
    
    return bytes(X[:16])


def calc_serial(md2_hash):
    """
    ASSUMPTION: The 'calc' function from keygenme.dat processes the MD2 hash
    and returns 10 bytes used as the serial. The exact algorithm inside 'calc'
    is unknown without the DLL. It likely uses 3DES encryption with a
    hardcoded key on the MD2 hash, but we don't have that key.
    
    This is a placeholder that cannot be implemented without the actual DLL.
    """
    # ASSUMPTION: Without the 'calc' function from keygenme.dat, we cannot
    # compute the correct serial. The function takes 16 bytes of MD2 hash
    # and returns some transformed output used as 10 bytes of serial.
    raise NotImplementedError(
        "The 'calc' function from keygenme.dat (embedded DLL) is required. "
        "Its internals are not fully described in the writeup."
    )


def verify(name, serial):
    """
    Verify name/serial pair.
    
    From the writeup:
    - name length must be 6..10
    - MD2 hash of name computed
    - MD2 hash passed to 'calc' from keygenme.dat
    - result compared to hex-decoded serial (serial must be 20 hex chars = 10 bytes)
    """
    if isinstance(name, str):
        name_bytes = name.encode('ascii')
    else:
        name_bytes = name
    
    # Check name length: 6 <= len <= 10
    if len(name_bytes) < 6 or len(name_bytes) > 10:
        return False
    
    # Serial must be 20 hex characters
    if len(serial) != 20:
        return False
    
    # Decode user serial from hex
    try:
        user_serial_bytes = bytes.fromhex(serial)
    except ValueError:
        return False
    
    # Compute MD2 hash of name
    name_md2 = md2(name_bytes)
    
    # ASSUMPTION: Call 'calc' on the MD2 hash to get generated serial bytes
    try:
        generated_serial_bytes = calc_serial(name_md2)
    except NotImplementedError:
        raise
    
    # Compare 10 bytes
    return user_serial_bytes == generated_serial_bytes[:10]


def keygen(name):
    """
    Generate serial for given name.
    Requires the 'calc' function from keygenme.dat which is not available here.
    """
    if isinstance(name, str):
        name_bytes = name.encode('ascii')
    else:
        name_bytes = name
    
    if len(name_bytes) < 6 or len(name_bytes) > 10:
        raise ValueError("Name must be 6-10 characters long")
    
    name_md2 = md2(name_bytes)
    
    # ASSUMPTION: calc() from keygenme.dat does the serial computation
    serial_bytes = calc_serial(name_md2)
    
    return serial_bytes.hex().upper()[:20]



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
