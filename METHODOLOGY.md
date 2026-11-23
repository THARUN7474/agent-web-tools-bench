# Methodology

## Principles

1. **Reproducible over clever.** Every run is one command, seeded task set,
   raw JSON kept next to the summary.
2. **Judge the output an agent would get.** Not the marketing page, not the
   SDK ergonomics - the payload an agent receives and must act on.
3. **Declare what we cannot measure.** Free-tier rate limits, regional
   latency, and pricing changes are noted per run, not hidden.

## Task design

Tasks are fixed in `tasks.yaml` and versioned with the repo. Each task has an
expected-answer rubric note so the judge scores against ground truth, not vibes.
Pages are chosen to be stable (docs, Wikipedia, company about pages) so runs
weeks apart stay comparable; drift in a target page is itself logged.

## LLM-as-judge rubric (0-5)

- 5: complete, correct, directly usable by an agent with no cleanup
- 4: correct with minor noise (boilerplate, truncation)
- 3: partially correct or incomplete but usable with retries
- 2: mostly unusable (wrong page, heavy noise)
- 0-1: missing, wrong, or hallucinated

Judge outputs include a one-line justification, kept in `results.json` so any
score can be audited. A score without its justification is invalid.

## Metrics

- Latency: wall time of the API call, p50/p95 per vendor per category.
- Cost: per-task USD from the vendor's public pricing page at run date;
  the pricing URL and date are recorded in `results.json`.
- Success: response 2xx AND output parses AND (for structured tasks) schema
  validates.

## Known limits

Single-region client (India), free/low tiers, small n per category. Treat
deltas under 0.5 judge points as noise.
