import datetime
import sys

# Decoder / permutation table for hex digits 0-F
# Maps hex digit index -> custom alphanumeric character
decoder = ['q', 'w', 'E', '1', 't', 'y', 'm', '5', 'B', 'v', 'C', 'X', '7', '0', 'f', 'G']

# Reverse map: custom char -> hex digit value
rev_decoder = {ch: i for i, ch in enumerate(decoder)}


def mapdigit(digit: str) -> str:
    """Map a single hex digit character to the custom alphabet."""
    return decoder[int(digit, 16)]


def num_to_hex(num: int) -> str:
    """
    Encode a 32-bit number as 8 custom-alphabet characters.
    Takes the hex representation, pads to 8 digits, then maps each digit.
    """
    # Mask to 32 bits
    num = num & 0xFFFFFFFF
    hex_str = hex(num).replace('0x', '').replace('L', '')
    enc = [mapdigit(c) for c in hex_str]
    padding = [mapdigit('0')] * (8 - len(enc))
    return ''.join(padding + enc)


def hex_to_num(encoded: str) -> int:
    """
    Decode 8 custom-alphabet characters back to a 32-bit integer.
    """
    hex_digits = ''
    for ch in encoded:
        hex_digits += hex(rev_decoder[ch])[2:]
    return int(hex_digits, 16)


def int_flip(num: int) -> int:
    """Flip all bits of a 32-bit integer (bitwise NOT, 32-bit)."""
    # Equivalent to C 'not eax' on a 32-bit value
    return (~num) & 0xFFFFFFFF


def argv1_to_numberA(name: str, hour: int, minute: int) -> int:
    """
    Number A:
      1. sum += char[i] * i  for each char
      2. result *= (minute + hour)
      3. flip all bits (bitwise NOT, 32-bit)
    """
    num = 0
    for i, ch in enumerate(name):
        num += ord(ch) * i
    num *= (minute + hour)
    return int_flip(num)


def argv1_to_numberB(name: str, hour: int, minute: int) -> int:
    """
    Number B:
      1. sum += char[i] + 2*i  for each char
      2. result += (minute + hour)
      3. result ^= 0xa318751
    """
    num = 0
    for i, ch in enumerate(name):
        num += ord(ch) + 2 * i
    num += minute + hour
    return num ^ 0xa318751


def argv1_to_numberC(name: str, hour: int, minute: int) -> int:
    """
    Number C:
      1. sum += char[i]  for each char (no counter multiplier)
      2. result += (minute + minute*16) + (hour*32 - hour)
         i.e. result += minute*17 + hour*31
      3. result <<= 4  (shift left 4)
    """
    num = 0
    for ch in name:
        num += ord(ch)
    # (minute + (minute << 4)) == minute * 17
    # ((hour << 5) - hour)      == hour * 31
    num += (minute + (minute << 4)) + ((hour << 5) - hour)
    return num << 4


def argv1_to_numberD(name: str, hour: int, minute: int) -> int:
    """
    Number D:
      1. init num = hour * 0x7d + minute
      2. sum += char[i] << (i & 0x7)  for each char
      3. result += minute + (hour << 7)
    """
    num = hour * 0x7d + minute
    for i, ch in enumerate(name):
        num += ord(ch) << (i & 0x7)
    num += minute + (hour << 0x7)
    return num


def keygen(name: str, hour: int = None, minute: int = None) -> str:
    """
    Generate a 32-character serial for the given name.
    Uses the current local time by default (hour and minute).
    The serial is time-dependent: it changes each minute.
    """
    if hour is None or minute is None:
        now = datetime.datetime.now()
        hour = now.hour
        minute = now.minute

    B = argv1_to_numberB(name, hour, minute)
    C = argv1_to_numberC(name, hour, minute)
    D = argv1_to_numberD(name, hour, minute)
    A = argv1_to_numberA(name, hour, minute)

    # Serial layout: B C D A  (each 8 chars, total 32)
    return num_to_hex(B) + num_to_hex(C) + num_to_hex(D) + num_to_hex(A)


def verify(name: str, serial: str, hour: int = None, minute: int = None) -> bool:
    """
    Verify a (name, serial) pair.
    The serial must be exactly 32 characters.
    Uses the current local time by default.
    NOTE: Because the algorithm is time-dependent (hour+minute), verification
    will only pass for the minute the serial was generated.
    """
    if len(serial) != 32:
        return False

    # Validate all characters are in the decoder alphabet
    for ch in serial:
        if ch not in rev_decoder:
            return False

    if hour is None or minute is None:
        now = datetime.datetime.now()
        hour = now.hour
        minute = now.minute

    # Decode the four 8-char blocks from the serial
    serial_B = hex_to_num(serial[0:8])
    serial_C = hex_to_num(serial[8:16])
    serial_D = hex_to_num(serial[16:24])
    serial_A = hex_to_num(serial[24:32])

    # Compute expected values from name
    exp_A = argv1_to_numberA(name, hour, minute) & 0xFFFFFFFF
    exp_B = argv1_to_numberB(name, hour, minute) & 0xFFFFFFFF
    exp_C = argv1_to_numberC(name, hour, minute) & 0xFFFFFFFF
    exp_D = argv1_to_numberD(name, hour, minute) & 0xFFFFFFFF

    return (serial_A == exp_A and
            serial_B == exp_B and
            serial_C == exp_C and
            serial_D == exp_D)



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
