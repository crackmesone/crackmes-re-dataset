# Ganoes First Crackme - Key Validation / Keygen
# Based on the assembly walkthrough by Fireblast
#
# Algorithm (two loops):
#
# Loop 1: For each position i in range(len(username)):
#   Find smallest integer c (starting from 0) such that
#   c % username[i] == 0  (i.e. c is the first multiple of ord(username[i]))
#   BUT the ASM shows: increment c until username_char matches the byte at some position.
#   ASSUMPTION: 'c' is incremented until (c % ord(username[i]) == 0), i.e.
#   c is a counter starting at 0, incremented until c mod char == 0, so c == char itself
#   (first positive multiple). Actually re-reading: "increment some counter until
#   the last byte modulo character = 0" -- so we look for c where c % char_value == 0.
#   The loop starts c=0 and increments, so the first such c where c%char==0 AND c==char
#   is just char itself when starting at 0 => c = char_value.
#   ASSUMPTION: c starts at 0, increments until c % ord(username[i]) == 0.
#   Since 0%anything==0, c would immediately be 0 -- that can't be right.
#   Re-reading ASM more carefully:
#     EBP-114 = c (starts at 0)
#     Loop: load char at position EBP-110 (counter), compare with AL (c & 0xFF)
#     If equal: break. Else: increment c.
#   So: c increments until c (as byte) == username[i] character.
#   That means c just equals ord(username[i]) at the end of the inner loop!
#   Then: array[i] = c * c + 0x539  (where c = ord(username[i]))
#
# Loop 2: For i from 1 to len(username)-1 (inclusive, i <= len):
#   array[i] = array[i-1] + array[i]
#   (cumulative sum from index 1 onward; array[0] stays as-is)
#
# Serial check:
#   The entered password is compared against array[len(username)]
#   ASSUMPTION: comparison index is username_length (last loop counter value)
#   But loop 2 runs i from 1 to len(username) inclusive, so last written index = len
#   ASSUMPTION: serial = array[len(username)] after cumulative sum

def compute_serial_array(name: str):
    n = len(name)
    arr = [0] * (n + 2)  # extra space

    # Loop 1: for i in 0..n-1
    # c increments from 0 until (c & 0xFF) == ord(name[i])
    # => c == ord(name[i])  (assuming all chars are ASCII < 256)
    for i in range(n):
        c = ord(name[i])  # inner loop result
        arr[i] = c * c + 0x539

    # Loop 2: cumulative sum starting at index 1
    # i goes from 1 to n (inclusive, i <= len)
    for i in range(1, n + 1):
        # ASSUMPTION: index bounds -- loop uses i as index
        # array[i] = array[i-1] + array[i]
        # But for i == n, array[n] was not set in loop 1 (loop 1 only sets 0..n-1)
        # ASSUMPTION: array[n] starts as 0 before loop 2 runs for index n
        arr[i] = arr[i - 1] + arr[i]

    return arr


def verify(name: str, serial: str) -> bool:
    """Verify a name/serial pair."""
    if not name:
        return False
    try:
        serial_int = int(serial)
    except ValueError:
        return False

    arr = compute_serial_array(name)
    n = len(name)

    # ASSUMPTION: serial compared against arr[n] (the value at index = username_length)
    # after the cumulative-sum loop
    expected = arr[n]
    return serial_int == expected


def keygen(name: str) -> str:
    """Generate a valid serial for the given name."""
    if not name:
        raise ValueError('Name must not be empty')
    arr = compute_serial_array(name)
    n = len(name)
    # ASSUMPTION: serial is arr[n]
    return str(arr[n])



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
