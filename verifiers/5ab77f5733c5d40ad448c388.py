import base64
import random
import sys

# ---- helpers mirroring the .NET crackme ----

def _net_string_hashcode(s: str) -> int:
    """Approximate .NET String.GetHashCode() for a given string.
    .NET's GetHashCode is implementation-specific and not guaranteed stable
    across versions, but the common x86 .NET 4 algorithm is well-known.
    ASSUMPTION: using the standard .NET 4 x86 GetHashCode formula.
    """
    h1 = 0x15051505
    h2 = 0x15051505
    # work on UTF-16 LE code units
    chars = [ord(c) for c in s]
    # pad to even length
    if len(chars) % 2 != 0:
        chars.append(0)
    i = 0
    while i < len(chars):
        h1 = (((h1 << 5) + h1 + (h1 >> 27)) ^ chars[i]) & 0xFFFFFFFF
        h2 = (((h2 << 5) + h2 + (h2 >> 27)) ^ chars[i + 1]) & 0xFFFFFFFF
        i += 2
    result = (h1 + h2 * 0x5D588B65) & 0xFFFFFFFF
    # convert to signed 32-bit
    if result >= 0x80000000:
        result -= 0x100000000
    return result


def _overloaded_int(num: int) -> int:
    """
    Recursive function from the crackme, unrolled to a closed form.

    From the write-up explanation:
      if num > 0:
        if even: return (num/2) + 1337
        if odd:  return ((num-1)/2) + 1335   # write-up says /1335 but context means +1335
      if num == 0:
        return 0x539  (= 1337)
      if num < 0:
        abs_num = -num
        if even: return (abs_num/2) + 1337
        if odd:  return ((abs_num-1)/2) + 1335

    ASSUMPTION: the write-up's 'divide by 1335' is a typo/mis-statement;
    the recursive structure shows it converges to 1337 +/- multiples of
    (3 or -2) per step, making the closed form:
      result = 0x539 + (|num|//2)*3 + ... 
    We derive it directly from the recurrence instead.

    Actual closed-form derivation from the recurrence:
      overloaded(0) = 0x539 = 1337
      overloaded(n) for n>0:
        each step reduces n by 1; even adds 3, odd subtracts 2.
        Net per 2 steps (n even, then n-1 odd): +3-2 = +1
        So overloaded(n) = 1337 + n//2 * 1 + (1 if n%2==0 and n>0 else 0) ... 
    Let's just implement it iteratively to be exact.
    """
    # Iterative version of the recursive function
    if num == 0:
        return 0x539
    if num > 0:
        acc = 0x539
        for k in range(1, num + 1):
            if k % 2 == 0:
                acc += 3
            else:
                acc -= 2
        return acc
    else:
        # num < 0
        pos = -num
        acc = 0x539
        for k in range(1, pos + 1):
            if k % 2 == 0:
                acc += 3
            else:
                acc -= 2
        return acc


def _overloaded_str(name: str) -> int:
    """overloaded(string): returns overloaded(GetHashCode(name) / 100000)"""
    h = _net_string_hashcode(name)
    num = int(h / 0x186a0)  # integer division toward zero (C# cast to int)
    return _overloaded_int(num)


def _overloaded_arr(arr: list) -> list:
    """
    Recursive reduction of int array.
    Each call: last element is the 'num', every other element becomes (num+chr[i]) % 0xff
    Recurse until length == 1, return that single-element array.
    """
    if len(arr) <= 1:
        return arr
    num = arr[-1]
    new_arr = [(num + arr[i]) % 0xff for i in range(len(arr) - 1)]
    return _overloaded_arr(new_arr)


def verify(name: str, serial: str) -> bool:
    """Verify name/serial pair."""
    if not name:
        return False
    if len(serial) != 40:
        return False
    try:
        buf = base64.b64decode(serial)
    except Exception:
        return False
    chr_arr = [int(b) for b in buf]
    name_val = _overloaded_str(name) % 0xff
    serial_val = _overloaded_arr(chr_arr)[0]
    return name_val == serial_val


def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.

    Strategy (from the keygen source in the write-up):
      1. Compute target = overloaded_str(name) % 0xff
      2. Start with array [target, 255] (2 elements)
      3. Repeatedly expand: pick random num in [1, last_element),
         prepend it, and reverse the reduction:
           new_arr[i] = (255 + chr[i] - num) % 255  for each existing element
         append num as the new last element
      4. Stop when array has >= 30 bytes, take first 30 bytes
      5. Base64-encode the 30 bytes -> length 40
    """
    target = _overloaded_str(name) % 0xff
    arr = [target, 255]

    sys.setrecursionlimit(100000)

    def expand(current):
        if len(current) >= 30:
            return current
        last = current[-1]
        # pick a random num between 1 and last (exclusive)
        # if last <= 1, use 1
        hi = max(2, last)
        num = random.randint(1, hi - 1) if hi > 1 else 1
        new_arr = [(255 + current[i] - num) % 255 for i in range(len(current))]
        new_arr.append(num)
        return expand(new_arr)

    expanded = expand(arr)
    key_bytes = bytes([expanded[i] % 256 for i in range(30)])
    serial = base64.b64encode(key_bytes).decode('ascii')
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
