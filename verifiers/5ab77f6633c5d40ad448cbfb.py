import random
import string


def _crc_byte(name: str) -> int:
    """Modified CRC32 that collapses the name to a single 6-bit value."""
    crc = 0
    for ch in name.encode('latin-1'):
        crc ^= ch
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xEDB88320
            else:
                crc >>= 1
    # Modification: keep only low 6 bits, then XOR with 0x3F
    # Equivalent to: crc <<= 0x1A; crc >>= 0x1A; crc ^= 0x3F
    # but working on unsigned 32-bit arithmetic:
    crc &= 0xFFFFFFFF
    crc <<= 0x1A
    crc &= 0xFFFFFFFF
    crc >>= 0x1A
    crc ^= 0x3F
    return crc & 0xFF


def _build_adjacency():
    """Build the 64x64 adjacency matrix for the graph.
    For each byte value i in [0,63], compute allowed next values.
    """
    A = [[False] * 64 for _ in range(64)]
    for i in range(256):  # iterate over all 256, but only 0..63 are valid vertices
        b = 0
        if i < 0x10:
            b |= 0x03
        if i < 0x08:
            b |= 0x0C
        if i >= 0x30:
            b |= 0xC0
        if i >= 0x38:
            b |= 0x30
        r = i % 8
        if r == 0:
            b |= 0x41
            b |= 0x14  # fallthrough
        elif r == 1:
            b |= 0x14
        elif r in (2, 3, 4, 5):
            pass
        elif r == 6:
            b |= 0x28
        elif r == 7:
            b |= 0x82
            b |= 0x28
        b = (~b) & 0xFF  # bl = b ^ 0xFF

        if i > 63:
            continue  # only vertices 0..63

        # Each bit in b determines an offset; compute neighbour and check range
        offsets = [
            (0x01, -17),
            (0x02, -15),
            (0x04, -10),
            (0x08,  -6),
            (0x10,  +6),
            (0x20, +10),
            (0x40, +15),
            (0x80, +17),
        ]
        for mask, off in offsets:
            if b & mask:
                nb = (i + off) & 0xFF
                if nb <= 0x3F:
                    A[i][nb] = True
    return A


_ADJACENCY = _build_adjacency()


def _dfs(start: int, max_attempts: int = 100000) -> list:
    """Randomised DFS to find a Hamiltonian path of length 64 starting at `start`.
    Returns a list of 64 unique values in [0,63], or raises RuntimeError.
    """
    A = _ADJACENCY
    for _ in range(max_attempts):
        path = [start]
        used = [False] * 64
        used[start] = True

        while len(path) < 64:
            v = path[-1]
            neighbours = [nb for nb in range(64) if A[v][nb] and not used[nb]]
            if not neighbours:
                break  # dead end, retry
            nxt = random.choice(neighbours)
            used[nxt] = True
            path.append(nxt)

        if len(path) == 64:
            return path

    raise RuntimeError("Could not find a valid path; try again.")


def _ser_to_hex(ans: list) -> str:
    """Pack 64 6-bit values into 48 bytes and return as 96-char hex string."""
    ser = bytearray(0x30)
    k = 0
    for j in range(0, 0x30, 3):
        ser[j]   = ((ans[k] << 2) | (ans[k + 1] >> 4)) & 0xFF
        k += 1
        ser[j+1] = ((ans[k] << 4) | (ans[k + 1] >> 2)) & 0xFF
        k += 1
        ser[j+2] = ((ans[k] << 6) | (ans[k + 1])) & 0xFF
        k += 2
    return ser.hex().upper()


def _hex_to_ser(serial: str) -> list:
    """Convert 96-char hex serial back to 64 6-bit values."""
    if len(serial) != 96:
        return None
    try:
        raw = bytes.fromhex(serial)
    except ValueError:
        return None
    if len(raw) != 0x30:
        return None
    # Unpack: every 3 bytes -> 4 6-bit values
    ans = []
    for j in range(0, 0x30, 3):
        a0 = (raw[j] >> 2) & 0x3F
        a1 = ((raw[j] & 0x03) << 4) | ((raw[j+1] >> 4) & 0x0F)
        a2 = ((raw[j+1] & 0x0F) << 2) | ((raw[j+2] >> 6) & 0x03)
        a3 = raw[j+2] & 0x3F
        ans.extend([a0, a1, a2, a3])
    return ans


def verify(name: str, serial: str) -> bool:
    """Verify a name/serial pair."""
    # Serial must be exactly 96 hex characters (0x60 chars)
    if len(serial) != 0x60:
        return False

    # Decode serial -> 64 6-bit values
    ans = _hex_to_ser(serial)
    if ans is None:
        return False

    # All values must be in [0, 63]
    if any(v > 63 for v in ans):
        return False

    # All values must be unique
    if len(set(ans)) != 64:
        return False

    # First value must equal NX derived from name
    nx = _crc_byte(name)
    if ans[0] != nx:
        return False

    # Each consecutive pair must be connected in the adjacency graph
    A = _ADJACENCY
    for i in range(63):
        if not A[ans[i]][ans[i+1]]:
            return False

    return True


def keygen(name: str) -> str:
    """Generate a valid serial for the given name."""
    nx = _crc_byte(name)
    path = _dfs(nx)
    return _ser_to_hex(path)



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
