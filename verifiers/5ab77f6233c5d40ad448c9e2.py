# Reconstruction of philpem's keygenme #1
# Based on TiGa's solution writeup (truncated)
# Many steps are partially described; gaps are marked with # ASSUMPTION:

import random
import string

# The hardcoded constant string from the binary
HARDCODED = "QWMF-KCMV-MRPJKC-MPQZIE"

def char_to_abs(c):
    """Convert a character to its 'absolute' value as described in the writeup."""
    if c == '-':
        return None  # dashes are skipped/kept
    c = c.upper()
    if c.isalpha():
        val = ord(c) - ord('A')
    elif c.isdigit():
        val = ord(c) - ord('0') + 26  # +26 for numbers
    else:
        val = ord(c)
    return val

def process_key_string(s):
    """Process a key string (strip dashes, convert chars to abs values,
    apply modulo 6, then NOT the result).
    This implements the transformation described for both the hardcoded string
    and the entered install key."""
    # ASSUMPTION: The modulo-6 step and NOT step apply to each character after abs conversion
    result = []
    for c in s.upper():
        if c == '-':
            continue  # skip dashes
        v = char_to_abs(c)
        if v is None:
            continue
        # modulo 6
        v = v % 6
        # NOT the value (byte NOT)
        v = (~v) & 0xFF
        result.append(v)
    return result

def strip_dashes(s):
    return [c for c in s.upper() if c != '-' and c != '\n' and c != '\r']

def verify(cdkey, installkey):
    """
    Attempt to verify a CD key / install key pair.
    
    WARNING: The writeup is heavily truncated and many steps are only partially
    described. This is a best-effort reconstruction.
    
    CD key format: XXXX-XXXX-XXXXXX-XXXXXX (alphanumeric + dashes)
    Install key format: same pattern
    """
    # Step 1: Convert to uppercase
    cdkey = cdkey.upper().strip()
    installkey = installkey.upper().strip()

    # ASSUMPTION: Both keys must match the pattern xxxx-xxxx-xxxxxx-xxxxxx
    # (same as the hardcoded string QWMF-KCMV-MRPJKC-MPQZIE)

    # Step 2: Process hardcoded constant -> Key1
    key1 = process_key_string(HARDCODED)
    # key1 has len = len without dashes = 4+4+6+6 = 20 chars

    # Step 3: Process entered install key -> Key2
    key2 = process_key_string(installkey)

    # Step 4: Process CD key chars (strip dashes)
    cdchars = strip_dashes(cdkey)
    # ASSUMPTION: cdkey should have 20 non-dash characters
    if len(cdchars) != 20:
        return False
    if len(key2) != 20:
        return False

    # Step 5: Compute sum counter = sum of all cd key char values (byte)
    counter1 = 0
    for c in cdchars:
        if c.isalpha():
            counter1 += ord(c)
        elif c.isdigit():
            counter1 += ord(c)
    counter1 &= 0xFF

    # Step 6: XOR cd key chars with key1 -> intermediate, then SHL 2
    # ASSUMPTION: element-wise XOR, then shift left 2
    intermediate = []
    for i in range(20):
        v = ord(cdchars[i]) ^ key1[i]
        v = (v << 2) & 0xFF
        # ASSUMPTION: then add cd key char back
        v = (v + ord(cdchars[i])) & 0xFF
        intermediate.append(v)

    # Step 7: XOR key1 with counter1 (except first 2 chars)
    key1_modified = list(key1)
    for i in range(2, len(key1_modified)):
        key1_modified[i] = (key1_modified[i] ^ counter1) & 0xFF

    # Step 8: Process key2 and key1_modified
    # key2: add 237; key1_modified: NOT; key2: subtract 13
    key2_mod = [(237 + v) & 0xFF for v in key2]
    key1_not = [(~v) & 0xFF for v in key1_modified]
    key2_sub = [(v - 13) & 0xFF for v in key2]

    # ASSUMPTION: combine key2_mod, key1_not, key2_sub in some way
    # The writeup says key1 is XORed again with key2:
    combined = [(key2_sub[i] ^ key1_not[i]) & 0xFF for i in range(20)]

    # Step 9: Map combined to readable ASCII
    # and val & 31; if <= 25: add 65 (-> 'A'-'Z'); else: ASSUMPTION add '0'
    expected_chars = []
    for v in combined:
        v = v & 31
        if v <= 25:
            ch = chr(v + 65)  # 'A' to 'Z'
        else:
            # ASSUMPTION: map 26-31 to digits '0'-'5'
            ch = chr(v - 26 + ord('0'))
        expected_chars.append(ch)

    # Step 10: Compare expected_chars with the install key (stripped of dashes)
    installkey_stripped = strip_dashes(installkey)
    if len(installkey_stripped) != 20:
        return False

    # ASSUMPTION: the expected install key chars must match the entered install key chars
    for i in range(20):
        if expected_chars[i] != installkey_stripped[i]:
            return False
    return True


