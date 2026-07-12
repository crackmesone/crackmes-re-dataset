import math
import struct

# NOTE: The algorithm for serial 1 (p1) has a known-unfixable gap:
# The third loop reads memory BEYOND the name buffer (name[strlen(name)+strlen(comp)] down to name[2]),
# which contains stack/heap garbage that is non-deterministic.
# We cannot replicate this in Python without knowing the actual runtime stack layout.
# The rest (p2 and p3) can be implemented faithfully.

def _p1(name: str, comp: str, extra_bytes: bytes = None) -> tuple:
    """
    Compute serial 1 value.
    extra_bytes: if provided, used for the 'random' bytes beyond the name buffer.
                 Should be (strlen(name)+strlen(comp)-2) bytes long (indices from
                 strlen(name)+strlen(comp) down to 2).
    Returns (serial1_string, float_value)
    """
    name_b = name.encode('latin-1')
    comp_b = comp.encode('latin-1')
    n_len = len(name_b)
    c_len = len(comp_b)

    s1 = 0.0
    for i in range(n_len):
        ch = name_b[i]
        s1 += (ch ^ n_len) % ch

    s2 = 0.0
    for i in range(c_len):
        ch = comp_b[i]
        s2 += (ch ^ c_len) % ch

    # ASSUMPTION: The third loop reads bytes beyond the name string.
    # These bytes are random stack data. We use extra_bytes if provided,
    # otherwise we assume zeros (which will give wrong serials in practice).
    s3 = 0.0
    start_i = n_len + c_len
    if extra_bytes is None:
        # ASSUMPTION: treat unknown bytes as 0
        for i in range(start_i, 1, -1):
            s3 += 0 ^ (c_len & 0xFF)  # name[i] is unknown, assume 0
    else:
        # extra_bytes covers indices n_len .. n_len+c_len (i goes from start_i down to 2)
        # total iterations: start_i - 1 = n_len + c_len - 1
        # index i: start_i, start_i-1, ..., 2
        # offset into extra_bytes: start_i - i (0-based)
        for idx, i in enumerate(range(start_i, 1, -1)):
            if idx < len(extra_bytes):
                byte_val = extra_bytes[idx]
            else:
                byte_val = 0
            # sign-extend as char
            if byte_val > 127:
                byte_val -= 256
            c_len_char = c_len & 0xFF
            if c_len_char > 127:
                c_len_char -= 256
            s3 += byte_val ^ c_len_char

    a = math.sqrt(s1) if s1 >= 0 else 0.0
    if s2 != 0:
        d_tmp = s3 / s2
    else:
        d_tmp = 0.0
    b = math.atan(d_tmp)
    c = s1 * s2
    d = a * b * c

    serial1 = "{:f}.{:f}".format(d, 0.0)
    return serial1, d


def _p2(comp: str, serial1: str) -> tuple:
    """
    Compute serial 2 value using company and serial1 string.
    Returns (serial2_string, float_value)
    """
    comp_b = comp.encode('latin-1')
    c_len = len(comp_b)
    seri_b = serial1.encode('latin-1')

    s1 = 0
    for i in range(c_len):
        s1 += comp_b[i] ^ c_len

    s2 = 0
    for i in range(c_len, 1, -1):  # i from c_len down to 2
        # comp[i] - reads beyond comp buffer: assume 0
        # ASSUMPTION: bytes beyond comp string are 0
        byte_val = 0
        s2 += byte_val ^ c_len

    s3 = 0
    for i in range(len(seri_b)):
        s3 += seri_b[i] ^ (s1 & 0xFF)

    s4 = 0
    for i in range(len(seri_b)):
        s4 += seri_b[i] ^ (s2 & 0xFF)

    x = float(s3 * s4)

    serial2 = "{:4.4f}.{:4.4f}".format(x, 0.0)
    return serial2, x


def _p3(a: float, b: float) -> str:
    """
    Compute serial 3.
    The constant -1713714.0 comes from _Z10NerveAgentv and is described as static.
    """
    # ASSUMPTION: The NerveAgent return value is always -1713714.0 (described as static in writeup)
    c = -1713714.0
    return "{:4.4f}".format(a + b + c)


def verify(name: str, serial: str) -> bool:
    """
    Cannot fully verify without the runtime stack data for the s3 loop in p1.
    This function computes the expected serials with assumed-zero extra bytes
    and checks if the provided serial matches serial3 (most deterministic part).
    For a real verify, all three serials would need to match.
    """
    # ASSUMPTION: extra_bytes for the random region are zero
    s1_str, s1_val = _p1(name, "", extra_bytes=None)
    # We need company to verify - serial here means serial3 for demonstration
    # Real crackme takes name + company -> 3 serials
    # This function is a placeholder showing the structure
    return False  # Cannot fully verify without company and runtime data


def generate_serials(name: str, comp: str, extra_bytes: bytes = None):
    """
    Generate all three serials for the given name, company, and optional extra_bytes.
    extra_bytes: the random stack bytes beyond the name buffer (n_len+c_len-1 bytes needed).
                 If None, zeros are assumed (INCORRECT in practice).
    Returns (serial1, serial2, serial3)
    """
    s1_str, s1_val = _p1(name, comp, extra_bytes=extra_bytes)
    s2_str, s2_val = _p2(comp, s1_str)
    s3_str = _p3(s1_val, s2_val)
    return s1_str, s2_str, s3_str


def keygen(name: str, comp: str = "Company"):
    """
    Attempt to generate serials. Due to the random stack bytes in p1,
    this will produce incorrect serial1 (and cascading incorrect serial2/3)
    unless the actual extra_bytes are provided.
    """
    # ASSUMPTION: extra_bytes are zero - THIS WILL BE WRONG AT RUNTIME
    s1, s2, s3 = generate_serials(name, comp, extra_bytes=None)
    return s1, s2, s3



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
