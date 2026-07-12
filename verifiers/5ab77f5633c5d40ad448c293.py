# Therapy's Crackme #3 - Combine sliders and checkboxes
# Reverse-engineered from kao's writeup
#
# The crackme has 4 sliders (each 0-8 steps) and 8 checkboxes.
# bx (slider value) and dx (checkbox value) must satisfy: bx + dx == 0xFFFF
#
# Slider calculation:
#   initial value: 0x42AC
#   slider 1 adds +0x0020 per step
#   slider 2 adds +0x0200 per step
#   slider 3 adds +0x0002 per step
#   slider 4 adds +0x2000 per step
#
# Checkbox calculation:
#   initial value: 0x33CC
#   checkbox 1 checked: +0x0030
#   checkbox 2 checked: -0x000C (i.e., +0xFFF4 in 16-bit)
#   checkbox 3 checked: +0x0003
#   checkbox 4 checked: +0xC000
#   checkbox 5 checked: -0x3000 (i.e., +0xD000 in 16-bit)
#   checkbox 6 checked: +0x0C00
#   checkbox 7 checked: -0x0300 (i.e., +0xFD00 in 16-bit)
#   checkbox 8 checked: -0x00C0 (i.e., +0xFF40 in 16-bit)

SLIDER_BASE = 0x42AC
SLIDER_STEPS = [0x0020, 0x0200, 0x0002, 0x2000]

CHECKBOX_BASE = 0x33CC
CHECKBOX_DELTAS = [
    0x0030,   # checkbox 1
   -0x000C,   # checkbox 2
    0x0003,   # checkbox 3
    0xC000,   # checkbox 4 (treated as signed 16-bit: -0x4000, but we use unsigned mod)
   -0x3000,   # checkbox 5
    0x0C00,   # checkbox 6
   -0x0300,   # checkbox 7
   -0x00C0,   # checkbox 8
]

def compute_bx(sliders):
    """sliders: list of 4 integers, each 0..8 (step count for each slider)"""
    val = SLIDER_BASE
    for i, s in enumerate(sliders):
        val += SLIDER_STEPS[i] * s
    return val & 0xFFFF

def compute_dx(checkboxes):
    """checkboxes: list of 8 booleans (True=checked)"""
    val = CHECKBOX_BASE
    for i, checked in enumerate(checkboxes):
        if checked:
            val += CHECKBOX_DELTAS[i]
    return val & 0xFFFF

def verify_values(sliders, checkboxes):
    """Returns True if the combination is valid."""
    bx = compute_bx(sliders)
    dx = compute_dx(checkboxes)
    return (bx + dx) & 0xFFFF == 0xFFFF

def verify(name, serial):
    """
    'name' is unused (no name-based keygen in this crackme).
    'serial' is a dict with keys:
        'sliders': list of 4 ints (0-8 each)
        'checkboxes': list of 8 bools
    Returns True if valid.
    """
    if not isinstance(serial, dict):
        return False
    sliders = serial.get('sliders', [0,0,0,0])
    checkboxes = serial.get('checkboxes', [False]*8)
    return verify_values(sliders, checkboxes)

def keygen(name=None):
    """
    Generates all valid (sliders, checkboxes) combinations.
    Yields dicts with 'sliders' and 'checkboxes' keys.
    Each slider ranges 0..8, each checkbox is True/False.
    """
    # ASSUMPTION: sliders go from 0 to 8 inclusive based on the solutions listed
    import itertools
    for s1, s2, s3, s4 in itertools.product(range(9), repeat=4):
        sliders = [s1, s2, s3, s4]
        bx = compute_bx(sliders)
        # We need dx = (0xFFFF - bx) & 0xFFFF
        target_dx = (0xFFFF - bx) & 0xFFFF
        # Try all checkbox combinations
        for cb_bits in range(256):
            checkboxes = [(cb_bits >> i) & 1 == 1 for i in range(8)]
            dx = compute_dx(checkboxes)
            if dx == target_dx:
                yield {'sliders': sliders, 'checkboxes': checkboxes}

def keygen_first(name=None):
    """Returns the first valid combination as a serial dict."""
    for sol in keygen(name):
        return sol
    return None


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
