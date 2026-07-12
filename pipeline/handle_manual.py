#!/usr/bin/env python3
"""
Handle the 63 dangerous/broken verifiers WITHOUT spending on the API:
  - strip any demo __main__ block (that's where most danger lives),
  - re-scan the remaining code for real danger,
  - if now clean AND it still parses with verify/keygen -> wrap it (salvaged),
  - otherwise -> replace with a safe QUARANTINE stub (verify/keygen raise,
    `verify` prints 0), marked unsupported with the reason.
Writes into verifiers_std/ alongside the deterministically-wrapped ones.
"""
import ast, os, json, re
import standardize_verifiers as S

HERE = os.path.dirname(os.path.abspath(__file__))
VDIR = os.path.join(HERE, "verifiers")
ODIR = os.path.join(HERE, "verifiers_std")
MANUAL = json.load(open(os.path.join(HERE, "manual_set.json")))
DETAIL = json.load(open(os.path.join(HERE, "manual_detail.json")))

CTYPES_LOAD = {"CDLL", "WinDLL", "OleDLL", "PyDLL", "cdll", "windll", "oledll",
               "pydll", "LoadLibrary", "LoadLibraryA", "LoadLibraryW", "memmove",
               "memset", "cast", "string_at"}
REAL_DANGER = {"system", "popen", "remove", "unlink", "rmtree", "rename", "chmod",
               "spawn", "fork", "connect", "urlopen", "Popen", "call", "run",
               "check_output", "__import__", "startfile", "kill"}


def danger_of(tree):
    d = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            attr = getattr(fn, "attr", None); name = getattr(fn, "id", None)
            owner = getattr(getattr(fn, "value", None), "id", None)
            call = attr or name
            if call in REAL_DANGER and not (call == "system" and owner == "platform"):
                d.append(call)
            if call in CTYPES_LOAD:
                d.append("ctypes:" + call)
            if name == "open":
                for a in list(node.args) + [k.value for k in node.keywords]:
                    if isinstance(a, ast.Constant) and isinstance(a.value, str) \
                       and any(c in a.value for c in ("w", "a", "x", "+")):
                        d.append("open_write")
    return sorted(set(d))


STUB = '''"""QUARANTINED verifier — original contained unsafe operations that could not
be reduced to a pure name/serial check. Reason: %(reason)s"""
import sys


def verify(*args, **kwargs):
    raise NotImplementedError("unsupported: %(reason)s")


def keygen(*args, **kwargs):
    raise NotImplementedError("unsupported: %(reason)s")


if __name__ == "__main__":
    argv = sys.argv[1:]
    if argv and argv[0] == "verify":
        print("0")
    elif argv and argv[0] == "keygen":
        pass  # no pairs — unsupported
    else:
        sys.stderr.write("usage: {} {{keygen|verify <args>}}\\n".format(sys.argv[0]))
        sys.exit(2)
'''


def reason_for(danger):
    if any(x.startswith("ctypes:") for x in danger):
        return "loads a native library (algorithm lives in an external DLL)"
    if any(x in ("urlopen", "connect") for x in danger):
        return "requires live network/server-side validation"
    if any(x in ("run", "Popen", "call", "check_output", "system", "__import__") for x in danger):
        return "spawns external processes / dynamic execution"
    if "open_write" in danger:
        return "reads/writes an external file (e.g. keyfile) not expressible as CLI args"
    return "unsafe operations not reducible to a pure check"


def main():
    salvaged = quarantined = broke = 0
    manifest = []
    for cid in MANUAL:
        src_path = os.path.join(VDIR, cid + ".py")
        src = open(src_path, encoding="utf-8", errors="replace").read()
        stripped = S.strip_old_main(src)
        status = None
        try:
            tree = ast.parse(stripped)
            fns = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
            residual = danger_of(tree)
            if not residual and "verify" in fns and "keygen" in fns:
                # salvage: core is clean once demo main removed
                params = [a.arg for a in fns["keygen"].args.args if a.arg != "self"]
                ndef = len(fns["keygen"].args.defaults)
                req = params[:len(params) - ndef] if ndef else params
                rec = {"functions": {"keygen": {"params": params, "required": req}},
                       "interface": "name+serial"}
                out = stripped.rstrip() + S.build_wrapper(rec)
                ast.parse(out)  # verify it parses
                open(os.path.join(ODIR, cid + ".py"), "w").write(out)
                status = "salvaged"; salvaged += 1
            else:
                raise ValueError("residual danger or missing fns")
        except Exception:
            reason = reason_for(DETAIL.get(cid, {}).get("danger", [])) \
                if DETAIL.get(cid, {}).get("cat") == "dangerous" else "script did not parse / incomplete generation"
            open(os.path.join(ODIR, cid + ".py"), "w").write(STUB % {"reason": reason})
            status = "quarantined"; quarantined += 1
            if DETAIL.get(cid, {}).get("cat") == "broken":
                broke += 1
        manifest.append({"id": cid, "handling": status})
    json.dump(manifest, open(os.path.join(HERE, "manual_handled.json"), "w"))
    print(f"salvaged (core clean after stripping demo main): {salvaged}")
    print(f"quarantined (unsupported stub)               : {quarantined}  (of which broken: {broke})")


if __name__ == "__main__":
    main()
