# Reconstructed algorithm for Guild Hall Adventure Ch.2
# Based on solution writeups
#
# The crackme has two main checks:
#
# CHECK 1 (main function / step1):
#   argv[1] must satisfy: len(argv[1]) - 1 == ord(argv[1][0]) - 0x30
#   i.e. the first character digit value equals the remaining length
#   Examples: '0', '1a', '2aa', '3aaa', etc.
#
# CHECK 2 (step2 function):
#   A math question is displayed: "what's X + 3 * 5 ?"
#   The user must answer with: ord(argv[1][0]) + 0x0f
#   (The displayed arithmetic expression is a red herring / flavor text)
#   The check is: var_14h == scanf_input
#   where var_14h = ord(argv[1][0]) + 0x0f
#
# SUCCESS output includes a segfault triggered intentionally.

def verify(name, serial):
    """
    name  = argv[1] (the name/key passed as command-line argument)
    serial = the numeric answer entered at the math prompt (as int or str)
    
    Returns True if both checks pass.
    """
    if not name or len(name) == 0:
        return False

    # CHECK 1: first char digit value == len(name) - 1
    first_char = name[0]
    try:
        first_digit = ord(first_char) - 0x30  # subtract ASCII '0'
    except Exception:
        return False

    remaining_length = len(name) - 1
    if remaining_length != first_digit:
        return False

    # CHECK 2: serial == ord(first_char) + 0x0f
    expected_answer = ord(first_char) + 0x0f
    try:
        answer = int(serial)
    except (ValueError, TypeError):
        return False

    if answer != expected_answer:
        return False

    return True


def keygen(name=None):
    """
    Generate a valid (name, serial) pair.
    If name is provided, compute its serial (if it satisfies check1).
    Otherwise generate a canonical valid pair.
    """
    if name is not None:
        # Validate check1 and compute serial
        if not name:
            raise ValueError("name cannot be empty")
        first_char = name[0]
        first_digit = ord(first_char) - 0x30
        remaining_length = len(name) - 1
        if remaining_length != first_digit:
            raise ValueError(
                f"name '{name}' does not satisfy check1: "
                f"len(name)-1={remaining_length} != ord(first_char)-0x30={first_digit}"
            )
        serial = ord(first_char) + 0x0f
        return str(serial)
    else:
        # Generate a canonical valid pair: name='1k', serial=64
        # '1' -> digit=1, so name must be 2 chars total -> '1k'
        # serial = ord('1') + 0x0f = 0x31 + 0x0f = 0x40 = 64
        canonical_name = '1k'
        canonical_serial = ord('1') + 0x0f  # 64
        return canonical_name, str(canonical_serial)



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
            print(_sv)
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
