# agent-web-tools-bench

An independent, reproducible micro-benchmark comparing web-data APIs for AI-agent use.

When an agent needs to read the web - extract a page, search and answer, or pull
structured data - which vendor API should it call? This repo measures that instead
of guessing: a fixed task suite, LLM-as-judge scoring, hard metrics (latency, cost,
success rate), and one-command reproducible runs.

Inspired by the open-benchmarks idea: evaluations agents can trust and cite.

## Vendors covered

Configured in `vendors.yaml`. Current adapters: Firecrawl, Tavily, Exa, Jina Reader.
Each adapter is a plain HTTP wrapper with a per-task cost estimate, so adding a
vendor is one config block.

## Task suite

`tasks.yaml` holds 9 tasks across three categories:

- **extract** - pull clean content from a real page
- **search-answer** - answer a question with a cited source
- **structured** - return data matching a JSON schema

## Metrics

- **Quality (0-5)** - LLM-as-judge scoring against the rubric in `METHODOLOGY.md`
- **Latency** - end-to-end p50/p95 per vendor per category
- **Cost** - per-task USD estimate from each vendor's public pricing
- **Success rate** - valid response / parseable output / schema match

## Run it

```bash
pip install -r requirements.txt
export FIRECRAWL_API_KEY=... TAVILY_API_KEY=... EXA_API_KEY=... JINA_API_KEY=...
export JUDGE_API_KEY=...        # any OpenAI-compatible endpoint
python bench.py --vendors all --tasks tasks.yaml --out results/
```

Outputs `results/results.json` (raw) and `results/report.md` (ranked table).

## Status

Framework complete; results are published here after full keyed runs. No
vendor pays for or reviews this benchmark. Methodology: see `METHODOLOGY.md`.
