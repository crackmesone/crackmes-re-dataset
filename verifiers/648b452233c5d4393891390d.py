def verify(name: str, serial: str) -> bool:
    return serial == keygen(name)


def keygen(name: str) -> str:
    """
    Reconstruct the serial for a given name.

    Algorithm (from both solutions):
      1. Iterate over each character of the name (NOT uppercased per sa2304's
         pseudocode, but the VB6 trace shows UCase is applied; both solutions
         agree on UCase).
      2. For each character c (uppercased):
             accum += ord(c) * 0x1749   # 0x1749 == 5961
             hash_val = accum - len(name)
      3. Serial = "Zitto - " + str(hash_val)

    Notes:
      - The multiplier 5961 == 0x1749 is confirmed by both solutions.
      - The name length subtraction happens inside the loop but only the
        final value of hash_val matters (per sa2304 pseudocode).
      - The prefix is "Zitto - " (with spaces around the dash).
        The VB6 decompiler output shows "Zitto-" (no spaces), but the
        comment example 'j4brik -> Zitto - 2515536' and sa2304 both use
        "Zitto - " with spaces.
    """
    # ASSUMPTION: UCase is applied to each character before processing
    # (confirmed by VB6 trace showing UCase in the loop).
    name_upper = name.upper()
    accum = 0
    hash_val = 0
    name_len = len(name_upper)
    for c in name_upper:
        accum += ord(c) * 5961  # 5961 == 0x1749
        hash_val = accum - name_len
    return f"Zitto - {hash_val}"


def _verify_examples():
    """Verify against known good examples from the comments/solutions."""
    examples = [
        ("j4brik", "Zitto - 2515536"),
        ("USERNAME", "Zitto - 3624280"),
        ("sa2304", "Zitto - 2080383"),
        ("A REALLY LONG NAME", "Zitto - 7218753"),
    ]
    for name, expected in examples:
        result = keygen(name)
        status = "OK" if result == expected else f"FAIL (got {result})"
        print(f"  name={name!r:25s}  expected={expected!r:30s}  {status}")



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
