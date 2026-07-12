def _string_length(name):
    return len(name)

def verify(name: str, serial: str) -> bool:
    try:
        expected = keygen(name)
        return serial == expected
    except Exception:
        return False

def keygen(name: str) -> str:
    # Name must be 1..9 characters
    if not (1 <= len(name) <= 9):
        raise ValueError("Name length must be between 1 and 9")

    # Step 1: Pad name to 9 bytes with zeros
    name_bytes = bytearray(name.encode('ascii'))
    original_len = len(name_bytes)
    # Pad remaining bytes up to 9 with 0
    while len(name_bytes) < 9:
        name_bytes.append(0)

    # Step 2: Calculate sum1 = sum of original name bytes (original_len bytes)
    sum1 = 0
    for i in range(original_len):
        sum1 += name_bytes[i]
    # sum1 is EDI

    # Step 3: Calculate sum2 over all 9 bytes
    # For each of 9 bytes:
    #   EAX = byte_value
    #   EAX = (EAX * sum1) & 0xFFFFFFFF   (MUL EDI - 32-bit result in EAX)
    #   EAX = (EAX * (36*47)) & 0xFFFFFFFF  (IMUL with 1692)
    #   remainder = EAX % 11
    #   sum2 += remainder
    sum2 = 0
    MASK32 = 0xFFFFFFFF
    for i in range(9):
        eax = name_bytes[i]
        # MUL EDI: unsigned multiply, take low 32 bits
        eax = (eax * sum1) & MASK32
        # IMUL EAX, 36*47 = 1692: take low 32 bits
        eax = (eax * 1692) & MASK32
        # DIV ECX (ECX=11): unsigned divide, remainder
        remainder = eax % 11
        sum2 += remainder
    # ESI = sum2

    # Step 4: ESI = sum2 * 1876 (IMUL, take low 32 bits)
    esi = (sum2 * 1876) & MASK32

    # Step 5: EBX = name_bytes[0] - name_bytes[original_len - 2]
    # (MOVZX EDX, BYTE PTR[EBX+EAX-2] where EAX = original_len from stringLength)
    # MOVZX EBX, BYTE PTR[EBX] = first byte
    # SUB EBX, EDX
    # Note: EBX+EAX-2 = nBuffer + original_len - 2 => index original_len-2
    # ASSUMPTION: when original_len == 1, index -1 wraps; we treat it as index 0 in that edge case
    # but the assembly pads to 9 bytes first so index original_len-2 accesses padded array
    if original_len >= 2:
        last_minus_one = name_bytes[original_len - 2]
    else:
        # ASSUMPTION: for length 1, original_len-2 = -1, which in x86 would access byte before buffer
        # We treat it as 0 to avoid undefined behavior
        last_minus_one = 0
    first_byte = name_bytes[0]
    diff = (first_byte - last_minus_one) & MASK32  # SUB in 32-bit
    esi = (esi + diff) & MASK32

    # Step 6: EAX = ESI * sum1 (MUL EDI, take low 32 bits)
    eax = (esi * sum1) & MASK32

    # Step 7: Convert EAX to decimal string (no leading zeros, no sign)
    return str(eax)



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
