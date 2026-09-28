# Contributing to TradeVelocity

TradeVelocity is an educational matching-engine project. Changes should keep
matching deterministic and performance claims reproducible.

## Set up

Follow the [README](README.md). Install `.[app,test]` for the full
test suite and use `npm ci` in `frontend/` for locked frontend dependencies.

## Make a change

Keep `app.py` and `demoapp.py` as the two application entry files. Put supporting
logic in `src/stock_engine/` and experiment tools in `scripts/` rather than
adding another launcher or dashboard.

1. Create a branch from current `main`, for example
   `git switch -c feature/describe-your-change`.
2. Keep matching logic in the engine and model analysis outside matching
   decisions. Preserve price-time priority, quantities, and index invariants.
3. Add focused regression coverage for changes to engine behavior, persistence,
   validation, or process ownership. Avoid tests that merely repeat the code.
4. Update `CHANGELOG.md`, the relevant documentation, and
   `docs/development-log.md` with the behavior changed and actual verification.
5. Build the frontend, run the relevant tests, and review the diff before
   committing. For a complete check, use the README's validation commands.

## Record each update

Each change-log entry should include its date, purpose, affected modules,
behavior before/after where useful, and verification results. Report known
limitations explicitly. Never invent benchmark timings, model accuracy, live
market data, or tests that were not run.

Use descriptive commits, such as `fix: release server port when launcher stops`.
Git retains the exact committed file differences; prose logs summarize why they
changed. Changes that were never committed cannot have an exact historical diff.

## Files to keep local

Do not commit virtual environments, `node_modules`, frontend builds, TypeScript
build caches, local paper sessions, credentials, or `.env` files. Preserve the
npm lockfile, source, tests, measured benchmark evidence, and relevant guides.

Use one working folder for this application. An existing folder named
`ADSA PROJECT` is the TradeVelocity project itself; a nested copy is unnecessary.
Unrelated `Lab_Assignments/` coursework remains local.

## Benchmarks and data

Benchmark commands must retain their workload, seed, repetition count, Python
version, and platform. Run timing independently of memory tracing. Compare both
correctness and speed, including workloads on which a simple list is faster.

Keep historical provider/source dates and simulated-data labels intact. The
Isolation Forest currently fits and scores one historical window; do not call
its scores calibrated probabilities or unseen-data accuracy.
