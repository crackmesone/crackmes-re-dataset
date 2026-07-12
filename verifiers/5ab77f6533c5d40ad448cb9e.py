import hashlib
import struct
import base64

# RSA public parameters from the crackme
E_RSA = 65537
N_RSA = 99653269292501507412524077632659748837049
D_RSA = 85188134318676540751695496866951428507745

# Constants discovered from analysis
BUGGY_BASE64_CONST = "110100110100110100110100110100110100"

# Hidden edit box value (bignum from hex string)
# ASSUMPTION: The hidden edit box contains a fixed value embedded in the binary.
# The large number shown in the writeup is likely derived from a fixed string.
# We use the value shown in the disassembly as a placeholder.
HIDDEN_BIGNUM = 4452178552884313028611408090651415885804801235620065339377288153636180879386205486164665792087289029040873978951208022729329824955576950163068633946737176298855180104453423358221986898030008350878566339638884388877979
MOD_BIGNUM = 642314238026171165685351229032594369597088601595857573337385896404017428545654712173076507380339621428833536337393676521815725981166162391504572697716975141165329833715434408831654671180094549014095920063421918644848731773
EXP2 = 13370


def modified_md5(data: str) -> bytes:
    """
    ASSUMPTION: This is a modified MD5 where some chaining variables (IVs) are changed.
    We do not know the exact IV values, so we approximate with standard MD5.
    A real implementation would require reversing the actual IV constants used.
    """
    # ASSUMPTION: Using standard MD5 as approximation; real crackme uses modified IVs
    m = hashlib.md5()
    if isinstance(data, str):
        data = data.encode('latin-1')
    m.update(data)
    return m.digest()


def convert_hash_to_hex_string(h: bytes) -> str:
    """Convert hash bytes to lowercase hex string."""
    return h.hex()


BUGGY_B64_TABLE = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'

def buggy_base64_encode(s: str) -> str:
    """
    Buggy base64 encode as described in the writeup.
    The bug causes certain characters to be encoded differently.
    
    From the writeup:
    standard: Y2QzZjZjMTc3NjcwNjFkDTdmGzEwDThiDzk1GjI3NGM=
    buggy:    G2QzGjZjDTc3DjcwDjFkDTdmGzEwDThiDzk1GjI3NGM=
    
    Comparing: positions 0,4,8,12,16,20,24,28,32 differ.
    ASSUMPTION: The bug affects the first character of each 4-char output group
    (except possibly the last group). The exact table remapping is unknown.
    We implement standard base64 as approximation.
    """
    # ASSUMPTION: Using standard base64 as we cannot determine exact bug from writeup alone
    if isinstance(s, str):
        data = s.encode('latin-1')
    else:
        data = s
    return base64.b64encode(data).decode('ascii')


def fgint_base64_encode(data: bytes) -> str:
    """
    FGInt library base64 encoding (used by ConvertBase256to64).
    ASSUMPTION: This is standard base64 as used by FGInt library.
    """
    return base64.b64encode(data).decode('ascii')


def rsa_encrypt_string(name: str) -> str:
    """
    RSA 'encrypt' the name string:
    - Convert name to integer (base256)
    - Compute name^D mod N  (note: uses D, not E, so this is actually RSA signing)
    - Convert result to FGInt base64
    """
    # Convert name string to integer (big-endian)
    name_bytes = name.encode('latin-1')
    name_int = int.from_bytes(name_bytes, 'big')
    
    # RSA operation: name^D mod N
    result_int = pow(name_int, D_RSA, N_RSA)
    
    # Convert back to bytes
    result_len = (result_int.bit_length() + 7) // 8
    result_bytes = result_int.to_bytes(result_len, 'big')
    
    # Convert to FGInt base64
    str1 = fgint_base64_encode(result_bytes)
    return str1


def compute_serial(name: str) -> str:
    """
    Compute serial from name following the algorithm in the crackme.
    
    Steps:
    1. RSA encrypt name (name^D mod N), convert to base64 -> str1
    2. Compute modified MD5 of name, convert to hex string
    3. Apply buggy_base64_encode to the hex string
    4. The buggy base64->base2 conversion always returns BUGGY_BASE64_CONST (due to bug)
    5. Concatenate BUGGY_BASE64_CONST + str1
    6. Apply buggy_base64_encode to the concatenation -> str_b64
    7. Compute modified MD5 of str_b64, convert to hex -> str2
    8. [Hidden editbox + more bignum operations - ASSUMPTION: these produce the final serial]
    """
    # Step 1: RSA encrypt name
    str1 = rsa_encrypt_string(name)
    
    # Step 2: Modified MD5 of name -> hex string
    hash1 = modified_md5(name)
    hex1 = convert_hash_to_hex_string(hash1)
    
    # Step 3: buggy base64 encode the hex string
    b64_of_hex = buggy_base64_encode(hex1)
    
    # Step 4: base64->base2 always returns constant due to bug
    base2_str = BUGGY_BASE64_CONST
    
    # Step 5: Concatenate base2_str + str1
    concat = base2_str + str1
    
    # Step 6: buggy base64 encode the concatenation
    str_b64 = buggy_base64_encode(concat)
    
    # Step 7: modified MD5 of str_b64 -> hex -> str2
    hash2 = modified_md5(str_b64)
    str2 = convert_hash_to_hex_string(hash2)
    
    # Steps 8+: The writeup was truncated. The hidden editbox and further bignum
    # operations are not fully described.
    # ASSUMPTION: str2 is the final serial or is further processed.
    # ASSUMPTION: The hidden editbox comparison involves str2 vs some transformation.
    # The writeup mentions bignum3 (MOD_BIGNUM) and exp2=13370 for further RSA ops.
    # Without the full writeup, we return str2 as best guess for the serial.
    return str2


def verify(name: str, serial: str) -> bool:
    """
    Verify name/serial pair.
    ASSUMPTION: The serial is compared against the computed str2 (or some
    transformation of it). The exact comparison is unknown due to truncated writeup.
    """
    # ASSUMPTION: Direct comparison with computed serial
    expected = compute_serial(name)
    return serial == expected


def keygen(name: str) -> str:
    """Generate a serial for the given name."""
    return compute_serial(name)



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
