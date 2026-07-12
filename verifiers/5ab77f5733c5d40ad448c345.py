import math


def function007(name: str) -> int:
    """Sum of ASCII values of name characters."""
    return sum(ord(c) for c in name)


def parse_serial(serial: str):
    """Parse serial string into list of integers (split by '-')."""
    try:
        parts = serial.split('-')
        return [int(p) for p in parts]
    except Exception:
        return []


def verify(name: str, serial: str) -> bool:
    """Verify a name/serial pair."""
    # Count hyphens
    num_hyphens = serial.count('-')
    if num_hyphens not in (11, 14):
        return False

    # Parse into integer array
    try:
        nums = parse_serial(serial)
    except Exception:
        return False

    # Expect 12 or 15 numbers
    if len(nums) not in (12, 15):
        return False

    # Count valid triplets:
    # For each group of 3 (i, i+1, i+2):
    #   nums[i] + nums[i+1] == nums[i+2]  AND  abs(nums[i+1] - nums[i]) == 1
    count = 0
    for i in range(0, len(nums), 3):
        if i + 2 >= len(nums):
            break
        a = nums[i]
        b = nums[i + 1]
        c = nums[i + 2]
        if (a + b == c) and (abs(b - a) == 1):
            count += 1

    target = function007(name)

    if count == 4 and len(nums) >= 12:
        total = nums[2] + nums[5] + nums[8] + nums[11]
        return total == target
    elif count == 5 and len(nums) >= 15:
        total = nums[2] + nums[5] + nums[8] + nums[11] + nums[14]
        return total == target
    return False


def make_triplet(odd_sum: int):
    """Given an odd number (2k+1), return (k, k+1, 2k+1) triplet parts as string."""
    assert odd_sum % 2 == 1, "odd_sum must be odd"
    k = odd_sum // 2
    return (k, k + 1, odd_sum)


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.

    Strategy (following the writeup):
    - Compute target = sum of ASCII values of name.
    - If target is odd: use 5 triplets (15 numbers, 14 hyphens).
      The sum of 5 odd numbers can be odd.
      Use first triplet = 1 (smallest odd: 0-1-1), then distribute remaining among 4 triplets.
    - If target is even: use 4 triplets (12 numbers, 11 hyphens).
      Sum of 4 odd numbers is even.

    For simplicity, use the 'easy key' approach:
      - Fill all but the last triplet with the smallest odd value (1 = 0+1+1, sum=1).
      - Compute last triplet's odd value = target - sum_of_others.
    """
    target = function007(name)

    if target % 2 == 1:
        # Need 5 triplets; sum of 5 odd numbers = odd
        num_triplets = 5
        # Use first (num_triplets - 1) triplets with value 1 each
        filler_count = num_triplets - 1
        filler_sum = filler_count * 1  # each filler triplet contributes 1
        last_odd = target - filler_sum
        if last_odd < 1 or last_odd % 2 == 0:
            # ASSUMPTION: if last_odd ends up even or too small, adjust fillers
            # Try filler value 3 for first triplet
            filler_sum = 3 + (filler_count - 1) * 1
            last_odd = target - filler_sum
        triplets = [1] * filler_count + [last_odd]
    else:
        # Need 4 triplets; sum of 4 odd numbers = even
        num_triplets = 4
        filler_count = num_triplets - 1
        filler_sum = filler_count * 1
        last_odd = target - filler_sum
        if last_odd < 1 or last_odd % 2 == 0:
            # Adjust: use filler value 3
            filler_sum = 3 + (filler_count - 1) * 1
            last_odd = target - filler_sum
        triplets = [1] * filler_count + [last_odd]

    # Build serial string
    parts = []
    for odd_val in triplets:
        a, b, c = make_triplet(odd_val)
        parts.append(f"{a}-{b}-{c}")
    serial = '-'.join(parts)
    return serial



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
