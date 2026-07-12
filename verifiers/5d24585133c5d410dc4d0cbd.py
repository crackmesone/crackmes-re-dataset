# Keygen for keygenme (kawaii-flesh)
#
# Algorithm (from disassembly):
#   argv[0] = program path (e.g. "./keygenme")
#   argv[1] = name
#   argv[2] = key (integer as string)
#
# acum_input_atoi(name) -> sum of ASCII values of all chars in name
# check: (name_sum ^ (first_char * 3)) << (len(argv[0]) & 0x1f) == key
#
# NOTE: The shift amount depends on len(argv[0]), i.e. the program invocation
# string (e.g. "./keygenme" has length 10).  keygen() below accepts
# program_path so callers can supply the exact string used at runtime.

def _name_sum(name: str) -> int:
    """Sum of ASCII values of all characters in name."""
    return sum(ord(c) for c in name)


def verify(name: str, serial: str, program_path: str = "./keygenme") -> bool:
    """
    Verify a (name, serial) pair.

    Parameters
    ----------
    name         : the username string (argv[1] of the crackme)
    serial       : the key string (argv[2] of the crackme), as a decimal integer string
    program_path : the string used as argv[0] when running the crackme
                   (default "./keygenme" which has length 10)
    """
    if not name:
        return False
    try:
        key = int(serial)
    except ValueError:
        return False

    name_sum   = _name_sum(name)
    first_char = ord(name[0])
    prog_len   = len(program_path)          # strlen(*argv) in C
    shift      = prog_len & 0x1f

    expected = (name_sum ^ (first_char * 3)) << shift
    return expected == key


def keygen(name: str, program_path: str = "./keygenme") -> str:
    """
    Generate the valid serial for the given name.

    Parameters
    ----------
    name         : the username string
    program_path : the string that will be argv[0] at runtime
                   (e.g. "./keygenme" -> length 10)

    Returns the serial as a decimal integer string.
    """
    if not name:
        raise ValueError("name must be non-empty")

    name_sum   = _name_sum(name)
    first_char = ord(name[0])
    prog_len   = len(program_path)
    shift      = prog_len & 0x1f

    key = (name_sum ^ (first_char * 3)) << shift
    return str(key)


# ---------------------------------------------------------------------------
# Quick self-test / demo
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
