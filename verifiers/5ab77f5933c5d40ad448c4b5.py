# Reconstructed from solution writeup by gemigis
# The crackme has multiple levels:
# Level 1: Slider puzzle - correct order is 3, 0, 1, 4, 2 (values 30142)
# Level 2: Checkbox puzzle - 25 checkboxes, pattern: 1100100110001001100110010
# Level 3: Text input - hardcoded string "SYSTEM1AA67fe6"
#
# The 'name' field does not appear to affect the serial/password in this crackme.
# This is a multi-level puzzle, not a name-based keygen.

# ASSUMPTION: The slider values correspond to positions 0-4 with values [3,0,1,4,2]
# based on the writeup stating "it should be 30142"

# ASSUMPTION: The checkbox pattern is exactly as stated: "1100100110001001100110010"
# (1=checked, 0=unchecked), 25 checkboxes total

# ASSUMPTION: The final password is hardcoded as "SYSTEM1AA67fe6" with no name dependency

SLIDER_SOLUTION = [3, 0, 1, 4, 2]  # The correct slider positions
CHECKBOX_PATTERN = "1100100110001001100110010"  # 25 checkboxes
FINAL_PASSWORD = "SYSTEM1AA67fe6"  # Hardcoded string compared at 004561E7


def verify_sliders(slider_values: list) -> bool:
    """Check if slider positions match the required pattern."""
    return list(slider_values) == SLIDER_SOLUTION


def verify_checkboxes(checkbox_states: list) -> bool:
    """Check if 25 checkbox states match the required pattern.
    1 = checked, 0 = unchecked
    """
    if len(checkbox_states) != 25:
        return False
    expected = [int(c) for c in CHECKBOX_PATTERN]
    return list(checkbox_states) == expected


def verify(name: str, serial: str) -> bool:
    """Verify the final level password. Name is not used in this crackme.
    The serial here represents the final text input (Level 3).
    Levels 1 and 2 are UI puzzle states, not text inputs.
    """
    # ASSUMPTION: name field is irrelevant; only the final password matters
    return serial == FINAL_PASSWORD


def keygen(name: str) -> str:
    """Return the valid serial (final password) for any name.
    Since the password is hardcoded, name does not affect the result.
    """
    # ASSUMPTION: hardcoded password, name-independent
    return FINAL_PASSWORD


def full_solution_summary():
    """Print the complete solution for all levels."""
    print("=== Multi-Level CrackMe Solution ===")
    print()
    print("Level 1 - Slider Puzzle:")
    print(f"  Set sliders to positions: {SLIDER_SOLUTION}")
    print(f"  (Order: {' '.join(map(str, SLIDER_SOLUTION))})") 
    print()
    print("Level 2 - Checkbox Puzzle (25 checkboxes, left-to-right, top-to-bottom):")
    for i, state in enumerate(CHECKBOX_PATTERN):
        status = "CHECKED" if state == '1' else "unchecked"
        print(f"  Checkbox {i+1:2d}: {status}")
    print()
    print("Level 3 - Text Input:")
    print(f"  Enter: {FINAL_PASSWORD}")
    print()
    print("Result: 'Good Job Cracker !!!' displayed in flashing colour")



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
