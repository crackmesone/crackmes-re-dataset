#!/usr/bin/env python3
"""
Poll a submitted batch until it ends, then collect results into results.jsonl,
merge the no-signal crackmes as has_unique_flag=null, and write the final
combined dataset results_final.jsonl. Prints a status line each poll.
"""
import os, sys, json, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from extract_flags import load_key, OUT, CORPUS  # noqa

BATCH_ID = sys.argv[1] if len(sys.argv) > 1 else json.load(
    open(os.path.join(OUT, "batch_job.json")))["batch_id"]
RESFILE = os.path.join(OUT, "results.jsonl")
FINAL = os.path.join(OUT, "results_final.jsonl")
POLL_EVERY = 90
MAX_WAIT = 6 * 3600


def collect(client, batch_id):
    n = 0
    with open(RESFILE, "w") as out:
        for r in client.messages.batches.results(batch_id):
            row = {"id": r.custom_id}
            if r.result.type == "succeeded":
                msg = r.result.message
                txt = next((b.text for b in msg.content if b.type == "text"), "{}")
                try:
                    row.update(json.loads(txt))
                except Exception:
                    row["parse_error"] = txt[:500]
            else:
                row["error"] = r.result.type
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    return n


def build_final():
    # names for all crackmes
    names = {}
    for l in open(CORPUS):
        r = json.loads(l)
        names[r["id"]] = r.get("name")
    scored = {}
    for l in open(RESFILE):
        r = json.loads(l)
        scored[r["id"]] = r
    no_sig = json.load(open(os.path.join(OUT, "no_signal_ids.json")))
    with open(FINAL, "w") as out:
        for cid, row in scored.items():
            row.setdefault("name", names.get(cid))
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
        for cid in no_sig:
            out.write(json.dumps({
                "id": cid, "name": names.get(cid),
                "has_unique_flag": None, "flag": None, "flag_source": "none",
                "obfuscation": [], "no_flag_reason": "no_signal",
                "confidence": "low", "evidence": "no comments or solution text available",
            }, ensure_ascii=False) + "\n")
    return len(scored), len(no_sig)


def main():
    import anthropic
    client = anthropic.Anthropic(api_key=load_key())
    t0 = time.time()
    while True:
        b = client.messages.batches.retrieve(BATCH_ID)
        c = b.request_counts
        el = int(time.time() - t0)
        print(f"[{el:5}s] status={b.processing_status} "
              f"succeeded={c.succeeded} errored={c.errored} "
              f"processing={c.processing} canceled={c.canceled} expired={c.expired}",
              flush=True)
        if b.processing_status == "ended":
            break
        if time.time() - t0 > MAX_WAIT:
            print("MAX_WAIT exceeded; stopping poll (batch still processing).")
            return
        time.sleep(POLL_EVERY)

    n = collect(client, BATCH_ID)
    ns, nnos = build_final()
    print(f"\ncollected {n} scored results -> {RESFILE}")
    print(f"final dataset: {ns} scored + {nnos} no-signal = {ns+nnos} -> {FINAL}")


if __name__ == "__main__":
    main()
