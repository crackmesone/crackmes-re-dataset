#!/usr/bin/env python3
"""
Static audit of the generated verifier scripts (no execution, no API):
  1) SAFETY  — flag any dangerous imports / calls (deterministic gate)
  2) SHAPE   — does it parse? does it have verify()/keygen()? arity + param names
  3) INTERFACE — guess input nature (key-only / name+serial / multi-arg / unknown)

Writes verifier_audit.jsonl and prints a summary.
"""
import ast, os, json, collections, re

HERE = os.path.dirname(os.path.abspath(__file__))
VDIR = os.path.join(HERE, "verifiers")

# imports that warrant a safety flag (capability to touch the system/network)
DANGER_IMPORTS = {
    "os", "subprocess", "socket", "urllib", "requests", "http", "ftplib",
    "shutil", "ctypes", "cffi", "pickle", "marshal", "pty", "importlib",
    "multiprocessing", "signal", "tempfile", "glob", "webbrowser", "smtplib",
}
# call names that warrant a flag regardless of import
DANGER_CALLS = {"eval", "exec", "compile", "__import__", "system", "popen",
                "remove", "unlink", "rmtree", "rename", "chmod", "spawn",
                "fork", "connect", "urlopen", "call", "run", "Popen", "check_output"}


def analyze(path):
    src = open(path, encoding="utf-8", errors="replace").read()
    rec = {"id": os.path.basename(path)[:-3], "parse_ok": True,
           "fenced": "```" in src, "danger_imports": [], "danger_calls": [],
           "open_write": False, "functions": {}, "has_verify": False,
           "has_keygen": False, "interface": "unknown", "arity": None}
    # markdown/prose contamination breaks execution -> note it
    try:
        tree = ast.parse(src)
    except SyntaxError:
        rec["parse_ok"] = False
        return rec
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mods = ([a.name.split(".")[0] for a in node.names]
                    if isinstance(node, ast.Import)
                    else [(node.module or "").split(".")[0]])
            for m in mods:
                if m in DANGER_IMPORTS and m not in rec["danger_imports"]:
                    rec["danger_imports"].append(m)
        if isinstance(node, ast.Call):
            fn = node.func
            name = getattr(fn, "id", None) or getattr(fn, "attr", None)
            if name in DANGER_CALLS and name not in rec["danger_calls"]:
                rec["danger_calls"].append(name)
            if name == "open":
                for a in list(node.args) + [k.value for k in node.keywords]:
                    if isinstance(a, ast.Constant) and isinstance(a.value, str) \
                       and any(c in a.value for c in ("w", "a", "x", "+")):
                        rec["open_write"] = True
        if isinstance(node, ast.FunctionDef):
            params = [a.arg for a in node.args.args]
            ndefault = len(node.args.defaults)
            required = params[:len(params) - ndefault] if ndefault else params
            rec["functions"][node.name] = {"params": params, "required": required}

    fns = rec["functions"]
    rec["has_verify"] = any(n in fns for n in ("verify",))
    rec["has_keygen"] = any(n in fns for n in ("keygen",))
    # pick the checker: verify > is_valid/validate/check*
    checker = None
    for cand in ("verify", "is_valid", "validate", "check_serial", "check", "check_key"):
        if cand in fns:
            checker = cand; break
    if checker:
        req = fns[checker]["required"]
        # drop a leading 'self' if present
        req = [p for p in req if p != "self"]
        rec["arity"] = len(req)
        names = " ".join(req).lower()
        if rec["arity"] >= 2 and re.search(r"name|user", names):
            rec["interface"] = "name+serial"
        elif rec["arity"] == 1 and re.search(r"serial|key|pass|code|flag|input", names):
            rec["interface"] = "key-only"
        elif rec["arity"] == 1:
            rec["interface"] = "single-arg"
        elif rec["arity"] >= 2:
            rec["interface"] = f"multi-arg({rec['arity']})"
        elif rec["arity"] == 0:
            rec["interface"] = "no-arg"
    rec["checker"] = checker
    return rec


def main():
    files = sorted(f for f in os.listdir(VDIR) if f.endswith(".py"))
    recs = [analyze(os.path.join(VDIR, f)) for f in files]
    with open(os.path.join(HERE, "verifier_audit.jsonl"), "w") as out:
        for r in recs:
            out.write(json.dumps(r, ensure_ascii=False) + "\n")

    n = len(recs)
    print(f"verifier scripts: {n}\n")
    print("=== SHAPE / HEALTH ===")
    print(f"  parse OK            : {sum(r['parse_ok'] for r in recs)}")
    print(f"  DO NOT parse        : {sum(not r['parse_ok'] for r in recs)}")
    print(f"  contain ``` fences  : {sum(r['fenced'] for r in recs)}")
    print(f"  has verify()        : {sum(r['has_verify'] for r in recs)}")
    print(f"  has keygen()        : {sum(r['has_keygen'] for r in recs)}")
    print(f"  no checker found    : {sum(1 for r in recs if r['parse_ok'] and not r.get('checker'))}")

    print("\n=== SAFETY (static) ===")
    di = collections.Counter()
    for r in recs:
        for m in r["danger_imports"]:
            di[m] += 1
    dc = collections.Counter()
    for r in recs:
        for c in r["danger_calls"]:
            dc[c] += 1
    flagged = [r for r in recs if r["danger_imports"] or r["danger_calls"] or r["open_write"]]
    print(f"  scripts with >=1 flag: {len(flagged)}  ({len(flagged)/n*100:.1f}%)")
    print(f"  clean (no flags)     : {n - len(flagged)}")
    print(f"  dangerous imports    : {dict(di)}")
    print(f"  dangerous calls      : {dict(dc)}")
    print(f"  open() for write     : {sum(r['open_write'] for r in recs)}")

    print("\n=== INTERFACE (input nature) ===")
    inter = collections.Counter(r["interface"] for r in recs)
    for k, v in inter.most_common():
        print(f"  {k:18} {v:4}")
    print("\nwrote verifier_audit.jsonl")


if __name__ == "__main__":
    main()
