#!/usr/bin/env python3
"""
Sub-classify the anti-debugging methods and packer names from the raw tags.
Local only. Enriches results_final_normalized.jsonl with:
  antidebug_methods : [normalized method names]
  packers           : [normalized packer names]
and prints the distributions.
"""
import json, re, collections, os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "results_final_normalized.jsonl")
OUT = os.path.join(HERE, "results_final_normalized.jsonl")  # in place

ANTIDEBUG = [
    ("IsDebuggerPresent",              r"isdebuggerpresent"),
    ("CheckRemoteDebuggerPresent",     r"checkremotedebugger"),
    ("NtQueryInformationProcess",      r"ntqueryinformation|queryinformationprocess|debugport|processdebug"),
    ("PEB BeingDebugged / NtGlobalFlag", r"beingdebugged|peb.*(debug|flag)|ntglobalflag|\bpeb\b"),
    ("ptrace (Linux)",                 r"ptrace"),
    ("INT3 / 0xCC breakpoint scan",    r"int3|0xcc|software breakpoint|breakpoint scan|scan.*breakpoint"),
    ("Hardware breakpoints (DRx)",     r"hardware breakpoint|debug register|\bdr[0-7]\b|getthreadcontext|setthreadcontext"),
    ("Timing (rdtsc/GetTickCount)",    r"rdtsc|gettickcount|timing|queryperformance|time.?check|clock"),
    ("Debugger/tool window detection", r"softice|ollydbg|\bolly\b|x64dbg|x32dbg|findwindow|window.*(detect|name)|process.*(enum|name).*debug|scylla|cheat engine"),
    ("OutputDebugString",              r"outputdebugstring"),
    ("Exception-based (SEH/VEH/INT2D)", r"exception.*debug|setunhandledexceptionfilter|kiuserexception|int\s*2d|0x2d|seh.*debug|veh.*debug"),
    ("CloseHandle invalid-handle",     r"closehandle"),
    ("DbgBreakPoint/DbgUiRemoteBreakin patch", r"dbgbreak|dbguiremote"),
    ("Self-debug / block debugger",    r"debugactiveprocess|self[-\s]?debug|ntsetinformationthread|hidefromdebugger|threadhidefromdebugger|hide from debugger"),
    ("TLS callback",                   r"tls callback"),
    ("Anti-dump",                      r"anti[-\s]?dump"),
    ("Parent-process check",           r"parent process|explorer\.exe.*parent|ppid"),
]

PACKERS = [
    ("UPX",        r"\bupx\b"),
    ("FSG",        r"\bfsg\b"),
    ("ASPack",     r"\baspack\b"),
    ("PECompact",  r"pecompact"),
    ("MPRESS",     r"mpress"),
    ("MEW",        r"\bmew\b"),
    ("Petite",     r"\bpetite\b"),
    ("tElock",     r"telock"),
    ("PKLite",     r"pklite"),
    ("NSPack",     r"nspack"),
    ("Yoda",       r"yoda"),
    ("exepack",    r"exepack"),
    ("Other named (Morphine/Neolite/PEtite…)", r"morphine|neolite|packman|mkfpack|kkrunchy"),
]

CONTROLFLOW = [
    ("Control-flow flattening (CFF)",   r"flatten|\bcff\b"),
    ("Indirect / computed jumps & calls", r"indirect (jump|call)|computed (jump|call|target)|jump table|function table|cmov.*jump|call target"),
    ("Return-address / stack-based",    r"\bret\b.*(jump|control|obfusc)|return address|push/?call|push.*call.*instead|stack-based control"),
    ("Exception / interrupt-based",     r"exception.*control|control.*exception|interrupt handler|int\s*[12]\b|int\s*2d"),
    ("State machine / dispatcher",      r"state machine|dispatcher|desynchroniz"),
    ("Spaghetti / junk-branch",         r"spaghetti|junk.*(branch|jump)|always[-\s]?taken|opaque"),
]

ADC = [(n, re.compile(p, re.I)) for n, p in ANTIDEBUG]
PKC = [(n, re.compile(p, re.I)) for n, p in PACKERS]
CFC = [(n, re.compile(p, re.I)) for n, p in CONTROLFLOW]


def match_all(tags, compiled):
    hits = set()
    for t in tags:
        for name, rx in compiled:
            if rx.search(t):
                hits.add(name)
    return sorted(hits)


def main():
    rows = [json.loads(l) for l in open(SRC)]
    ad_dist = collections.Counter()
    pk_dist = collections.Counter()
    cf_dist = collections.Counter()
    ad_generic = pk_generic = cf_generic = 0
    for r in rows:
        tags = r.get("obfuscation") or []
        classes = r.get("obfuscation_classes") or []
        adm = match_all(tags, ADC)
        pks = match_all(tags, PKC)
        cfm = match_all(tags, CFC)
        r["antidebug_methods"] = adm
        r["packers"] = pks
        r["controlflow_methods"] = cfm
        if "Anti-debugging" in classes:
            for m in adm:
                ad_dist[m] += 1
            if not adm:
                ad_generic += 1
        if "Packer" in classes:
            for m in pks:
                pk_dist[m] += 1
            if not pks:
                pk_generic += 1
        if "Control-flow obfuscation" in classes:
            for m in cfm:
                cf_dist[m] += 1
            if not cfm:
                cf_generic += 1

    with open(OUT, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    ad_total = sum(1 for r in rows if "Anti-debugging" in (r.get("obfuscation_classes") or []))
    pk_total = sum(1 for r in rows if "Packer" in (r.get("obfuscation_classes") or []))
    print(f"=== ANTI-DEBUGGING methods (of {ad_total} anti-debug crackmes) ===")
    for m, _ in ANTIDEBUG:
        if ad_dist[m]:
            print(f"  {m:42} {ad_dist[m]:4}")
    print(f"  {'(named method not resolved / generic)':42} {ad_generic:4}")
    print(f"\n=== PACKERS (of {pk_total} packed crackmes) ===")
    seen = set()
    for m, _ in PACKERS:
        if pk_dist[m] and m not in seen:
            seen.add(m); print(f"  {m:42} {pk_dist[m]:4}")
    print(f"  {'(named packer not resolved / generic)':42} {pk_generic:4}")

    cf_total = sum(1 for r in rows if "Control-flow obfuscation" in (r.get("obfuscation_classes") or []))
    print(f"\n=== CONTROL-FLOW obfuscation methods (of {cf_total} crackmes) ===")
    for m, _ in CONTROLFLOW:
        if cf_dist[m]:
            print(f"  {m:42} {cf_dist[m]:4}")
    print(f"  {'(generic obfuscated control flow, no mechanism)':42} {cf_generic:4}")


if __name__ == "__main__":
    main()
