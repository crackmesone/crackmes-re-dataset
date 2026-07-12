#!/usr/bin/env python3
"""
Live runner: real-time concurrent Sonnet 4.6 calls with running progress and
exact cost tracking (from each response's token usage). Writes results
incrementally so it is resumable.

  python3 run_live.py --limit 20 --sample     # 20 richest-signal crackmes -> results_sample.jsonl
  python3 run_live.py                          # everything with signal    -> results.jsonl
  python3 run_live.py --resume                 # skip ids already in the out file

Reads the API key from key.txt (or ANTHROPIC_API_KEY). Nothing else contacts
the network.
"""
import os, sys, json, time, argparse, threading
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from extract_flags import SYSTEM, SCHEMA, render_user, has_signal  # noqa
MODEL = "claude-sonnet-4-6"  # overridable via --model

ROOT = os.path.dirname(HERE)
CORPUS = os.path.join(HERE, "corpus.jsonl")

# real-time (non-batch) Sonnet 4.6 pricing per 1M tokens
PRICE_IN, PRICE_OUT = 3.00, 15.00
MAX_TOKENS = 1024


def load_key():
    # Prefer key.txt over any stale exported ANTHROPIC_API_KEY that would shadow it.
    p = os.path.join(ROOT, "key.txt")
    if os.path.exists(p):
        k = open(p).read().strip()
        if k:
            return k
    k = os.environ.get("ANTHROPIC_API_KEY")
    if k:
        return k
    sys.exit("No API key: provide key.txt or set ANTHROPIC_API_KEY")


def signal_weight(rec):
    """Prefer records with real writeup text for the sample."""
    w = 0
    for s in rec.get("solutions", []):
        w += len(s.get("writeup", "")) + len(s.get("info", "")) * 2
    w += sum(len(c["text"]) for c in rec.get("comments", []))
    return w


def _blob(rec):
    return " ".join([rec.get("info", "")]
                    + [c["text"] for c in rec.get("comments", [])]
                    + [s.get("info", "") + s.get("writeup", "") for s in rec.get("solutions", [])]).lower()


def load_records(limit, sample, resume, out_path, contains=None):
    recs = [json.loads(l) for l in open(CORPUS)]
    recs = [r for r in recs if has_signal(r)]
    if contains:
        terms = [t.strip().lower() for t in contains.split("|")]
        recs = [r for r in recs if any(t in _blob(r) for t in terms)]
    if sample:
        recs.sort(key=signal_weight, reverse=True)
    done = set()
    if resume and os.path.exists(out_path):
        for l in open(out_path):
            try:
                done.add(json.loads(l)["id"])
            except Exception:
                pass
    recs = [r for r in recs if r["id"] not in done]
    if limit:
        recs = recs[:limit]
    return recs, len(done)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--sample", action="store_true",
                    help="order by richest signal (for previews)")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--out", default=None)
    ap.add_argument("--contains", default=None,
                    help="only records whose text contains one of these '|'-separated terms")
    args = ap.parse_args()

    out_path = args.out or os.path.join(
        HERE, "results_sample.jsonl" if args.sample and args.limit else "results.jsonl")
    recs, already = load_records(args.limit, args.sample, args.resume, out_path, args.contains)
    total = len(recs)
    if total == 0:
        print("nothing to do (all done or no signal).")
        return

    import anthropic
    client = anthropic.Anthropic(api_key=load_key())

    lock = threading.Lock()
    state = {"n": 0, "ok": 0, "err": 0, "in": 0, "out": 0, "cost": 0.0}
    t0 = time.time()
    fout = open(out_path, "a")

    def work(rec):
        user = render_user(rec)
        try:
            resp = client.messages.create(
                model=MODEL, max_tokens=MAX_TOKENS, system=SYSTEM,
                messages=[{"role": "user", "content": user}],
                output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
            )
            it, ot = resp.usage.input_tokens, resp.usage.output_tokens
            row = {"id": rec["id"], "name": rec.get("name")}
            if resp.stop_reason == "refusal":
                row["error"] = "refusal"
            else:
                txt = next((b.text for b in resp.content if b.type == "text"), "{}")
                try:
                    row.update(json.loads(txt))
                except Exception:
                    row["parse_error"] = txt[:400]
            return row, it, ot, None
        except Exception as e:
            return {"id": rec["id"], "name": rec.get("name"), "error": str(e)[:200]}, 0, 0, e

    def render_progress():
        el = time.time() - t0
        rate = state["n"] / el if el else 0
        eta = (total - state["n"]) / rate if rate else 0
        bar = f"[{state['n']}/{total}]"
        sys.stdout.write(
            f"\r{bar} ok={state['ok']} err={state['err']} "
            f"tok(in/out)={state['in']:,}/{state['out']:,} "
            f"spent=${state['cost']:.4f}  {rate:.1f}/s  ETA {eta:5.0f}s   ")
        sys.stdout.flush()

    print(f"running {total} crackmes on {MODEL} (real-time), {args.workers} workers")
    print(f"output -> {out_path}   ({already} already done)\n")

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(work, r) for r in recs]
        for fut in as_completed(futs):
            row, it, ot, err = fut.result()
            c = it / 1e6 * PRICE_IN + ot / 1e6 * PRICE_OUT
            with lock:
                state["n"] += 1
                state["in"] += it
                state["out"] += ot
                state["cost"] += c
                state["ok"] += 0 if ("error" in row or "parse_error" in row) else 1
                state["err"] += 1 if ("error" in row or "parse_error" in row) else 0
                fout.write(json.dumps(row, ensure_ascii=False) + "\n")
                fout.flush()
                render_progress()
    fout.close()
    print("\n\n=== done ===")
    print(f"processed {state['n']}  ok {state['ok']}  err {state['err']}")
    print(f"tokens in/out: {state['in']:,} / {state['out']:,}")
    print(f"TOTAL COST: ${state['cost']:.4f}")


if __name__ == "__main__":
    main()
