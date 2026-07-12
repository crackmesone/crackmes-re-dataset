#!/usr/bin/env python3
"""
Normalize the free-text obfuscation tags into a controlled vocabulary.
Local only (regex rules) — no API cost.

Reads results_final.jsonl, adds an "obfuscation_classes" list to each record,
writes results_final_normalized.jsonl, and prints the per-class crackme counts.
"""
import json, re, collections, os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "results_final.jsonl")
OUT = os.path.join(HERE, "results_final_normalized.jsonl")

# Ordered canonical classes. Each raw tag is matched against ALL of these
# (multi-label); a tag matching none goes to "Other / unclassified".
CLASSES = [
    ("Commercial protector",      r"themida|vmprotect|winlicense|enigma|armadillo|execryptor|obsidium|safengine|molebox|codevirtualizer|asprotect|pelock|\.net\s*reactor|reactor|confuser|dotfuscator|smartassembly|\.net\s*guard"),
    ("Code virtualization / VM",  r"\bvm\b|virtual\s*machine|virtuali[sz]|byte\s*code|bytecode|p-?code|custom (interpreter|machine)|opcode|interpreter"),
    ("Packer",                    r"\bupx\b|\bfsg\b|aspack|pecompact|mpress|\bmew\b|petite|nspack|telock|pklite|yoda|nspack|exepack|\bpacked\b|packer|unpack|packing"),
    ("Anti-debugging",            r"isdebuggerpresent|checkremotedebugger|ntqueryinformation|ntsetinformation|debugger|anti[-\s]?debug|dbgbreak|dbguiremote|beingdebugged|peb.*debug|\bint3\b|0xcc|ptrace|outputdebugstring|hardware breakpoint|debug register|\bdr[0-7]\b|breakpoint|softice|ntglobalflag|setunhandledexceptionfilter|anti[-\s]?dump|closehandle|findwindow|ollydbg|olly\b|x64dbg|kiuserexceptiondispatcher"),
    ("Anti-VM / sandbox",         r"anti[-\s]?vm|vmware|virtualbox|\bvbox\b|sandbox|hypervisor"),
    ("Anti-disassembly",          r"anti[-\s]?disas|junk\s*(code|byte|instr)|opaque predicate|garbage\s*(code|byte)|fake\s*(jump|instr)|obfuscated\s*(jump|jne|jz|je)|je obfuscation|misalign"),
    ("Self-modifying / runtime decrypt", r"self[-\s]?modif|self[-\s]?decrypt|\bsmc\b|runtime\s*(code\s*)?(decrypt|unpack)|section\s*(encrypt|decrypt)|decrypt.*section|encrypted\s*(section|code)|code encrypt|stage decrypt|on-the-fly|polymorph|metamorph|code mutation|oep hid|writeprocessmemory|virtualalloc.*code|virtualprotect"),
    ("Control-flow obfuscation",  r"control[-\s]?flow|flatten|spaghetti|call stack manipulation|jump table|indirect (jump|call)"),
    ("String / data encryption",  r"string\s*(encrypt|obfusc|encod)|encrypted string|\bxor\b|rc4|encrypted data|data encrypt|cipher"),
    ("Encoding (base64/hex)",     r"base\s*64|base64|base32|hex encod|encoded string|rot13"),
    ("Anti-tamper / integrity",   r"checksum|integrity|crc.*check|anti[-\s]?patch|anti[-\s]?tamper|self[-\s]?check|\btamper"),
    ("Crypto / hash algorithm",   r"\bmd5\b|sha-?\d|sha256|sha1|crc-?32|\baes\b|\btea\b|xtea|blowfish|\bdes\b|\brsa\b|hashing|hash function"),
    ("Timing checks",             r"rdtsc|gettickcount|timing|time\s*check|queryperformance|\bsleep\b"),
    ("Import / API obfuscation",  r"import\s*(resolution|obfusc|hash|table)|getprocaddress|loadlibrary|api\s*hash|dynamic import|iat\b|runtime import"),
    ("Stripped / no symbols",     r"strip|no symbol|symbol.*remov"),
    ("Anti-attach / thread tricks", r"anti[-\s]?thread|thread suspension|suspend thread|anti[-\s]?attach|thread-based|tls callback"),
    ("Exception-based",           r"exception handler|seh\b|veh\b|vectored exception|structured exception"),
    ("Nag / trial",               r"\bnag\b|trial|time.?limit|expire"),
    ("Binary hardening (ASLR/PIE/canary)", r"\baslr\b|\bpie\b|stack canary|stack cookie|\bnx\b|\bdep\b|relro|fortify|no[-\s]?exec"),
    ("Anti-static analysis",      r"anti[-\s]?static|static analysis"),
    ("Custom / generic obfuscation", r"custom obfusc|code obfusc|obfuscator|obfuscated code|heavy obfusc|generic obfusc"),
]
COMPILED = [(name, re.compile(pat, re.I)) for name, pat in CLASSES]


def classify(tag: str):
    hits = [name for name, rx in COMPILED if rx.search(tag)]
    return hits


def main():
    rows = [json.loads(l) for l in open(SRC)]
    per_class = collections.Counter()      # crackmes per class
    raw_total = 0
    raw_unmatched = collections.Counter()
    with open(OUT, "w") as out:
        for r in rows:
            classes = set()
            for tag in (r.get("obfuscation") or []):
                raw_total += 1
                hits = classify(tag)
                if hits:
                    classes.update(hits)
                else:
                    raw_unmatched[tag.strip().lower()] += 1
            r["obfuscation_classes"] = sorted(classes)
            for c in classes:
                per_class[c] += 1
            out.write(json.dumps(r, ensure_ascii=False) + "\n")

    tagged = sum(1 for r in rows if r.get("obfuscation"))
    with_class = sum(1 for r in rows if r.get("obfuscation_classes"))
    print(f"crackmes with >=1 raw tag: {tagged}")
    print(f"crackmes mapped to >=1 class: {with_class}")
    print(f"raw tag mentions: {raw_total}   unmatched: {sum(raw_unmatched.values())} "
          f"({sum(raw_unmatched.values())/raw_total*100:.1f}%)")
    print(f"\n=== crackmes per obfuscation class (multi-label) ===")
    for name, _ in CLASSES:
        c = per_class.get(name, 0)
        if c:
            print(f"  {name:34} {c:5}  ({c/len(rows)*100:4.1f}% of all crackmes)")
    print(f"\ntop 15 still-unmatched raw tags (candidates for new rules):")
    for t, c in raw_unmatched.most_common(15):
        print(f"  {c:4}  {t[:60]}")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
