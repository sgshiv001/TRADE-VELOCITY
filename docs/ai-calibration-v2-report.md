# TradeVelocity AI calibration v2 — archived test report

Date: **1 October 2026 (India time)**. Application: **0.3.2**.
Detector: **execution-watchdog-v2**.

This is preserved historical evidence, superseded by the
[current v3 report](ai-calibration-report.md). Its former held-out seeds are now
regression cases. The commands below describe the v2 source state, not the
current evaluator, which generates v3 measurements. The original artifact is
retained as `benchmarks/ai-calibration-v2.json`.

## Outcome

The execution watchdog is now a calibrated hybrid: Isolation Forest plus
explicit robust-deviation guards. The previously missed 5,000-share execution
at 130 after a repetitive small-order baseline is detected in Python, the
browser, and the packaged Windows application. Monitoring remains advisory;
it does not block orders, change prices, or alter matching records.

On the controlled held-out evaluation, **767 of 768 injected deviations were
detected**, with **6 false alerts among 7,680 normal controls**. One scaled
high-volume case remains undetected and is recorded below. This is **not
real-market fraud accuracy**, and the scores are **not probabilities**.

## What changed

- Keep the first 40 executed-order observations as a fixed per-symbol baseline:
  24 fit the model/statistics; 16 separate observations calibrate cutoffs.
  Only observations 41 onward are scored.
- Log-transform positive quantity, fill-count, submitted-quantity, and depth
  features. Keep price-change percentage and depth imbalance unlogged.
- Fit a 150-tree Isolation Forest with seed 42. Derive its review cutoff from
  the most unusual calibration observation plus a selected margin.
- Add median/MAD deviation guards with fixed minimum scales, avoiding division
  by zero and disproportionate responses to tiny changes in constant features.
  Derive the guard cutoff from the calibration maximum plus padding, subject
  to a selected minimum. Either detector can request review.
- Display detector names, fixed-cutoff severity, and baseline limitations.
  Later activity does not retrospectively change earlier severity scores.
- Cache fixed baseline models and unchanged reports. Preserve saved reviews,
  investigation notes, and matching records. Reviews do not retrain the model.
- Fix a reproduced WebSocket-disconnect cleanup race found during full-suite
  testing; shield asynchronous cleanup while preserving request cancellation.

Selected settings, stored in the application and included in the Windows build:

| Setting | Value |
| --- | ---: |
| Forest margin above calibration maximum | 0.08 |
| Minimum robust-deviation cutoff | 6.0 |
| Padding above calibration maximum robust deviation | 1.0 |

The guard uses transformed, median/MAD-scaled deviations; 6.0 is **not** a
six-standard-deviation Gaussian probability or a promised false-alarm rate.
Feature-scale floors are fixed design choices, not optimized on held-out data.

