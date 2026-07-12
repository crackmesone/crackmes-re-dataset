#!/usr/bin/env python3
"""
Phase 2: generate a Python verify()/keygen() script for keygen-style crackmes,
from the algorithm described in the solution write-ups. Reports whether the
algorithm was fully recoverable from the text (hit-rate signal) and tracks
exact token cost.

  python3 phase2_gen.py --limit 15         # preview (real-time), measures hit-rate + cost
  python3 phase2_gen.py --limit 15 --submit-batch   # (full run via batch; omit --limit for all)

Selects the "gated" subset: crackmes whose write-ups look like they contain an
algorithm/source (so generation is grounded, not guessed).
"""
import os, sys, json, re, time, argparse, threading
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from extract_flags import render_user, load_key, has_signal  # noqa

CORPUS = os.path.join(HERE, "corpus.jsonl")
VERIDIR = os.path.join(HERE, "verifiers")
MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 3500
PRICE_IN, PRICE_OUT = 3.00, 15.00

SYSTEM = (
    "You are a reverse-engineering assistant. From the crackme description, "
    "comments, and SOLUTION write-ups, reconstruct the key/serial validation "
    "algorithm and produce a self-contained Python 3 script.\n"
    "The script must define verify(name, serial) -> bool implementing the real "
    "check, and keygen(name) -> serial (or a generator of valid inputs). Base it "
    "ONLY on the algorithm actually shown/described in the text. Mark any gap "
    "with a '# ASSUMPTION:' comment. Do NOT invent an algorithm the text does "
    "not support.\n"
    "Also self-assess: algorithm_recovered = 'full' (algorithm fully determined "
    "from the text), 'partial' (core logic present but with gaps/assumptions), "
    "or 'none' (text does not contain enough to implement the real check)."
)

SCHEMA = {
    "type": "object",
    "properties": {
        "algorithm_recovered": {"type": "string", "enum": ["full", "partial", "none"]},
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
        "language": {"type": "string"},
        "code": {"type": "string"},
        "notes": {"type": "string"},
    },
    "required": ["algorithm_recovered", "confidence", "language", "code", "notes"],
    "additionalProperties": False,
}


def is_keygen(r):
    b = " ".join([r.get("name", "") or "", r.get("info", "") or ""]
                 + [c["text"] for c in r.get("comments", [])]
                 + [s.get("info", "") + " " + s.get("writeup", "") for s in r.get("solutions", [])]).lower()
    name = (r.get("name", "") or "").lower()
    return bool(re.search(r'keygen|write a keygen|make a keygen|serial.{0,25}(from|based on).{0,15}name|name.{0,15}(to|is used).{0,15}(generate|serial)', b)) or 'keygenme' in name or 'keygen-me' in b


def has_code(r):
    b = " ".join(s.get("writeup", "") for s in r.get("solutions", [])).lower()
    return bool(re.search(r'\b(for\s*\(|while\s*\(|def |int main|void |unsigned|0x[0-9a-f]{2,}|sprintf|strlen|xor |crc|sub_|mov )', b))


