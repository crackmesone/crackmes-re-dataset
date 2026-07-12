# Reverse-engineered keygen for dhack.crackme7.0
# Based on Cronos solution writeup
#
# Algorithm summary (per writeup):
#   For each character in name[1:] (starting from 2nd char):
#     N = cumulative sum of ord(char) for chars seen so far (from index 1)
#     serial_so_far = N*2 + N + 6541 + 666 + 666 + 666 + prev_serial_value
#       where prev_serial_value starts at 0
#     then: temp = N - serial_so_far + 12189
#     then: serial_so_far += 335
#     then: serial_so_far *= 3  (ASSUMPTION: truncated writeup, multiplied by magic value 3)
#   Final serial is the last computed value
#
# NOTE: The writeup was truncated and several steps near the end are unclear.
# The reconstruction below is the best estimate from the available text.
# Gaps are marked with # ASSUMPTION comments.

def compute_serial(name: str) -> int:
    """
    Compute the serial number for the given name.
    Returns the integer serial value.
    """
    if len(name) < 2:
        # ASSUMPTION: name must be at least 2 characters; behavior for shorter names unknown
        return 0

    cumulative_n = 0
    prev_serial = 0  # value carried from previous loop iteration

    serial = 0

    for i in range(1, len(name)):  # start from index 1 (second character)
        char_val = ord(name[i])
        cumulative_n += char_val  # cumulative sum of ascii values from char[1] onward

        N = cumulative_n

        # From writeup:
        # N*2  (N added to itself)
        step1 = N * 2

        # + N + 6541 (198dh)
        # ASSUMPTION: the 'N+198dh' step adds current N to step1 result, giving N*2 + N = N*3, then +6541
        # But re-reading: "N+198dh" and "adds 666 three times" and "adds prev loop value"
        # The sequence is: (N+N) then (result + 6541) then (+666) then (+666) then (+666) then (+prev)
        step2 = step1 + 6541       # N*2 + 6541
        step3 = step2 + 666        # + 666
        step4 = step3 + 666        # + 666
        step5 = step4 + 666        # + 666
        step6 = step5 + prev_serial  # + value from previous loop

        serial_so_far = step6

        # Then: temp = N - serial_so_far + 12189  (2f9dh)
        temp = N - serial_so_far + 12189
        # ASSUMPTION: temp seems unused per writeup ("why? don't ask me, it seems to be unused")
        # So serial_so_far remains step6

        # Then: serial_so_far += 335 (14fh)
        serial_so_far += 335

        # Then multiply by 3 (magic value 3 mentioned)
        # ASSUMPTION: the truncated writeup shows magic value 3; multiply
        serial_so_far *= 3

        prev_serial = serial_so_far
        serial = serial_so_far

    return serial


def verify(name: str, serial: str) -> bool:
    """
    Verify that the given serial matches the expected serial for name.
    """
    try:
        serial_int = int(serial)
    except ValueError:
        return False
    expected = compute_serial(name)
    return serial_int == expected


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    """
    return str(compute_serial(name))



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
