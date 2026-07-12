import struct
import math


def compute_serial_raw(name: str) -> bytes:
    """
    Implements the floating-point loop described in the writeup.

    Buffer construction:
      - buffer length is 0x63 (99) bytes
      - buffer[i] = (name_length - (0x63 - name_length) + i + 1) ... actually:
        The writeup says:
          len_name is subtracted from 0x63, added to name pointer, pointer (EDI) increased by 1.
          AL (= length of name at first) is moved into buffer while AL is increased.
        So: the starting fill value = name_length, and for each position i in 0..0x62,
            buffer[i] = (name_length + i) & 0xFF  (wrapping byte arithmetic)
        BUT the start index into the name is (0x63 - name_length), so:
            buffer[i] = ord(name[ (0x63 - name_length + i) % len(name) ])  -- ASSUMPTION below
    """
    # ASSUMPTION: The buffer is filled as follows based on the writeup description.
    # "length of the string subtracted from 0x63, added to pointer to name, EDI increased by one.
    #  AL (containing length) increased while moved into increasing buffer (LOOPD)"
    # This suggests: start_offset = 0x63 - len_name in the name string,
    # then copy wrapping around, but AL starts at name_length and increments.
    # The most consistent reading: buffer[i] = (name_length + i) & 0xFF for i in 0..0x62
    # where name_length = len(name). This is the byte value loaded as a float.
    # ASSUMPTION: buffer values are just ascending bytes starting from name_length.

    n = len(name)
    buf = []
    for i in range(0x63):
        buf.append((n + i) & 0xFF)

    a = float(n)  # 'len' in the writeup

    result_accum = 0.0  # 'zero2' / result accumulator

    for i in range(0x63 - 1):  # pairs: buf[i] and buf[i+1]
        # Step 2-6: load name[i] and name[i+1], take sqrt
        b = math.sqrt(float(buf[i]))    # sqrt1
        c = math.sqrt(float(buf[i + 1]))  # sqrt2

        # Steps 7-11: (a+b)*(c-b)*0.5
        temp2 = (a + b) * (c - b) * 0.5

        # Steps 12-16: (c+b)*(a-c)*0.5 added to temp2
        temp2 += (c + b) * (a - c) * 0.5

        # Steps 17-20: subtract (c+a)*(a-b)*0.5
        # writeup: "result of step 19 is subtracted by temp2" -> temp2 - (c+a)*(a-b)*0.5
        # ASSUMPTION: sign direction per writeup step 20
        val = temp2 - (c + a) * (a - b) * 0.5

        # Steps 21-22: absolute value
        val = abs(val)

        # Step 23-24: add to accumulator
        result_accum += val

    # The loop runs 0x63 times (counter goes from 0 to 0x62),
    # but we only have pairs so last iteration uses buf[0x62] and buf[0x63]?
    # ASSUMPTION: loop is exactly 0x63 iterations, using buf[i] and buf[i+1],
    # with buf sized 0x64 or wrapping. We run 0x63 iterations.
    # Re-run including index 0x62:
    # Already handled above (range(0x63-1) = 0..97, that's 98 iters).
    # ASSUMPTION: it's actually 0x63 iterations total:
    buf2 = []
    for i in range(0x64):
        buf2.append((n + i) & 0xFF)

    result_accum = 0.0
    for i in range(0x63):
        b = math.sqrt(float(buf2[i]))
        c = math.sqrt(float(buf2[i + 1]))
        temp2 = (a + b) * (c - b) * 0.5
        temp2 += (c + b) * (a - c) * 0.5
        val = temp2 - (c + a) * (a - b) * 0.5
        val = abs(val)
        result_accum += val

    # result_accum is the final double; take its 8 raw bytes
    raw = struct.pack('<d', result_accum)
    return raw


def keygen(name: str) -> str:
    """
    Convert the 8 bytes of the double to a serial string,
    then apply the character transformation:
      each character except '9' and 'F' is decreased by 1.
    ASSUMPTION: the 8 bytes are printed as hex digits (uppercase) forming a 16-char string.
    ASSUMPTION: 'subtracted by one' means ASCII value -= 1 for chars != '9' and != 'F'.
    """
    raw = compute_serial_raw(name)
    # Convert to hex string (16 uppercase hex chars)
    # ASSUMPTION: printed as raw bytes interpreted as characters, not hex.
    # The writeup says "taking the 8 bytes of the double variable and printing it as string"
    # This likely means the raw bytes ARE the serial string (8 chars).
    # Then transformation: each char except '9' and 'F' is subtracted by 1.
    # But serial length must be 16 (first check). So hex representation is more likely.
    hex_str = raw.hex().upper()  # 16 chars

    serial_chars = []
    for ch in hex_str:
        if ch == '9' or ch == 'F':
            serial_chars.append(ch)
        else:
            # subtract 1 from ASCII
            serial_chars.append(chr(ord(ch) - 1))

    return ''.join(serial_chars)


def verify(name: str, serial: str) -> bool:
    if len(serial) != 16:
        return False
    expected = keygen(name)
    return serial == expected



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
