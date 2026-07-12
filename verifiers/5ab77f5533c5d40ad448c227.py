#!/usr/bin/env python3
"""
Terminator crackme by kkr_we_rule
Merkle-Hellman knapsack based serial generation/verification.

The crackme:
- Takes an ID (alphanumeric, lowercased internally)
- Generates serial by MerkleHellman_Encrypt(lowercase(ID))
- On verify: MerkleHellman_Decrypt(serial) should equal lowercase(ID)

Constants from the source:
  Beta (public key): [295, 592, 301, 14, 28, 353, 120, 236]  (indices 1..8)
  W    (superincreasing sequence): [2, 7, 11, 21, 42, 89, 180, 354]  (indices 1..8)
  Q = 881  (modulus)
  R = 588  (multiplier used in encrypt, not directly needed for verify)
  S = 442  (= R^-1 mod Q, used in decrypt)
"""

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BETA = [295, 592, 301, 14, 28, 353, 120, 236]   # public key (length 8)
W    = [2,   7,  11, 21, 42, 89, 180, 354]       # superincreasing sequence
Q    = 881   # modulus
R    = 588   # multiplier (used in encrypt: cipher = sum(bit_i * beta_i), beta_i = r*w_i mod q)
S    = 442   # S = R^-1 mod Q  (588^-1 mod 881 = 442)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _char_to_bits(ch: str) -> list:
    """Convert a single character to a list of 8 bits, MSB first."""
    val = ord(ch)
    bits = []
    for i in range(7, -1, -1):
        bits.append((val >> i) & 1)
    return bits  # bits[0] = MSB, bits[7] = LSB


def _pad4(s: str) -> str:
    """Zero-pad a decimal string to length 4."""
    while len(s) < 4:
        s = '0' + s
    return s


def _bits_to_char(bits: list) -> str:
    """Convert a list of 8 bits (MSB first) to a character."""
    val = 0
    for b in bits:
        val = (val << 1) | b
    return chr(val)


# ---------------------------------------------------------------------------
# Encrypt  (ID -> Serial)
# ---------------------------------------------------------------------------

def merkle_hellman_encrypt(plaintext: str) -> str:
    """
    For each character:
      1. Convert to 8 bits (MSB first, matching Delphi ConvertBase256to2)
      2. compute sum = sum(bit_j * Beta[j])  for j in 0..7
      3. zero-pad the decimal sum to 4 digits
    Concatenate all 4-char groups.
    """
    ciphertext = ''
    for ch in plaintext:
        bits = _char_to_bits(ch)
        s = sum(bits[j] * BETA[j] for j in range(8))
        ciphertext += _pad4(str(s))
    return ciphertext


# ---------------------------------------------------------------------------
# Decrypt  (Serial -> plaintext)
# ---------------------------------------------------------------------------

def merkle_hellman_decrypt(serial: str) -> str:
    """
    For each 4-character block:
      1. Parse as integer
      2. Multiply by S mod Q  (i.e. val * 442 mod 881)
      3. Greedy decode against W (superincreasing sequence, index 7 down to 0)
      4. Build 8-bit binary string, convert to character
    Concatenate all characters.
    """
    final_message = ''
    i = 0
    n = len(serial)
    while i < n:
        block = serial[i:i+4]
        i += 4
        if not block:
            break

        val = int(block)
        # mat * S mod Q
        val = (val * S) % Q

        # Greedy decode: find which W elements sum to val
        # The Delphi code iterates j from 7 down to 0 (W[j+1] in 1-based = W[j] in 0-based)
        binary_array = [0] * 8
        j = 7  # 0-based index, corresponds to Delphi j starting at 7 (W[j+1] = W[8..1])
        # ASSUMPTION: The greedy loop stops when val==0; any remaining bits are 0
        while val > 0 and j >= 0:
            if val >= W[j]:
                binary_array[j] = 1
                val -= W[j]
            j -= 1

        # Build binary string: binary_array[0..7] in order
        binary_message = ''.join(str(binary_array[k]) for k in range(8))

        # Convert binary string back to character (MSB = binary_message[0])
        char_val = int(binary_message, 2)
        final_message += chr(char_val)

        if i >= len(serial):
            break

    return final_message


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def keygen(name: str) -> str:
    """
    Generate a serial for the given name/ID.
    The crackme lowercases the ID before encrypting.
    The ID must be alphanumeric; the crackme validates this.
    """
    # Validate: only alphanumeric
    for ch in name:
        if not (ch.isalpha() or ch.isdigit()):
            raise ValueError(f'Invalid character in ID: {ch!r}')
    return merkle_hellman_encrypt(name.lower())


def verify(name: str, serial: str) -> bool:
    """
    Returns True if serial decrypts back to lowercase(name).
    Mimics the crackme check: Decrypt(serial) == lowercase(ID).
    """
    # Serial must be a multiple of 4 decimal digits
    if len(serial) == 0 or len(serial) % 4 != 0:
        return False
    if not serial.isdigit():
        return False
    try:
        decrypted = merkle_hellman_decrypt(serial)
    except Exception:
        return False
    return decrypted == name.lower()


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------


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
