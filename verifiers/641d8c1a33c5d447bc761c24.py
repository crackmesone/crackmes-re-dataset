import random

def _apply_changer(inp):
    """
    The 'changer' function:
    1. Checks inp[0] == 'G' and inp[18] == 'G'
    2. Swaps: output[0]=inp[4], output[18]=inp[14]
    3. Sets output[4]='-', output[14]='-'
    4. Everything else stays the same
    """
    buf = list(inp)
    # Initial check
    if buf[0] != 'G' or buf[18] != 'G':
        return None
    # Save source chars
    c4 = buf[4]
    c14 = buf[14]
    # Write to destination
    buf[0] = c4
    buf[18] = c14
    # Overwrite with hyphens
    buf[4] = '-'
    buf[14] = '-'
    return buf


def _validate_transformed(buf):
    """
    Validates the transformed buffer.
    Checks four 4-byte chunks at offsets 0, 5, 10, 15.
    Within each chunk, abs(buf[i+1] - buf[i]) must equal 5 for i in 0..2.
    """
    chunk_starts = [0, 5, 10, 15]
    for start in chunk_starts:
        for i in range(3):
            diff = abs(ord(buf[start + i + 1]) - ord(buf[start + i]))
            if diff != 5:
                return False
    return True


def verify(name, serial):
    """
    Verify a serial/password.
    The name parameter is not used by this crackme (serial-only check).
    Returns True if the serial is valid.
    """
    if len(serial) != 19:
        return False
    buf = _apply_changer(list(serial))
    if buf is None:
        return False
    return _validate_transformed(buf)


def _decrypt_code(buf):
    """
    The final 'code' is produced by subtracting 3 from each non-hyphen character.
    """
    result = []
    for ch in buf:
        if ch == '-':
            result.append('-')
        else:
            result.append(chr(ord(ch) - 3))
    return ''.join(result)


def keygen(name):
    """
    Generate a valid serial. The name parameter is ignored (no name-based check).
    Strategy:
      - Build the 19-char 'output' (transformed) buffer with valid chunks.
      - Chunks at offsets 0,5,10,15 each have 4 chars with abs-diff==5.
      - output[4] and output[14] are '-'.
      - Reverse the changer transform to get the password:
          password[0] = 'G'
          password[18] = 'G'
          password[4] = output[0]
          password[14] = output[18]
          password[i] = output[i] for all other i
    """
    # ASSUMPTION: characters are kept in printable ASCII range (33..125)
    for _ in range(10000):
        output = [0] * 19
        chunk_starts = [0, 5, 10, 15]
        valid = True

        for start in chunk_starts:
            current_char = random.randint(65, 90)
            direction = random.choice([-5, 5])
            chunk = []
            ok = True
            for i in range(4):
                # Check that current_char + direction stays in printable range
                if not (32 < current_char < 126):
                    ok = False
                    break
                chunk.append(current_char)
                next_char = current_char + direction
                if not (32 < next_char < 126):
                    direction *= -1
                current_char += direction
            if not ok or len(chunk) < 4:
                valid = False
                break
            for i in range(4):
                output[start + i] = chunk[i]

        if not valid:
            continue

        # Fix mandatory hyphens at positions 4 and 14
        output[4] = ord('-')
        output[14] = ord('-')

        # Fill any remaining zeros (positions that overlap chunk boundaries or gaps)
        # The 19 positions: chunks cover 0-3, 4(hyphen), 5-8, 9(?), 10-13, 14(hyphen), 15-18
        # Position 9 is not covered by any chunk_start range
        # ASSUMPTION: position 9 is not validated, fill with a printable char
        for i in range(19):
            if output[i] == 0:
                output[i] = ord('X')

        # Reverse the changer transform to get the password
        password = list(output)  # copy
        password[0] = ord('G')
        password[18] = ord('G')
        password[4] = output[0]   # changer sets output[0]=inp[4], so inp[4]=output[0]
        password[14] = output[18] # changer sets output[18]=inp[14], so inp[14]=output[18]
        # All other positions: password[i] = output[i]

        serial = ''.join(chr(c) for c in password)

        # Verify before returning
        if verify(name, serial):
            return serial

    # Fallback deterministic valid serial
    # Build a simple valid output manually
    # chunk 0-3: G(71),L(76),G(71),L(76) -> diffs: 5,5,5 abs ok? |76-71|=5 yes
    # chunk 5-8: G,L,G,L
    # chunk 10-13: G,L,G,L
    # chunk 15-18: G,L,G,L
    base = ord('G')
    output = [0]*19
    for start in [0,5,10,15]:
        for i in range(4):
            output[start+i] = base + (5 * (i % 2))
    output[4] = ord('-')
    output[9] = ord('X')
    output[14] = ord('-')
    password = list(output)
    password[0] = ord('G')
    password[18] = ord('G')
    password[4] = output[0]
    password[14] = output[18]
    serial = ''.join(chr(c) for c in password)
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
