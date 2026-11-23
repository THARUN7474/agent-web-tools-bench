"""One-command benchmark runner.

Usage: python bench.py --vendors all --tasks tasks.yaml --out results/
Writes results/results.json (raw, auditable) and results/report.md (ranked table).
"""
import argparse
import json
import os
import time
import urllib.request
from statistics import median

import yaml

from judges import judge


def call_vendor(name: str, cfg: dict, task: dict) -> dict:
    """One vendor, one task. Never raises: failures are data."""
    key = os.environ.get(cfg["env_key"], "")
    if not key:
        return {"ok": False, "error": f"missing env {cfg['env_key']}", "latency_s": 0}
    ep = cfg["endpoints"].get(task["category"])
    if not ep:
        return {"ok": False, "error": f"no {task['category']} endpoint", "latency_s": 0}
    url = cfg["base_url"] + ep["path"].replace("{url}", task.get("url", ""))
    payload = {k: v for k, v in task.items() if k in ("url", "query", "schema")}
    headers = {"Content-Type": "application/json"}
    if "auth_header" in cfg:
        h, v = cfg["auth_header"].split(": ", 1)
        headers[h] = v.format(key=key)
    else:
        headers["Authorization"] = f"Bearer {key}"
    t0 = time.monotonic()
    try:
        req = urllib.request.Request(
            url, method=ep.get("method", "POST"),
            data=None if ep.get("method") == "GET" else json.dumps(payload).encode(),
            headers=headers)
        with urllib.request.urlopen(req, timeout=90) as r:
            body = r.read().decode("utf-8", "replace")
        ok, err = True, None
    except Exception as e:  # HTTP errors, timeouts: all recorded, none hidden
        body, ok, err = "", False, f"{type(e).__name__}: {e}"
    return {"ok": ok, "error": err, "latency_s": round(time.monotonic() - t0, 2),
            "output": body[:20000]}


def pct(values, p):
    if not values:
        return None
    s = sorted(values)
    return round(s[min(len(s) - 1, int(len(s) * p))], 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vendors", default="all")
    ap.add_argument("--tasks", default="tasks.yaml")
    ap.add_argument("--out", default="results")
    a = ap.parse_args()

    tasks = yaml.safe_load(open(a.tasks))
    cfg = yaml.safe_load(open("vendors.yaml"))
    names = list(cfg["vendors"]) if a.vendors == "all" else a.vendors.split(",")

    runs = []
    for task in tasks:
        for name in names:
            v = cfg["vendors"][name]
            print(f"[run] {task['id']} <- {name}", flush=True)
            r = call_vendor(name, v, task)
            scored = judge(task, r["output"]) if r["ok"] else {"score": 0, "why": r["error"]}
            runs.append({"task": task["id"], "category": task["category"], "vendor": name,
                         "ok": r["ok"], "latency_s": r["latency_s"],
                         "cost_usd": v.get("cost_usd_per_task"),
                         "judge_score": scored["score"], "judge_why": scored["why"],
                         "output_preview": r["output"][:2000]})

    os.makedirs(a.out, exist_ok=True)
    meta = {"pricing_checked": cfg.get("pricing_checked"),
            "note": "single-region client (India); small n; deltas <0.5 judge points are noise"}
    with open(f"{a.out}/results.json", "w") as f:
        json.dump({"meta": meta, "runs": runs}, f, indent=2)

    lines = ["# Benchmark report", "",
             "| Vendor | Avg judge (0-5) | Success | p50 latency | p95 latency | Cost/task |",
             "|---|---|---|---|---|---|"]
    for name in names:
        rs = [r for r in runs if r["vendor"] == name]
        scores = [r["judge_score"] for r in rs if r["judge_score"] is not None]
        lat = [r["latency_s"] for r in rs if r["ok"]]
        succ = f"{sum(r['ok'] for r in rs)}/{len(rs)}"
        lines.append(f"| {name} | {round(sum(scores)/max(len(scores),1), 2)} | {succ} | "
                     f"{pct(lat, .5)} | {pct(lat, .95)} | ${cfg['vendors'][name].get('cost_usd_per_task')} |")
    with open(f"{a.out}/report.md", "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"done -> {a.out}/results.json, {a.out}/report.md")


if __name__ == "__main__":
    main()
