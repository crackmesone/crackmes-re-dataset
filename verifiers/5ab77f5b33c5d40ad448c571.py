def keygen(name: str) -> str:
    """
    Implements the serial/key generation algorithm from the crackme4rd keygen assembly.

    The algorithm iterates over each character in 'name':
      - For each position i (0-indexed), compute power_val = 10^i (but with a quirk: for i=0, power_val=10; for i>=2, power_val=10^i)
      - The loop computes 10^i via repeated multiplication starting from 0x0a (10), looping (i-1) times.
        Actually: for esi=0 (i=0): goes to no1 => eax=10; for esi=1 (i=1): also goes to no1 => eax=10; for esi>=2: loop2 runs (esi-1) times starting from eax=10, imul eax,eax ... wait, let me re-read.

    Re-reading the asm carefully:
      esi starts at 0.
      loop1:
        if esi <= 1: goto no1 (eax = 10)
        else: ecx = esi-1, eax=10, loop2: eax = eax*eax each iter (NO: edx=eax; imul eax,edx => eax=eax*eax ... that's squaring)
        Actually: mov edx,eax; imul eax,edx => eax = eax * edx = eax*eax (squaring)
        But ecx = esi-1 decrements each pass. So for esi=2: ecx=1, one squaring: 10^2=100. For esi=3: ecx=2, 10->100->10000. That's 10^(2^(esi-1)).

    Wait - let me re-read: eax starts at 0x0a=10. loop2: edx=eax; imul eax,edx (eax=eax*eax); dec ecx; jnz loop2.
    For esi=2: ecx=1, one iteration: eax=10*10=100. OK 10^2.
    For esi=3: ecx=2, iter1: eax=100; iter2: eax=10000. That is 10^(2^(esi-1)).
    Hmm but that seems off. Actually eax starts at 10 always.
    esi=2: ecx=1: 10*10=100 = 10^2
    esi=3: ecx=2: 10*10=100, 100*100=10000 = 10^4
    esi=4: ecx=3: 10^2=100, 100^2=10000, 10000^2=100000000 = 10^8
    So power_val = 10^(2^(esi-1)) for esi>=2, and 10 for esi<=1.

    Then:
      eax = power_val
      cdq; idiv 0x7530 (30000) => eax=quotient, edx=remainder
      eax = edx (remainder of power_val % 30000)
      edx = sign-extended bl (current char ASCII value)
      eax = eax * edx  (= (power_val % 30000) * char_val)
      eax = eax + edi  (edi = accumulated serial so far)
      cdq; idiv 0x7530 => edx = remainder
      edi = edx
      esi++, next char

    Final serial = edi (as decimal string), but only if len(name) >= 4.
    """
    if len(name) < 4:
        return ''  # Name must be at least 4 chars

    MOD = 0x7530  # 30000
    edi = 0  # accumulated result

    for esi, ch in enumerate(name):
        bl = ord(ch)

        # Compute power_val
        if esi <= 1:
            # ASSUMPTION: for esi=0 and esi=1, the code jumps to no1 => eax=10
            power_val = 10
        else:
            # loop2 runs (esi-1) times, squaring eax=10 each time
            eax = 10
            ecx = esi - 1
            while ecx > 0:
                eax = (eax * eax) & 0xFFFFFFFF  # 32-bit imul
                ecx -= 1
            power_val = eax

        # cdq + idiv ecx (ecx=30000) - signed division, get remainder
        # In Python, replicate signed 32-bit idiv remainder
        def signed32(v):
            v = v & 0xFFFFFFFF
            if v >= 0x80000000:
                v -= 0x100000000
            return v

        pv_signed = signed32(power_val)
        # idiv: remainder has same sign as dividend
        if pv_signed >= 0:
            rem1 = pv_signed % MOD
        else:
            rem1 = -((-pv_signed) % MOD)

        eax = rem1
        # movsx edx,bl => sign extend byte
        edx = bl if bl < 128 else bl - 256
        eax = eax * edx

        # signed 32-bit
        eax = signed32(eax & 0xFFFFFFFF)

        eax = eax + edi
        eax = signed32(eax & 0xFFFFFFFF)

        # idiv 30000
        if eax >= 0:
            edi = eax % MOD
        else:
            edi = -((-eax) % MOD)

    return str(edi)


def verify(name: str, serial: str) -> bool:
    if len(name) < 4:
        return False
    expected = keygen(name)
    return serial.strip() == expected



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
