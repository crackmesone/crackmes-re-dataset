"""QUARANTINED verifier — original contained unsafe operations that could not
be reduced to a pure name/serial check. Reason: loads a native library (algorithm lives in an external DLL)"""
import sys


def verify(*args, **kwargs):
    raise NotImplementedError("unsupported: loads a native library (algorithm lives in an external DLL)")


def keygen(*args, **kwargs):
    raise NotImplementedError("unsupported: loads a native library (algorithm lives in an external DLL)")


if __name__ == "__main__":
    argv = sys.argv[1:]
    if argv and argv[0] == "verify":
        print("0")
    elif argv and argv[0] == "keygen":
        pass  # no pairs — unsupported
    else:
        sys.stderr.write("usage: {} {{keygen|verify <args>}}\n".format(sys.argv[0]))
        sys.exit(2)
