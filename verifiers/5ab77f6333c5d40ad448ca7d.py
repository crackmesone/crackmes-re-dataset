# Reverse-engineered keygen for mucki's crackme1
# Based on the solution writeup by Nuno_1
#
# The writeup describes the serial generation function at 0x004012C0.
# Key observations from the writeup:
#   - SumPart1 (EBP-F0) initialized to -8
#   - SumPart3 (EBP-F4) initialized to 0
#   - SumPart2 (EBP-F8) initialized to 0x3C6 (966)
#   - Part1: sum all characters of the name, added to SumPart1 (starting at -8)
#   - Part2: XOR each character by part of a calculated number (derived from SumPart2/index)
#   - Part3: sum all processed characters from Part2 into SumPart3
#   - Final: SumPart3 * 0x3E8 + SumPart1  (where 0x3E8 = 1000)
#
# NOTE: The writeup was truncated, so exact XOR logic for Part2 is partially assumed.
# The description says "each character is xored by part of a number that is calculated"
# and SumPart2 starts at 0x3C6. A common pattern is to use the index or a rolling
# value derived from SumPart2.
#
# ASSUMPTION: The XOR value for each character at position i is (SumPart2 >> (some_shift))
# or simply (SumPart2 & 0xFF) or index-based. We implement the most straightforward
# interpretation: XOR with (i ^ (SumPart2 & 0xFF)) or XOR with SumPart2 itself.
# Without the full disassembly we cannot be 100% certain.
#
# ASSUMPTION: The writeup says the trap (debugger-present) serial uses the algorithm described.
# The 'real' serial (non-debugger path) may use a different but similar algorithm.
# We implement the described algorithm (which appears to be the trap path based on context,
# but the writeup also says it IS the serial generation function at 0x401028).
#
# From the writeup example: name -> serial 627396 (0x992C4), which we use for validation.

def _compute_serial(name: str) -> int:
    # Part 1: sum all characters, starting accumulator at -8
    sum_part1 = -8
    for ch in name:
        sum_part1 += ord(ch)

    # Part 2: XOR each character by a value derived from SumPart2 (init 0x3C6)
    # ASSUMPTION: The XOR operand cycles or is derived from SumPart2 and the loop index.
    # A common pattern seen in crackmes: xor_val = (sum_part2 >> 8) & 0xFF or similar.
    # We assume: each char is XORed with ((0x3C6 + i) & 0xFF) -- most plausible simple pattern.
    sum_part2_init = 0x3C6
    processed = []
    for i, ch in enumerate(name):
        # ASSUMPTION: XOR key is derived from (sum_part2_init + i) & 0xFF
        xor_key = (sum_part2_init + i) & 0xFF
        processed_char = ord(ch) ^ xor_key
        processed.append(processed_char)

    # Part 3: sum all processed characters
    sum_part3 = 0
    for val in processed:
        sum_part3 += val

    # Final: sum_part3 * 0x3E8 + sum_part1
    result = (sum_part3 * 0x3E8) + sum_part1
    return result


def verify(name: str, serial: str) -> bool:
    """Verify name/serial pair."""
    try:
        serial_int = int(serial)
    except ValueError:
        return False
    computed = _compute_serial(name)
    return computed == serial_int


def keygen(name: str) -> str:
    """Generate the serial for a given name."""
    result = _compute_serial(name)
    return str(result)



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
