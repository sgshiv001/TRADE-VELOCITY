# TradeVelocity AI calibration v3 — current controlled test report

Date: **1 October 2026 (India time)**. App **0.3.3**.

1. **Previous issue repaired.** A new fixed raw-count envelope catches the
   former high-volume seed-2009 miss even when price change is zero. Forest
   alerts now require corroborating robust feature deviation, reducing noisy
   forest-only alarms. The original small repetitive-baseline miss still passes.

2. **Method.** The first 24 of 40 per-symbol executions fit the forest and
   median/MAD statistics. The following 16 calibrate cutoffs without refitting.
   Positive count/depth features are logged for forest/robust scoring; a separate
   raw-count envelope uses the fixed 40-row maximum plus one. Any confirmed
   forest, robust guard, or count-envelope exceedance requests human review.
   Scale floors and feature transforms are fixed design choices. Severity is
   relative to fixed thresholds, not a probability. Reports never change orders.

3. **Selected parameters.** Forest margin **0.08**, robust floor **8.0**, padding
   **1.0**, forest confirmation **4.0**, size multiplier **20.0**. A 54-candidate
   grid selected these on development seeds 100–107 (48 streams), maximizing
   recall within the 2% development false-alert budget, then minimizing false
   alerts and preferring conservative cutoffs. The budget is not a statistical
   guarantee. Counts above 20 times the fixed baseline maximum-plus-one can
   flag even if the log/MAD response is below eight.

4. **New held-out data.** The old seeds 2000–2015 are now regression evidence,
   not untouched evaluation. A newly reserved set, seeds **3000–3031**, was
   generated only after selection. Six profiles × 32 seeds = **192 streams**.
   Each has 40 baseline observations, 80 normal controls, and eight extreme
   injected deviations. Data comes from actual in-memory matching commands;
   no real user sessions are read or seeded. The same six profile generators
   remain synthetic; new seeds do not establish a new real-market distribution.

5. **Fresh controlled results.** TP **1,536**, FP **0**, FN **0**, TN **15,360**.
   Precision, recall, and F1 are **100% on this finite synthetic test set**;
   observed false-positive rate is **0%**. Each profile detected 256/256
   deviations; each deviation kind detected 192/192. The run reproduced the
   same settings and confusion counts. Zero observed errors is not a promise
   of zero future errors or real-world fraud accuracy.

6. **Regression results.** The formerly held-out set now detects **768/768**
   deviations with **0/7,680** normal controls falsely flagged. This includes
   the previous miss and all six earlier false-alert observations. Development
   also produced TP 384, FP 0, FN 0, TN 3,840. These sets are no longer fresh
   evidence about unseen behavior.

7. **Detector attribution.** On the new held-out set, **1,527** deviations
   trigger explicit guards alone, **nine** trigger guards plus confirmed forest,
   and **none** trigger confirmed forest alone. Do not present these results
   as standalone Isolation Forest accuracy. The comparison old forest-only
   method detected 531/1,536 deviations, missed 1,005, and falsely flagged
   1,061/15,360 controls. This is a complete-pipeline comparison, not ablation.

8. **Scope and limits.** Repetitive/constant profiles repeat across seeds, so
   stream counts are not independent statistical replications. Deviations are
   extreme and follow in a fixed order, affecting later price changes. Poisoned
   baselines, normal regime shifts, subtle abuse, and behavior in unfilled or
   cancelled orders remain unvalidated. The first 40 observations are assumed
   normal. Depth covers only the top 30 levels. Real fraud prevalence is not
   represented. Daily-history anomaly analysis remains separate and in-sample.

9. **Evidence.** [Current raw measurements](../benchmarks/ai-calibration.json)
   retain candidates, selected settings, protocol, per-profile/per-kind results,
   attribution, error cases, and environment. The prior v2 result is preserved
   in [its archived report](ai-calibration-v2-report.md) and
   [archived measurements](../benchmarks/ai-calibration-v2.json), not erased.
   Runtime settings are in `src/stock_engine/data/watchdog-calibration.json`;
   tests require them to match selection. Python 3.14.7, scikit-learn 1.9.1,
   Windows 11 x64 were used; other versions can change numeric outputs.

10. **Reproduce.** Run `.\.venv\Scripts\python.exe scripts/calibrate_ai.py` from
    the project root. This generates the measurement artifact but does not
    silently change runtime parameters. Run `python -m pytest -q -ra`, the
    frontend browser suite, and packaged `--smoke-test` for application checks.
    See [the completion checklist](completion-report.md) for final test counts,
    Windows packaging, security tooling, and external limitations.

Keep evaluation separate as described in
[scikit-learn's leakage guidance](https://scikit-learn.org/stable/common_pitfalls.html).
The [Isolation Forest reference](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html)
documents its scores; they are not fraud probabilities. Any future retuning
informed by this report needs another untouched evaluation set.
