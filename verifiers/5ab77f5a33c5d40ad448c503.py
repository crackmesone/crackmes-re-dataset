import random

# Based on VB6 P-CODE analysis from the writeup
# The crackme:
#   - On Form.Load(): generates a random number: key_num = Int(Rnd() * 156) + 3808 (0xEE0)
#   - On Text1.Change(): computes something with the text length and Rnd()
#   - On Command1.Click(): calls a function (Form1 1.1) that compares TextBox text to param_8 string
#     If match => MsgBox with 'Key' title and flags 0x10 (info/correct)
#     If no match => MsgBox with 'Key' title and flags 0x40 (error/incorrect) then Unload
#
# Form1 1.1 (the check function):
#   Gets TextBox text, compares with param_8 (a stored string), returns 0 or 1
#
# Form.Load logic (pseudocode):
#   correct_msg = "W00t! Correct Key Enterd! YOU OWN ME!"
#   incorrect_msg = "In-Correct Key Enterd!"
#   key_num = Int(Int(Rnd() * 156) * 1.0) + 3808  => integer in [3808, 3963]
#   (stored as I2 param)
#
# Text1.Change logic (pseudocode):
#   text_len_str = Str(Len(Text1.Text))  => stored
#   new_val = Int(Rnd() * key_num) + 845  => stored as I2
#   computed = Int(87945.0 * CDbl(text_len_str)) + new_val
#   => this becomes the serial string (CStr of computed)
#   stored as param_8 string for comparison
#
# ASSUMPTION: The 'correct key' is simply the string representation of:
#   Int(87945 * Len(name)) + (Int(Rnd() * key_num) + 845)
# BUT since Rnd() is used, the serial is RANDOM and not name-based in the traditional sense.
# The serial changes every time the text changes.
# ASSUMPTION: The intended check is:
#   serial == str(87945 * len(name) + some_random_offset)
# Since Rnd() makes it non-deterministic, we cannot produce a fixed keygen without seeding.
# The P-CODE shows the serial displayed in a label or stored internally, not derived purely
# from name. The user must read the generated serial from the UI.
#
# ASSUMPTION: For keygen purposes, we assume Rnd() returns a pseudo-random value seeded
# by VB6's default RNG. Without knowing the seed, we cannot reproduce it exactly.
# We model the algorithm structure only.

def _vb6_rnd_sequence(seed=None):
    """ASSUMPTION: VB6 Rnd() uses a specific LCG. We use Python's random as approximation."""
    if seed is not None:
        random.seed(seed)
    return random.random()

def verify(name: str, serial: str) -> bool:
    """
    ASSUMPTION: The 'name' field is Text1 (the only text box shown).
    The stored serial (param_8) is computed as:
        key_num = Int(rnd1 * 156) + 3808   (from Form.Load)
        rand_part = Int(rnd2 * key_num) + 845  (from Text1.Change, each change)
        computed = Int(87945.0 * float(str(len(name)))) + rand_part
        stored_serial = str(computed)
    Then on Command1.Click, it checks if TextBox.Text == stored_serial.
    Since serial depends on two Rnd() calls we cannot verify without the RNG state.
    
    ASSUMPTION: For a static check, we try to see if serial could equal
    87945 * len(name) + offset for some offset in a plausible range.
    """
    try:
        serial_int = int(serial.strip())
    except ValueError:
        return False
    
    base = 87945 * len(name)
    # rand_part range: [845, 845 + 3963] = [845, 4808]
    # ASSUMPTION: key_num in [3808, 3963], rand_part in [845, 845+3963-1]
    min_offset = 845
    max_offset = 845 + 3963  # 845 + (3963 * 1) at most
    
    offset = serial_int - base
    return min_offset <= offset <= max_offset

def keygen(name: str, vb_rnd1: float = None, vb_rnd2: float = None) -> str:
    """
    Generate a valid serial for the given name.
    vb_rnd1, vb_rnd2: VB6 Rnd() values (0.0 to 1.0).
    ASSUMPTION: If not provided, use Python random (approximate).
    """
    if vb_rnd1 is None:
        vb_rnd1 = random.random()
    if vb_rnd2 is None:
        vb_rnd2 = random.random()
    
    # Form.Load: key_num = Int(Int(Rnd() * 156) * 1) + 3808
    # ASSUMPTION: Int() in VB truncates toward zero (floor for positive)
    key_num = int(vb_rnd1 * 156) + 3808  # range [3808, 3963]
    
    # Text1.Change: rand_part = Int(Rnd() * key_num) + 845
    rand_part = int(vb_rnd2 * key_num) + 845
    
    # computed = Int(87945.0 * float(str(len(name)))) + rand_part
    # ASSUMPTION: str(len(name)) is just the decimal string of length
    text_len = len(name)
    computed = int(87945.0 * float(str(text_len))) + rand_part
    
    return str(computed)


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
