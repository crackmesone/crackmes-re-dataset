#!/usr/bin/env python3
"""
Chainbreaker crackme reverse-engineered solver.

The binary takes a single integer SEED argument.
It computes required_links(seed), then iteratively applies parse_step
for that many steps. Success if final state == original seed.

Known valid seed: -11478 (requires 72 links)
"""

def int32(x: int) -> int:
    """Convert to signed 32-bit integer."""
    x &= 0xFFFFFFFF
    return x - 0x100000000 if (x & 0x80000000) else x

def u32(x: int) -> int:
    """Convert to unsigned 32-bit integer."""
    return x & 0xFFFFFFFF

def c_rem(a: int, m: int) -> int:
    """C-style remainder (truncates toward zero)."""
    q = int(a / m)  # truncation toward zero
    return a - q * m

def required_links(seed: int) -> int:
    """
    Compute the number of chain links required for a given seed.
    Reconstructed from binary analysis:
      a = int32(u32(seed) ^ 0x141)
      b = int32(u32(seed) ^ 0x7B)
      t = int32(a + b)
      t = int32(t * 0x533D)
      links = abs(c_rem(t, 100))
      if links == 0: links = 10
    """
    s = int32(seed)
    a = int32(u32(s) ^ 0x141)
    b = int32(u32(s) ^ 0x7B)
    t = int32(a + b)
    t = int32(t * 0x533D)
    links = c_rem(t, 100)
    if links < 0:
        links = -links
    if links == 0:
        links = 10
    return links

def parse_step(seed: int, current_state: int, step_idx: int):
    """
    State transition function: parse(seed, current_state, step_idx)

    1. If current_state == 0, exit (return None to signal failure).
    2. Normalize state:
       if current_state < -0x1000 or current_state > 0x1000:
           state_mod = u32(-(current_state % 0x1000))  # C-style rem
       else:
           state_mod = u32(current_state)
    3. xor_mix = 1 ^ state_mod ^ (state_mod<<1) ^ (state_mod<<2)  (all u32)
    4. next = seed + (((step_idx + seed) - 1U) ^ state_mod) + xor_mix - 0x0F
       (all operations in u32, result converted back to int32)
    """
    if current_state == 0:
        return None  # chain broken by zero

    # Normalize state
    if current_state < -0x1000 or current_state > 0x1000:
        r = c_rem(current_state, 0x1000)
        state_mod = u32(-r)
    else:
        state_mod = u32(current_state)

    # Build xor_mix: xor_mix = 1 ^ state_mod ^ (state_mod<<1) ^ (state_mod<<2)
    # Implemented as loop over shift indices 0,1,2
    xor_mix = 1
    for shift_idx in range(3):
        xor_mix = u32(xor_mix ^ u32(state_mod << (shift_idx & 0x1F)))

    # Compute next state (all arithmetic in u32)
    u_seed = u32(seed)
    x = u32(u32(step_idx) + u_seed - 1)
    x = u32(x ^ state_mod)
    out = u32(u_seed + x + xor_mix - 0x0F)
    return int32(out)

def verify(seed: int, serial=None) -> bool:
    """
    Verify that 'seed' breaks the chain.
    The crackme takes only a single integer seed; 'serial' param is unused.
    Returns True if the seed is valid.
    """
    seed = int32(int(seed))
    links = required_links(seed)
    if links <= 0 or links >= 100:
        return False
    state = seed
    for step_idx in range(links):
        state = parse_step(seed, state, step_idx)
        if state is None:
            return False
    return state == seed

def keygen(name=None):
    """
    Brute-force search for valid seeds.
    The crackme has no 'name' field; this ignores it and yields valid seeds.
    Known valid seed: -11478
    Searches negative integers first (where the known solution lives),
    then positive integers.
    """
    # Known valid answer from write-up
    if verify(-11478):
        yield -11478

    # General brute-force over int32 range
    # Negative range first (known solution is negative)
    for seed in range(-1, -2**31, -1):
        if seed == -11478:
            continue  # already yielded
        if verify(seed):
            yield seed

    # Positive range
    for seed in range(1, 2**31):
        if verify(seed):
            yield seed

def find_seeds(start: int, end: int):
    """Search a specific range for valid seeds."""
    results = []
    for seed in range(start, end + 1):
        if verify(seed):
            links = required_links(int32(seed))
            print(f"[+] Found seed: {seed}  (links={links})")
            results.append(seed)
    return results


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
            print(_sv)
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