def select(limit):
    recs = [json.loads(l) for l in open(CORPUS)]
    recs = [r for r in recs if has_signal(r) and is_keygen(r) and has_code(r)]
    recs.sort(key=lambda r: r["id"])            # deterministic order
    if limit:
        recs = recs[::max(1, len(recs) // limit)][:limit]  # even spread, not just longest
    return recs


def build_requests(limit=0):
    recs = select(limit)
    reqs = []
    for rec in recs:
        reqs.append({
            "custom_id": rec["id"],
            "params": {
                "model": MODEL, "max_tokens": MAX_TOKENS, "system": SYSTEM,
                "messages": [{"role": "user", "content": render_user(rec)}],
                "output_config": {"format": {"type": "json_schema", "schema": SCHEMA}},
            },
        })
    return reqs, recs


def submit_batch():
    import anthropic
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request
    reqs, recs = build_requests(0)
    client = anthropic.Anthropic(api_key=load_key())
    batch = client.messages.batches.create(requests=[
        Request(custom_id=r["custom_id"],
                params=MessageCreateParamsNonStreaming(**r["params"]))
        for r in reqs])
    json.dump({"batch_id": batch.id, "count": len(reqs)},
              open(os.path.join(HERE, "phase2_batch_job.json"), "w"), indent=2)
    print(f"submitted phase-2 batch {batch.id} with {len(reqs)} requests")
    print("poll with: python3 phase2_gen.py --poll", batch.id)


def poll_collect(batch_id):
    import anthropic
    client = anthropic.Anthropic(api_key=load_key())
    os.makedirs(VERIDIR, exist_ok=True)
    t0 = time.time()
    while True:
        b = client.messages.batches.retrieve(batch_id)
        c = b.request_counts
        print(f"[{int(time.time()-t0):5}s] {b.processing_status} "
              f"ok={c.succeeded} err={c.errored} proc={c.processing}", flush=True)
        if b.processing_status == "ended":
            break
        if time.time() - t0 > 6 * 3600:
            print("MAX_WAIT exceeded"); return
        time.sleep(90)
    names = {json.loads(l)["id"]: json.loads(l).get("name") for l in open(CORPUS)}
    st = {"full": 0, "partial": 0, "none": 0, "err": 0}
    man = open(os.path.join(HERE, "phase2_manifest.jsonl"), "w")
    for r in client.messages.batches.results(batch_id):
        cid = r.custom_id
        row = {"id": cid, "name": names.get(cid)}
        if r.result.type != "succeeded":
            row["error"] = r.result.type; st["err"] += 1
        else:
            m = r.result.message
            if m.stop_reason == "refusal":
                row["error"] = "refusal"; st["err"] += 1
            else:
                txt = next((b.text for b in m.content if b.type == "text"), "")
                try:
                    d = json.loads(txt)
                    open(os.path.join(VERIDIR, cid + ".py"), "w").write(d.get("code", ""))
                    row.update({k: d.get(k) for k in ("algorithm_recovered", "confidence", "language")})
                    row["notes"] = (d.get("notes") or "")[:200]
                    st[d.get("algorithm_recovered", "none")] += 1
                except Exception:
                    row["error"] = "parse"; st["err"] += 1
        man.write(json.dumps(row, ensure_ascii=False) + "\n")
    man.close()
    print(f"\n=== PHASE 2 COMPLETE ===")
    print(f"  full={st['full']}  partial={st['partial']}  none={st['none']}  err={st['err']}")
    print(f"  verifiers written to {VERIDIR}/  manifest: phase2_manifest.jsonl")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--submit", action="store_true")
    ap.add_argument("--poll", metavar="BATCH_ID")
    args = ap.parse_args()
    if args.submit:
        return submit_batch()
    if args.poll:
        return poll_collect(args.poll)
    os.makedirs(VERIDIR, exist_ok=True)

    recs = select(args.limit)
    total = len(recs)
    print(f"gated keygen subset selected: {total} crackmes")

    import anthropic
    client = anthropic.Anthropic(api_key=load_key())
    lock = threading.Lock()
    st = {"in": 0, "out": 0, "cost": 0.0, "full": 0, "partial": 0, "none": 0, "err": 0}
    manifest = open(os.path.join(HERE, "phase2_preview.jsonl"), "w")

    def work(rec):
        try:
            r = client.messages.create(model=MODEL, max_tokens=MAX_TOKENS, system=SYSTEM,
                messages=[{"role": "user", "content": render_user(rec)}],
                output_config={"format": {"type": "json_schema", "schema": SCHEMA}})
            it, ot = r.usage.input_tokens, r.usage.output_tokens
            if r.stop_reason == "refusal":
                return rec, None, it, ot, "refusal"
            txt = next((b.text for b in r.content if b.type == "text"), "{}")
            return rec, json.loads(txt), it, ot, None
        except Exception as e:
            return rec, None, 0, 0, str(e)[:80]

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for rec, data, it, ot, err in [f.result() for f in as_completed([ex.submit(work, r) for r in recs])]:
            c = it / 1e6 * PRICE_IN + ot / 1e6 * PRICE_OUT
            with lock:
                st["in"] += it; st["out"] += ot; st["cost"] += c
                if err or not data:
                    st["err"] += 1
                    manifest.write(json.dumps({"id": rec["id"], "name": rec.get("name"), "error": err or "empty"}) + "\n")
                    continue
                st[data["algorithm_recovered"]] += 1
                # save the generated code
                code = data.get("code", "")
                open(os.path.join(VERIDIR, rec["id"] + ".py"), "w").write(code)
                manifest.write(json.dumps({"id": rec["id"], "name": rec.get("name"),
                    "algorithm_recovered": data["algorithm_recovered"],
                    "confidence": data["confidence"], "in": it, "out": ot,
                    "notes": data.get("notes", "")[:200]}, ensure_ascii=False) + "\n")
    manifest.close()

    ok = st["full"] + st["partial"]
    print(f"\n=== PHASE-2 PREVIEW RESULT ({total} crackmes) ===")
    print(f"  algorithm fully recovered : {st['full']}")
    print(f"  partial (gaps/assumptions): {st['partial']}")
    print(f"  not recoverable from text : {st['none']}")
    print(f"  refused/error             : {st['err']}")
    print(f"  => usable (full+partial)  : {ok}/{total} = {ok/total*100:.0f}% hit rate")
    avg_in = st["in"] / total; avg_out = st["out"] / total
    print(f"\n  avg tokens/item: in {avg_in:.0f}  out {avg_out:.0f}")
    print(f"  preview cost (real-time): ${st['cost']:.3f}")
    # extrapolate to full gated subset via batch pricing (50% off)
    full_n = len(select(0))
    full_batch = (avg_in * full_n / 1e6 * PRICE_IN + avg_out * full_n / 1e6 * PRICE_OUT) * 0.5
    print(f"\n  full gated subset size: {full_n}")
    print(f"  EXTRAPOLATED full phase-2 cost (batch, 50% off): ${full_batch:.2f}")
    print(f"  (real-time would be ~${full_batch*2:.2f})")


if __name__ == "__main__":
    main()
