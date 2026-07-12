#!/usr/bin/env python3
# Keygen / verifier for kwenma's 'Custom Packer 2.0'
# Algorithm fully recovered from djd320's writeup + keygen.py

import os
import re
import math
from datetime import datetime, timezone, date


# --- helpers ---

def to_u32(x):
    return x & 0xFFFFFFFF

def to_s32(x):
    return (x + 2**31) % 2**32 - 2**31

def to_u8(x):
    return x & 0xFF

def to_s8(x):
    x &= 0xFF
    return x if x < 0x80 else x - 0x100

def signed_mod(a, m):
    """Truncated (C-style) signed modulo."""
    if m == 0:
        raise ZeroDivisionError
    q = int(a / m)
    return a - q * m


# --- pipeline stages ---

def f1c0(s: bytes) -> bytes:
    """Stage 1: Fibonacci XOR/add on every 3rd byte (indices 0,3,6,...)."""
    b = bytearray(s)
    fib1, fib2 = 1, 1
    for i in range(0, len(b), 3):
        new_fib2 = to_u8(fib1 + fib2)
        b[i] = to_u8((b[i] ^ fib1) + fib2)
        fib1 = fib2
        fib2 = new_fib2
    return bytes(b)


def f00edc0(s: bytes) -> bytes:
    """Stage 2: Prime-based signed arithmetic + XOR."""
    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]
    out = bytearray()
    for i, c in enumerate(s):
        c_signed = to_s8(c)
        a = c_signed * primes[i % len(primes)] + i * 7
        rem = signed_mod(a, 0xFB)
        val = to_u32(rem) ^ primes[(i + 3) % len(primes)]
        out.append(to_u8(val))
    return bytes(out)


def f00f990(s: bytes) -> bytes:
    """Stage 3: Trig-based transform.
    ASSUMPTION: uses truncated pi = 3.14159 to match MSVCRT behavior."""
    local_48 = 3.14159  # truncated pi, NOT math.pi
    out = bytearray()
    for i, c in enumerate(s):
        c_signed = to_s8(c)
        dVar10 = math.sin(local_48 * c_signed)
        dVar11 = math.cos(c_signed + i)
        local_48 = math.fmod(dVar10 * dVar11 * 1000.0, 0x100)
        dVar10 = abs(local_48)
        base = int(dVar10)
        val = base + c_signed + i * 0x0D
        out.append(to_u8(val))
    return bytes(out)


def win_day_of_week(d: date) -> int:
    """Windows SYSTEMTIME DayOfWeek: Sunday=0, Monday=1, ..., Saturday=6."""
    return (d.weekday() + 1) % 7


def f00eb00(s: bytes, d: date) -> bytes:
    """Stage 4: Date-based XOR transform."""
    wYear = d.year
    wMonth = d.month
    wDay = d.day
    wDayOfWeek = win_day_of_week(d)
    local_54 = (wYear % 100) + wMonth * 7 + wDay * 13
    local_1c = wDayOfWeek
    out = bytearray()
    for i, c in enumerate(s):
        c_signed = to_s8(c)
        t = c_signed + local_54 + i * local_1c
        t_u8 = to_u8(t)
        shift = i % 8
        v = t_u8 ^ (local_54 >> shift)
        out.append(to_u8(v))
    return bytes(out)


def f00f530(s: bytes) -> bytes:
    """Stage 5: 5-round byte transformation."""
    cur = bytearray(s)
    for rnd in range(5):
        nxt = bytearray()
        for i, c in enumerate(cur):
            x = to_s8(c)
            x32 = to_s32(x)
            if rnd == 0:
                v = to_s32((x32 << 2) | (x32 >> 6))
                v = to_s32(v ^ 0xAA)
                outb = to_u8(v)
            elif rnd == 1:
                iVar2 = to_s32(x32 * 0x11 + 0x2A)
                edx = to_u32(iVar2 >> 31) & 0xFF
                eax = to_u32(iVar2 + edx) & 0xFF
                eax = to_s32(eax - edx)
                outb = to_u8(eax)
            elif rnd == 2:
                v = to_s32((x32 ^ to_s32(i * 0x17)) + to_s32(rnd * 0x0B))
                outb = to_u8(v)
            elif rnd == 3:
                iVar2 = to_s32((x32 + 0x5A) * 3)
                edx = to_u32(iVar2 >> 31) & 0xFF
                eax = to_u32(iVar2 + edx) & 0xFF
                eax = to_s32(eax - edx)
                outb = to_u8(eax)
            else:  # rnd == 4
                v = to_s32((x32 ^ 0xF0) + (i + rnd) * 7)
                outb = to_u8(v)
            nxt.append(outb)
        cur = nxt
    return bytes(cur)


def format_password(data: bytes) -> str:
    """Stage 6+7: Hex encode with per-byte offset, group with '-', substitute chars."""
    parts = []
    for i, b in enumerate(data):
        parts.append(f"{(b + 0x10 + i * 3) & 0xFF:02x}")
        if (i + 1) % 4 == 0 and i != len(data) - 1:
            parts.append("-")
    hexstr = "".join(parts)
    return hexstr.replace("a", "@").replace("e", "$").replace("f", "#")


# --- MachineGuid readers ---

def read_machine_guid_windows():
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography")
        value, _ = winreg.QueryValueEx(key, "MachineGuid")
        return value
    except Exception:
        return None


def read_machine_guid_wine():
    reg_path = os.path.expanduser("~/.wine/system.reg")
    if not os.path.isfile(reg_path):
        return None
    try:
        with open(reg_path, "r", encoding="utf-8", errors="ignore") as f:
            reg_data = f.read()
        m = re.search(r'"MachineGuid"="([0-9a-fA-F-]+)"', reg_data)
        return m.group(1) if m else None
    except Exception:
        return None


def get_machine_guid(override=None):
    if override:
        return override
    return read_machine_guid_windows() or read_machine_guid_wine()


# --- core algorithm ---

def compute_serial(machine_guid: str, d: date) -> str:
    """Full pipeline: MachineGuid + date -> serial string."""
    s0 = machine_guid.encode("ascii")
    s1 = f1c0(s0)
    s2 = f00edc0(s1)
    s3 = f00f990(s2)
    s4 = f00eb00(s3, d)
    s5 = f00f530(s4)
    return format_password(s5)


# --- public API ---
# NOTE: 'name' is not used by this crackme; the key is machine-bound + date-bound.
# ASSUMPTION: serial validity is checked only against the machine's own MachineGuid
# and the current UTC date. There is no username component.

def verify(name: str, serial: str, machine_guid: str = None, d: date = None) -> bool:
    """Return True if serial is the correct password for this machine+date.
    machine_guid: override (for testing). If None, read from registry.
    d: date override (for testing). If None, use today UTC.
    """
    guid = get_machine_guid(machine_guid)
    if not guid:
        raise RuntimeError("Cannot determine MachineGuid")
    if d is None:
        d = datetime.now(timezone.utc).date()
    expected = compute_serial(guid, d)
    return serial == expected


def keygen(name: str, machine_guid: str = None, d: date = None) -> str:
    """Generate the valid serial for this machine+date.
    machine_guid: override (for testing). If None, read from registry.
    d: date override (for testing). If None, use today UTC.
    """
    guid = get_machine_guid(machine_guid)
    if not guid:
        raise RuntimeError("Cannot determine MachineGuid")
    if d is None:
        d = datetime.now(timezone.utc).date()
    return compute_serial(guid, d)


# --- CLI ---


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
