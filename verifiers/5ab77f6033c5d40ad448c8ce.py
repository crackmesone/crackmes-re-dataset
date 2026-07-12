#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reverse-engineered keygen for 'back_to_basics' by hmx0101.
Based on the keygen script btb_kg.py from the solution writeup.
"""

from fractions import Fraction
from math import gcd
from zlib import crc32
import copy
from functools import reduce


def _gausselim(A, B, ztol=1.0e-8):
    size = len(A)
    X = [0.0] * size
    R = list(range(size))
    C = list(range(size))
    code = 0

    for pivot in range(size - 1):
        absm = abs(A[pivot][pivot])
        exchrow = pivot
        exchcol = pivot

        for row in range(pivot + 1, size):
            atestm = abs(A[row][pivot])
            if atestm > absm:
                absm = atestm
                exchrow = row

        if pivot != exchcol:
            for row in range(pivot, size):
                A[row][pivot], A[row][exchcol] = A[row][exchcol], A[row][pivot]
            C[pivot] = exchcol

        if pivot != exchrow:
            A[exchrow], A[pivot] = A[pivot], A[exchrow]
            B[exchrow], B[pivot] = B[pivot], B[exchrow]
            R[pivot] = exchrow

        if absm > ztol:
            m = float(A[pivot][pivot])
            for row in range(pivot + 1, size):
                kmul = float(A[row][pivot]) / m
                for col in range(size - 1, pivot, -1):
                    A[row][col] = float(A[row][col]) - kmul * A[pivot][col]
                B[row] = float(B[row]) - kmul * B[pivot]
                A[row][pivot] = 0.0
        else:
            code = 1

    if code == 0:
        for row in range(size - 1, -1, -1):
            s = B[row]
            for k in range(row + 1, size):
                s -= X[k] * A[row][k]
            X[row] = s / A[row][row]
        _reorder(X, C)
    return (code, R, C, A, X, B)


def _reorder(X, C):
    for i, c in enumerate(C):
        if i != c:
            X[i], X[c] = X[c], X[i]
    return X


def _solve(A, b):
    code, R, C, A, X, B = _gausselim(A, b)
    if code == 0:
        return X
    return None


def _lcm(ns):
    return reduce(lambda x, y: x * y // gcd(x, y), ns)


def keygen(name):
    """
    Generate a valid serial for the given name.
    Name must be longer than 5 characters.
    """
    if len(name) <= 5:
        raise ValueError("Name must be longer than 5 characters")

    # Compute crc32 of name (bytes), add constant, take abs, reverse digits
    crcval = str(abs(crc32(name.encode('latin-1')) + 0x13333337))
    crcval = crcval[::-1]

    tooShort = 0
    if len(crcval) < 9:
        crcval += '0'
        tooShort = 1
    crcval = crcval[:9]

    # Build 3x3 matrix A from crcval digits (slicing every 3rd)
    A = []
    A.append(list(crcval[::3]))
    A.append(list(crcval[1::3]))
    A.append(list(crcval[2::3]))

    if tooShort:
        A[2][2] = '-3'

    for row in A:
        for i in range(len(row)):
            row[i] = int(row[i])

    # Identity matrix used as RHS
    B = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    B1 = copy.deepcopy(B)

    # First pass: collect denominators to find LCM divisor
    divs = []
    for i in range(3):
        A1 = copy.deepcopy(A)
        X = _solve(A1, B1[i])
        if X is None:
            raise ValueError("Singular matrix, cannot generate serial")
        for num in X:
            if num != 0.0:
                fracs = str(Fraction(num).limit_denominator()).split('/')
                if len(fracs) > 1:
                    div = int(fracs[1])
                    divs.append(div)

    if not divs:
        divisor = 1
    else:
        divisor = _lcm(divs)

    # Second pass: build serial
    B[0][0] = divisor
    B[1][1] = divisor
    B[2][2] = divisor
    B1 = copy.deepcopy(B)

    serial = ''
    bin_str = ''

    for i in range(3):
        A1 = copy.deepcopy(A)
        X = _solve(A1, B1[i])
        if X is None:
            raise ValueError("Singular matrix, cannot generate serial")
        for num in X:
            frac_str = str(Fraction(num).limit_denominator())
            numerator_str = frac_str.split('/')[0]
            value = '%X' % abs(int(numerator_str))
            if num < 0:
                bin_str += '1'
            else:
                bin_str += '0'
            serial += value + '.'

    serial += '%X' % divisor + '.'

    bin_str = bin_str[::-1]
    lastnum = 0
    for ch in bin_str:
        lastnum <<= 1
        if ch == '1':
            lastnum += 1

    serial += '%X' % lastnum
    return serial


def verify(name, serial):
    """
    Verify a name/serial pair.
    Checks:
      1. len(name) > 5
      2. len(serial) > 0
      3. serial matches keygen output
    """
    if len(name) <= 5:
        return False
    if len(serial) == 0:
        return False
    try:
        expected = keygen(name)
    except Exception:
        return False
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
