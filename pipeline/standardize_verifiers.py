#!/usr/bin/env python3
"""
Deterministically wrap the CLEAN, parsing verifier scripts with the standard
keygen/verify CLI contract. Flagged/broken scripts are handled by the LLM
sanitize batch instead (skipped here). Outputs to verifiers_std/.
"""
import ast, os, json, re

HERE = os.path.dirname(os.path.abspath(__file__))
VDIR = os.path.join(HERE, "verifiers")
ODIR = os.path.join(HERE, "verifiers_std")
AUDIT = {json.loads(l)["id"]: json.loads(l) for l in open(os.path.join(HERE, "verifier_audit.jsonl"))}
MANUAL = set(json.load(open(os.path.join(HERE, "manual_set.json"))))  # handled by hand instead

SAMPLE = ["alice", "bob", "Kevin", "test123", "admin",
          "crackme", "john_doe", "w1nner", "root", "dragon"]

WRAPPER = '''

# ===== standardized CLI (auto-added) =====
def _cli_norm(_x):
    if isinstance(_x, bytes):
        return _x.hex()
    if isinstance(_x, (list, tuple)):
        return " ".join(_cli_norm(_i) for _i in _x)
    return str(_x)


def _cli_main():
    import sys
    _SAMPLE = %(sample)r
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
            print(%(kg_print)s)
            n += 1
            if n >= 10:
                break
    elif mode == "verify":
        try:
            print("1" if verify(*argv[1:]) else "0")
        except Exception:
            print("0")
    else:
        sys.stderr.write("usage: {} {{keygen|verify <args>}}\\n".format(sys.argv[0]))
        sys.exit(2)


if __name__ == "__main__":
    _cli_main()
'''


def strip_old_main(src: str) -> str:
    """Remove a trailing `if __name__ == '__main__':` block."""
    m = re.search(r"\nif\s+__name__\s*==\s*['\"]__main__['\"]\s*:", src)
    return src[:m.start()] if m else src.rstrip()


def keygen_arity(rec):
    fns = rec.get("functions", {})
    kg = fns.get("keygen")
    if not kg:
        return None
    req = [p for p in kg["required"] if p != "self"]
    return len(req)


def build_wrapper(rec):
    ar = keygen_arity(rec)
    key_only = rec.get("interface") in ("key-only", "single-arg") or ar == 0
    kg_print = "_sv" if key_only else "_nm, _sv"        # "key" vs "username serial"
    return WRAPPER % dict(sample=SAMPLE, kg_print=kg_print)


def main():
    os.makedirs(ODIR, exist_ok=True)
    done = skipped = 0
    for f in sorted(os.listdir(VDIR)):
        if not f.endswith(".py"):
            continue
        cid = f[:-3]
        rec = AUDIT.get(cid, {})
        if cid in MANUAL or not rec.get("parse_ok") or not rec.get("has_verify") or not rec.get("has_keygen"):
            skipped += 1               # -> hand-fixed in-session
            continue
        src = open(os.path.join(VDIR, f), encoding="utf-8", errors="replace").read()
        out = strip_old_main(src) + build_wrapper(rec)
        # sanity: must still parse
        try:
            ast.parse(out)
        except SyntaxError:
            skipped += 1
            continue
        open(os.path.join(ODIR, f), "w").write(out)
        done += 1
    print(f"deterministically standardized (clean): {done}")
    print(f"deferred to LLM sanitize (flagged/broken): {skipped}")


if __name__ == "__main__":
    main()
