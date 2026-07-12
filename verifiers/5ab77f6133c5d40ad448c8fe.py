# Keygen for scarabee's KeyGenMe#1
# Based on the solution writeup by crackmes.de user
#
# Algorithm (from writeup):
# 1. Reverse the username
# 2. For each character in reversed name:
#    partial = asc(char) * rnd_val * len(name)
#    serial_sum += partial
# 3. serial_sum / rnd_val  (FPU division step from writeup)
#    Wait - re-reading more carefully:
#    The loop does: sum += asc(char) * rnd_val * len(name)
#    Then after loop: result = sum / rnd_val  (fdiv step)
#    Which simplifies to: result = sum(asc(c) for c in reversed_name) * len(name)
#    But we keep the rnd_val variants since the writeup says rnd_val in {1,2,3}
#
# ASSUMPTION: The exact FPU arithmetic and integer truncation behavior is approximated here.
# ASSUMPTION: rnd_val is one of {1, 2, 3} as stated in the writeup.
# ASSUMPTION: The serial is compared as a floating-point number converted to string.
# ASSUMPTION: The division step divides the accumulated sum by rnd_val (not by something else).
# ASSUMPTION: 'imul eax, edx' where eax=length and edx=asc*rnd_val means partial = asc(char)*rnd_val*length
#             then sum += partial, then final_result = sum / rnd_val
#             => final_result = sum(asc(c) * length for c in reversed_name)
#             => final_result = length * sum(asc(c) for c in reversed_name)  (rnd_val cancels)
# But since the writeup says rnd_val matters (3 serials), the division might not fully cancel.
# Let's keep rnd_val explicit and generate all 3 candidates.

def _compute_serial(name: str, rnd_val: int) -> str:
    """
    Compute serial for a given name and rnd_val (1, 2, or 3).
    Based on writeup assembly:
      reversed_name = reverse(name)
      total = 0
      for each char in reversed_name:
          partial = asc(char) * rnd_val   # imul edx, ebx  (edx=rnd_val, ebx=asc)
          partial = partial * len(name)   # imul eax, edx  (eax=len)
          total += partial                # add eax, edx (where edx is running total)
      serial = total / rnd_val           # fdiv step
    Simplifies to: serial = sum(ord(c) for c in name) * len(name)
    BUT keeping rnd_val in case the simplification is wrong or truncation differs.
    """
    reversed_name = name[::-1]
    n = len(name)
    total = 0
    for ch in reversed_name:
        partial = ord(ch) * rnd_val  # imul edx, ebx
        partial = partial * n        # imul eax, edx  (eax held len of name)
        total += partial
    # FPU division step: fdiv by rnd_val
    result = total / rnd_val
    # ASSUMPTION: serial is the integer part represented as a string (or float string)
    # The writeup says fcomp is used, so it's a float comparison after converting serial string
    # We'll return as integer string if it's whole, else float string
    if result == int(result):
        return str(int(result))
    else:
        return str(result)


def keygen(name: str):
    """
    Generate up to 3 candidate serials (for rnd_val in {1, 2, 3}).
    The writeup states one of these will work.
    Returns list of candidate serials.
    """
    candidates = []
    for rnd_val in [1, 2, 3]:
        s = _compute_serial(name, rnd_val)
        if s not in candidates:
            candidates.append(s)
    return candidates


def verify(name: str, serial: str) -> bool:
    """
    Check if serial matches any of the 3 candidate serials for name.
    ASSUMPTION: comparison is done as float (fcomp in assembly).
    """
    try:
        serial_float = float(serial)
    except ValueError:
        return False
    for rnd_val in [1, 2, 3]:
        s = _compute_serial(name, rnd_val)
        try:
            if float(s) == serial_float:
                return True
        except ValueError:
            pass
    return False



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