def keygen(cdkey):
    """
    Given a CD key, generate a valid install key.
    
    ASSUMPTION: The install key format is XXXX-XXXX-XXXXXX-XXXXXX
    We compute what the install key chars should be from the algorithm,
    then insert dashes.
    
    NOTE: Because the algorithm is circular (install key is used to compute
    what the install key should be), we must fix a seed for key2 first,
    or we need to solve for it. This is a major gap in the reconstruction.
    """
    # ASSUMPTION: The algorithm may not be circular in the real binary.
    # The install key chars are derived entirely from the CD key and hardcoded string,
    # not from the install key itself. The writeup suggests this direction.
    # We attempt to generate the expected install key chars:

    cdkey = cdkey.upper().strip()
    key1 = process_key_string(HARDCODED)
    cdchars = strip_dashes(cdkey)

    if len(cdchars) != 20:
        raise ValueError("CD key must have 20 non-dash characters (format: XXXX-XXXX-XXXXXX-XXXXXX)")

    counter1 = 0
    for c in cdchars:
        counter1 += ord(c)
    counter1 &= 0xFF

    key1_modified = list(key1)
    for i in range(2, len(key1_modified)):
        key1_modified[i] = (key1_modified[i] ^ counter1) & 0xFF

    key1_not = [(~v) & 0xFF for v in key1_modified]

    # ASSUMPTION: We need to reverse the install key derivation.
    # combined[i] = (key2_sub[i] ^ key1_not[i]) & 0xFF
    # combined[i] = ((v & 31) mapped to char) -- we know expected_chars
    # But we need combined to produce the install key chars after AND 31 mapping.
    # Since install key IS the input, this is circular. We treat it as:
    # The install key is the OUTPUT of the algorithm applied to the CD key.
    # ASSUMPTION: The install key chars ARE expected_chars directly.

    # We can't fully invert without knowing the exact algorithm.
    # Produce a candidate install key by using expected_chars:
    # (This is almost certainly incomplete)
    # For now, produce a fixed key2 = all zeros and compute combined,
    # then the install key IS the combined chars.
    # Actually: if the verify check is that install_key_chars == expected_chars,
    # then the install key is just the expected_chars.

    # But expected_chars depends on key2 which depends on the install key -> circular.
    # ASSUMPTION: key2 is derived from the install key but the final check compares
    # something derived from CD key only against the install key directly.
    # We attempt: treat key2 contribution as zero (all key2 steps cancel or are zero).
    dummy_key2 = [0] * 20
    key2_mod = [(237 + v) & 0xFF for v in dummy_key2]
    key2_sub = [(v - 13) & 0xFF for v in dummy_key2]
    combined = [(key2_sub[i] ^ key1_not[i]) & 0xFF for i in range(20)]

    install_chars = []
    for v in combined:
        v = v & 31
        if v <= 25:
            ch = chr(v + 65)
        else:
            ch = chr(v - 26 + ord('0'))
        install_chars.append(ch)

    # Insert dashes: XXXX-XXXX-XXXXXX-XXXXXX
    raw = ''.join(install_chars)
    install_key = raw[0:4] + '-' + raw[4:8] + '-' + raw[8:14] + '-' + raw[14:20]
    return install_key



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
