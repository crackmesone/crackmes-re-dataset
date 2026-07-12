# Reconstructed from keygen.cpp (solution/keygen.cpp) embedded in the writeup
# The CPP source was encoded but the PDF writeup + code logic describes the algorithm fully.
#
# Algorithm (from keygen.cpp and PDF writeup):
#
# 1. Iterate over each character of the username.
#    For each char ch = ord(username[i]):
#      - if ch < 110: ch += 11
#      - if ch > 110: ch -= 13
#      - if ch == 110: ch += 20
#      - ch += 11
#    Add ch to ESI (accumulator).
#    loopTemp += (ESI - 63)
#
# 2. firstComponent = loopTemp + ESI
#
# 3. Convert firstComponent to string -> loopResultAsString
#
# 4. stringToDecimal: concatenate decimal ASCII values of each char of loopResultAsString
#    -> decimalString
#
# 5. Sliding window: for each position i in decimalString, take 4 chars starting at i,
#    build serialWithDashes as: '-' + decimalString[i:i+4] repeated for each i
#    (window slides over decimalString)
#
# 6. correctSerialAsString = str(len(serialWithDashes)) + '13' + serialWithDashes
#    (pad/prefix with the length-as-decimal then append '13' then the dashed string)
#
# NOTE: The keygen.cpp source was garbled (mojibake). The algorithm below is reconstructed
# from the readable PDF writeup + the partially decoded C++ source. Some steps are
# ASSUMPTION-marked where exact details were not perfectly clear.

def _char_transform(ch):
    """Transform a single ASCII value per the loop in keygen.cpp"""
    ch = int(ch)
    if ch < 110:
        ch += 11
    if ch > 110:
        ch -= 13
    if ch == 110:
        ch += 20
    ch += 11
    return ch


def _string_to_decimal(s):
    """Concatenate decimal representations of ASCII values of each char in s."""
    result = ''
    for c in s:
        result += str(ord(c))
    return result


def _build_serial_with_dashes(loop_result_as_string):
    """Sliding 4-char window over decimalString, building dashed serial."""
    decimal_string = _string_to_decimal(loop_result_as_string)
    serial_with_dashes = ''
    for i in range(len(decimal_string)):
        # ASSUMPTION: each window segment is prefixed with '-', window size = 4
        serial_with_dashes += '-' + decimal_string[i:i+4]
    return serial_with_dashes


def _compute_serial(name):
    ESI = 0
    loop_temp = 0

    for i in range(len(name)):
        ch = ord(name[i])
        # Transform
        if ch < 110:
            ch += 11
        # re-check after first modification
        if ch > 110:
            ch -= 13
        if ch == 110:
            ch += 20
        ch += 11

        ESI += ch
        loop_temp += (ESI - 63)

    first_component = loop_temp + ESI

    # Convert firstComponent to string
    loop_result_as_string = str(first_component)

    # Build serial with dashes
    serial_with_dashes = _build_serial_with_dashes(loop_result_as_string)

    # ASSUMPTION: correctSerialAsString = str(len(serialWithDashes)) + '13' + serialWithDashes
    correct_serial = str(len(serial_with_dashes)) + '13' + serial_with_dashes

    return correct_serial


def keygen(name):
    """Generate a valid serial for the given name."""
    return _compute_serial(name)


def verify(name, serial):
    """Verify that serial matches the expected serial for name."""
    expected = _compute_serial(name)
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