Fitting preprocessing on training data and keeping evaluation separate follows
[scikit-learn's data-leakage guidance](https://scikit-learn.org/stable/common_pitfalls.html).
The forest's raw unusualness is used with an explicitly calibrated cutoff, not
as a probability; see the
[Isolation Forest reference](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html).
Shielded finalization follows
[AnyIO's cancellation guidance](https://anyio.readthedocs.io/en/stable/cancellation.html).

## Evaluation protocol

All observations come from actual `ExchangeSession` matching commands in
isolated in-memory test engines. The evaluator neither reads nor seeds user
sessions. This is a developer measurement tool, not an application demo feature.

Six profiles cover varied small orders, repetitive small orders, constant
activity, high volume, fragmented fills, and balanced resting depth. Each stream
has 40 baseline observations, then 80 normal controls and eight injected
deviations. The deviations follow in a fixed order; earlier executions can
affect later price-change features.

Development uses seeds 100–107: 48 streams, 3,840 scored normal controls, and
384 deviations. A declared grid of 16 candidates combines forest margins
0.01/0.03/0.05/0.08 with guard floors 5/6/8/10; padding stays 1. The selector
maximizes development recall among candidates with at most 2% development false
alerts, breaking ties by fewer false alerts and more conservative cutoffs.
This budget is a selection rule, not a statistical guarantee.

Only after selection finishes does the evaluator generate held-out seeds
2000–2015: 96 streams, 7,680 scored normal controls, and 768 deviations. Their
labels are not used to choose settings. Constant and repetitive profiles are
deterministic across seeds; these stream counts are not independent statistical
replications. The evaluation was run twice; settings and confusion counts
reproduced exactly on this environment.

The comparison detector reproduces the prior method on the same held-out
streams: StandardScaler + 150-tree Isolation Forest, contamination 0.05,
trained on all 40 baseline observations, with its default decision cutoff.
This compares complete old/new pipelines, not one isolated parameter change.

## Measured results

| Held-out measurement | Prior detector | Calibrated hybrid |
| --- | ---: | ---: |
| Detected deviations (true positives) | 286 | **767** |
| Missed deviations (false negatives) | 482 | **1** |
| Normal controls incorrectly flagged (false positives) | 592 | **6** |
| Normal controls correctly unflagged (true negatives) | 7,088 | **7,674** |
| Precision | 32.57% | **99.22%** |
| Recall | 37.24% | **99.87%** |
| F1 | 34.75% | **99.55%** |
| False-positive rate | 7.7083% | **0.0781%** |

Precision = TP / (TP + FP); recall = TP / (TP + FN);
false-positive rate = FP / (FP + TN). Precision depends on this deliberately
chosen mix of normal controls and injected deviations, not real-world prevalence.
Development selection achieved 384/384 detections and four false alerts.

| Held-out profile | Detected / deviations | False alerts / normal controls |
| --- | ---: | ---: |
| Varied small orders | 128 / 128 | 4 / 1,280 |
| Repetitive small orders | 128 / 128 | 0 / 1,280 |
| Constant activity | 128 / 128 | 0 / 1,280 |
| High-volume activity | 127 / 128 | 1 / 1,280 |
| Fragmented fills | 128 / 128 | 0 / 1,280 |
| Balanced resting depth | 128 / 128 | 1 / 1,280 |

Quantity spikes, upward/downward price jumps, fragmentation bursts, depth
surges, large partially unfilled submissions, and combined spikes were each
detected 96/96 times. The scaled missed-case regression was detected 95/96 times.

Detector attribution matters: **763 deviations were flagged by guards alone,
four by both detectors, and none by the forest alone**. All six false alerts
came from the forest alone. Therefore the strong result on these extreme
deviations is primarily evidence for the explicit guards, not standalone
Isolation Forest performance or subtle abuse detection.

### Remaining miss and false alerts

The miss is `high_volume`, seed **2009**, observation **128**: 200,000 shares
at 130, after another injected execution at the same price. Its price-change
feature is therefore zero. The largest robust deviation is **5.9745**, below
the **6.0** cutoff; forest unusualness **0.5417** is below its **0.6468** cutoff.
Neither branch requests review. Settings were not retuned to erase this
held-out failure.

Four false alerts occurred in `varied_small` (seed 2012 observations 56, 57,
93; seed 2015 observation 102), one in `high_volume` (seed 2015 observation 83),
and one in `balanced_book` (seed 2002 observation 54). Full feature values,
thresholds, and outcomes for every error are in
[the archived raw measurement artifact](../benchmarks/ai-calibration-v2.json).

## Application verification

| Check | Recorded result |
| --- | --- |
| Complete Python suite | **124 passed**, 19.88 seconds; no failures/skips |
| Browser end-to-end suite | **5 passed**, 12.4 seconds; retries disabled |
| TypeScript + Vite production build | Passed |
| Python dependency consistency | `pip check`: no broken requirements |
| Frontend dependency audit | `npm audit`: zero known vulnerabilities reported |
| Native packaged Windows smoke | Exit **0**; UI rendered, 7 shares matched in 1 trade |
| Packaged calibrated model | 46 executed-order observations; large execution flagged by robust guard; correct model version and 24/16 split loaded |
| Advisory isolation | Exported matching records unchanged by AI report |
| Desktop shutdown | Smoke closes its own window and server |
| Portable ZIP integrity | CRC passed for all 2,655 entries; packaged EXE, frontend, shortcut, and calibration settings match the rebuilt files |

The rebuilt `dist/TradeVelocity-Windows-x64.zip` is 120,449,699 bytes. Its SHA-256
is `a8d08cb09971c150783b2296c4fd993c89e3f95076d72063b470daf825dc4dd7`.
No TradeVelocity process or test listeners on ports 8765/8804 remained afterward.
The executable/ZIP are local generated artifacts; no GitHub release or push
was performed.

Python tests cover the former miss, constant-baseline tolerance, extreme
deviations, stable earlier scores, model reuse, calibration/fit separation,
disjoint evaluation seeds, selected-setting consistency, and invalid parameters.
The full suite also checks persistence, rollback, retry idempotency, timestamps,
concurrent quantity conservation, session isolation, and market-data failures.
Browser tests exercise lifecycle/live updates, theme/chart controls, lost-response
retry safety, persistent review notes, and the original repetitive-baseline miss.

During the browser run, Windows logged one `WinError 10054` closed-connection
diagnostic; all five tests passed. This was not treated as a failed assertion
or suppressed. If it recurs during ordinary usage, investigate it separately.
Known-vulnerability audits do not establish overall application security.

Environment: Windows 11 x64, Python **3.14.7**, scikit-learn **1.9.1**,
Node/npm frontend tooling, Chromium browser tests, and native WebView2 desktop
smoke. The latest evaluator run took **25.782 seconds**. Package/library changes
can change numerical outputs; exact measurements are tied to this environment.
These are local results, not an assertion that GitHub CI or another OS was run.

## Reproduce

From the project root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[app,test,desktop]"
cd frontend
npm ci
npm run build
npx playwright install chromium
npm run test:e2e
cd ..
.\.venv\Scripts\python.exe -m pytest -q -ra
.\.venv\Scripts\python.exe scripts/calibrate_ai.py
.\.venv\Scripts\python.exe scripts/build_desktop.py
.\dist\TradeVelocity\TradeVelocity.exe --smoke-test
```

The v2 evaluator originally wrote `benchmarks/ai-calibration.json` (now archived
as `benchmarks/ai-calibration-v2.json`) with every candidate,
selected settings, protocol, aggregate/profile/deviation counts, detector
attribution, and error cases. It does not silently replace runtime settings;
the checked-in settings file matches the selected candidate. Desktop smoke
writes its receipt under `%LOCALAPPDATA%\TradeVelocity\smoke-test.json` and uses
separate smoke sessions/WebView storage, not the normal user workspace.

## Limits and next validation

The baseline is assumed representative and normal. A poisoned baseline,
ordinary changes of regime, sparse observations, or unmeasured behavior can
cause misses or false alerts. Only executed commands create observations; this
does not detect every suspicious unfilled/cancelled order or establish identities.
Depth covers the top 30 levels. No real-market labelled abuse dataset was used.

Historical daily-bar anomaly analysis remains separate and in-sample; this
calibration does not validate it. The app is still a local own-engine system,
not a broker connection or an authenticated public exchange.

Next validation should use a newly reserved, realistic dataset with interleaved
subtle deviations, normal regime shifts, contaminated baselines, and explicit
guard/forest ablation. Any tuning informed by this report requires a **new**
untouched evaluation set. Probability claims would require separate probability
calibration and labelled evidence. This release completes controlled hybrid
threshold calibration, not production fraud certification.
