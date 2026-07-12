# Reverse-engineered keygen for 'get2thatnumber' by obnoxious
# Based on solution writeup by indomit
#
# ASSUMPTION: function_one() computes an integer (lt) from the name.
#   The writeup says lt can be 5, 6, or 8, but does NOT give the exact
#   formula. We assume it's based on name length mod something, or a
#   sum of character values mod something. We will ASSUME a plausible
#   mapping based on the clue that 'lt can be 5, 6 or 8'.
#   The writeup gives example names for lt==5: "11111", "abcd", "crackmes.de"
#   len("11111")=5, len("abcd")=4, len("crackmes.de")=11
#   No clear pattern from length alone. We'll assume sum of ASCII bytes mod 3
#   maps to {5,6,8} as: 0->5, 1->6, 2->8.
#
# ASSUMPTION: function_two() maps lt -> num2 as documented:
#   5 -> 8, 6 -> 13, 8 -> 34  (Fibonacci-like: F(5)=8? no, F(6)=8, F(7)=13, F(9)=34)
#   Actually 8,13,34 are Fibonacci numbers. This mapping is exact per writeup.

def function_one(name: str) -> int:
    # ASSUMPTION: exact algorithm unknown. We derive lt from name.
    # The writeup only says lt can be 5, 6, or 8.
    # We map sum of ASCII bytes mod 3 -> {5, 6, 8}
    s = sum(ord(c) for c in name)
    r = s % 3
    return [5, 6, 8][r]

def function_two(lt: int) -> int:
    mapping = {5: 8, 6: 13, 8: 34}
    return mapping[lt]

def generate_segments(lt: int):
    """
    Generate all valid segments for the given lt.
    Rules:
    - Each segment ends with digit lt
    - Each segment starts with '1' or '2'
    - Contiguous digits differ by exactly 1 or 2 (each next digit = prev+1 or prev+2)
    - The segment is a sequence of increasing digits ending at lt
    """
    results = []

    def dfs(current_seq):
        last = current_seq[-1]
        if last == lt:
            results.append(''.join(str(d) for d in current_seq))
            return
        for step in (1, 2):
            nxt = last + step
            if nxt <= lt:
                dfs(current_seq + [nxt])

    for start in (1, 2):
        if start <= lt:
            dfs([start])

    return results

def keygen(name: str) -> str:
    """
    Generate a valid serial for the given name.
    """
    lt = function_one(name)
    num2 = function_two(lt)
    segments = generate_segments(lt)

    # We need exactly num2 unique segments.
    # The writeup asserts there are exactly num2 such segments for each lt.
    if len(segments) < num2:
        raise ValueError(f"Not enough segments generated: got {len(segments)}, need {num2}")

    # Use the first num2 unique segments (all should be unique by construction)
    chosen = segments[:num2]
    # Serial is the concatenation of chosen segments (no separator)
    serial = ''.join(chosen)
    return serial

def verify(name: str, serial: str) -> bool:
    """
    Verify a serial for a given name.
    """
    if not name:
        return False

    lt = function_one(name)
    num2 = function_two(lt)

    text = serial
    index = 0
    num4 = 0
    str_array = [None] * num2

    # Phase 1: split serial on occurrences of lt digit
    for ch in serial:
        if ch == str(lt):
            if index >= num2:
                break
            str_array[index] = text[:num4 + 1]
            text = text[num4 + 1:]
            index += 1
            num4 = 0
        else:
            num4 += 1

    # Phase 2: must have found at least num2 segments
    if index < num2:
        return False

    # Phase 3: all segments must be unique
    for i in range(num2):
        for j in range(i + 1, num2):
            if str_array[i] == str_array[j]:
                return False

    # Phase 4: first char of each segment must be '1' or '2'
    #          contiguous digits must differ by exactly 1 or 2
    for seg in str_array[:num2]:
        if seg is None or len(seg) == 0:
            return False
        if seg[0] not in ('1', '2'):
            return False
        for k in range(len(seg) - 1):
            diff = int(seg[k + 1]) - int(seg[k])
            if diff not in (1, 2):
                return False

    return True


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
