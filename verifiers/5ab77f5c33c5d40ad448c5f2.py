import random

def verify(name: str, serial: str) -> bool:
    """
    Reconstruct the crackme validation from the disassembly writeup.

    Checks:
    1. Name length must be 8-12 chars.
    2. Serial must be exactly 12 chars.
    3. First 12 chars of Name != First 12 chars of Serial (they must differ).
    4. The core hash loop must yield variable == 0.

    Core algorithm (from disassembly at 401147-401182):
      variable = 0
      repeat:
        edx = 0
        for ecx from 12 down to 1:
            dl += Name[ecx-1]
            dl ^= Serial[ecx-1]
            edx = ROR(edx, 8)
        variable += edx
        eax = edx << 2   (SHL 2 = multiply by 4, but disasm says SHL 2 = *4)
        variable += eax
        if variable > 0x100: repeat
      until variable <= 0x100
      if variable != 0: badboy  else: goodboy

    ASSUMPTION: 'variable' is reset each outer loop iteration (the loop repeats
    until variable <= 0x100, then checks if it equals 0). Since the loop
    reruns until variable <= 0x100, a valid serial must produce variable == 0
    after the loop terminates. The loop variable [40309C] appears to accumulate
    across iterations (ADD, not MOV), so we accumulate.

    ASSUMPTION: name and serial are padded/truncated to exactly 12 chars for
    the loop (name may be shorter than 12, padded with 0 bytes implicitly).
    """
    # Basic length checks
    # ASSUMPTION: name length 8-12 per disassembly ("8-12 letters")
    name_len = len(name)
    if name_len < 8 or name_len > 12:
        return False
    if len(serial) != 12:
        return False

    # Pad name to 12 chars with null bytes for loop
    name12 = (name + '\x00' * 12)[:12]
    serial12 = serial[:12]

    # Check name != serial (first 12 bytes must differ)
    if name12 == serial12:
        return False

    def ror32(val, n):
        val = val & 0xFFFFFFFF
        return ((val >> n) | (val << (32 - n))) & 0xFFFFFFFF

    variable = 0
    max_iters = 10000  # safety
    iters = 0
    while iters < max_iters:
        iters += 1
        edx = 0
        for ecx in range(12, 0, -1):  # ecx from 12 down to 1
            # dl += Name[ecx-1]
            dl = edx & 0xFF
            dl = (dl + ord(name12[ecx - 1])) & 0xFF
            # dl ^= Serial[ecx-1]
            dl = dl ^ ord(serial12[ecx - 1])
            # write dl back into edx low byte
            edx = (edx & 0xFFFFFF00) | dl
            # ROR edx, 8
            edx = ror32(edx, 8)
        # variable += edx
        variable = (variable + edx) & 0xFFFFFFFF
        # eax = edx << 2
        eax = (edx << 2) & 0xFFFFFFFF
        # variable += eax
        variable = (variable + eax) & 0xFFFFFFFF
        if variable <= 0x100:
            break

    return variable == 0


def keygen(name: str) -> str:
    """
    Generate a valid serial for a given name using the KeyGen.cpp algorithm.

    Algorithm from KeyGen.cpp:
    1. serial = name (copy, use first 12 chars)
    2. Repeat until serial != name:
       For i from 11 down to 4:
           char_before = serial[i]
           char_after = char_before + (rand() & 0xF)
           if char_after > ord('z'): char_after -= 0x5B
           to_add = char_before ^ char_after
           added = serial[i-4] + to_add
           if added < ord(' ') or added > ord('z'): continue
           serial[i-4] = chr(added)
           serial[i] = chr(char_after)
    3. Return serial (12 chars)

    ASSUMPTION: Name must be exactly 12 chars; if shorter, pad with spaces.
    The keygen truncates/pads to 12 chars.
    """
    if len(name) < 8:
        raise ValueError("Name must be at least 8 characters")

    # Pad or truncate to 12 chars
    name12 = (name + ' ' * 12)[:12]
    serial = list(name12)

    max_attempts = 100000
    attempts = 0
    while True:
        attempts += 1
        if attempts > max_attempts:
            raise RuntimeError("keygen failed to find valid serial")

        changed = False
        for i in range(11, 3, -1):  # i from 11 down to 4
            char_before = ord(serial[i])
            rand_val = random.randint(0, 15)
            char_after = (char_before + rand_val) & 0xFF
            if char_after > ord('z'):
                char_after = (char_after - 0x5B) & 0xFF
            to_add = char_before ^ char_after
            added = ord(serial[i - 4]) + to_add
            if added < ord(' ') or added > ord('z'):
                continue
            serial[i - 4] = chr(added)
            serial[i] = chr(char_after)
            changed = True

        result = ''.join(serial)
        if result != name12:
            return result

        # Reset serial and try again
        serial = list(name12)



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
