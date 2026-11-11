# TradeVelocity — Test Suite Report

> **Run Date:** 2026-11-01 · **Environment:** Windows, Python 3.14.7, pytest 9.1.1, pluggy 1.6.0
> **Project Root:** `c:\Users\shivu\OneDrive\Documents\GitHub\ADSA PROJECT`

---

## 🟢 Overall Verdict: HEALTHY

All tests passed. All import and startup checks succeeded. The project is in excellent condition.

---

## Summary Table

| Metric | Count |
|---|---|
| **Total Tests Collected** | 160 |
| ✅ Passed | **160** |
| ❌ Failed | 0 |
| 💥 Errors | 0 |
| ⏭️ Skipped | 0 |
| **Duration** | 38.24 s |

---

## Per-Test-File Breakdown

| Test File | Tests | Passed | Failed | Errors | Skipped |
|---|---|---|---|---|---|
| `test_anomaly.py` | 3 | 3 | 0 | 0 | 0 |
| `test_calibration.py` | 11 | 11 | 0 | 0 | 0 |
| `test_compare_cli.py` | 6 | 6 | 0 | 0 | 0 |
| `test_desktop.py` | 2 | 2 | 0 | 0 | 0 |
| `test_engine.py` | 10 | 10 | 0 | 0 | 0 |
| `test_execution_monitor.py` | 11 | 11 | 0 | 0 | 0 |
| `test_experiments.py` | 16 | 16 | 0 | 0 | 0 |
| `test_launcher.py` | 6 | 6 | 0 | 0 | 0 |
| `test_market_data.py` | 5 | 5 | 0 | 0 | 0 |
| `test_order_lifecycle.py` | 3 | 3 | 0 | 0 | 0 |
| `test_portfolio.py` | 9 | 9 | 0 | 0 | 0 |
| `test_release_tools.py` | 6 | 6 | 0 | 0 | 0 |
| `test_security.py` | 18 | 18 | 0 | 0 | 0 |
| `test_session.py` | 8 | 8 | 0 | 0 | 0 |
| `test_storage.py` | 1 | 1 | 0 | 0 | 0 |
| `test_structures.py` | 7 | 7 | 0 | 0 | 0 |
| `test_windows_checks.py` | 3 | 3 | 0 | 0 | 0 |
| `test_workspace_api.py` | 35 | 35 | 0 | 0 | 0 |
| **TOTAL** | **160** | **160** | **0** | **0** | **0** |

---

## Detailed Test Results by Module

### `test_anomaly.py` (3/3 ✅)
- `test_feature_engineering_returns_required_numeric_features`
- `test_isolation_forest_report_is_serializable_and_bounded`
- `test_unknown_anomaly_symbol_is_rejected`

### `test_calibration.py` (11/11 ✅)
- `test_calibration_and_heldout_seeds_are_disjoint`
- `test_controlled_heldout_profile_catches_injected_deviations` × 6 params (varied_small, repeated_small, constant_small, high_volume, fragmented, balanced_book)
- `test_recorded_evaluation_matches_runtime_settings_and_declares_limits`
- `test_former_false_alerts_do_not_regress` × 3 params (varied_small-2012, varied_small-2015, high_volume-2015, balanced_book-2002)

### `test_compare_cli.py` (6/6 ✅)
- `test_comparison_cli_writes_reproducible_results_with_memory`
- `test_invalid_cli_arguments_do_not_write_results` × 5 params (args0–args4)

### `test_desktop.py` (2/2 ✅)
- `test_desktop_smoke_runs_real_api_and_releases_owned_port`
- `test_desktop_frontend_failure_still_shuts_down`

### `test_engine.py` (10/10 ✅)
- `test_example_matches_at_resting_price_and_partially_fills`
- `test_price_time_priority_and_market_remainder`
- `test_cancel_modify_and_multiple_symbols`
- `test_statistics_volume_ranges_and_trade_lookup`
- `test_invalid_input_does_not_consume_id_or_modify_existing_order`
- `test_avl_tree_deletions_and_ordering`
- `test_fenwick_growth_and_ranges`
- `test_no_cross_when_limit_prices_do_not_overlap`
- `test_randomized_matching_agrees_with_simple_reference_book`
- `test_concurrent_submissions_conserve_shares`

### `test_execution_monitor.py` (11/11 ✅)
- `test_warmup_only_counts_executions`
- `test_later_activity_does_not_change_baseline_or_old_scores`
- `test_previously_missed_repeated_baseline_is_detected_by_explicit_guard`
- `test_constant_baseline_has_no_tiny_change_alarm_but_detects_extremes`
- `test_cutoff_observations_are_not_used_to_fit_forest_or_robust_statistics`
- `test_unchanged_reports_reuse_model_and_return_independent_copies`
- `test_invalid_calibration_parameters_are_rejected` × 5 params
- `test_high_volume_previous_miss_is_caught_by_raw_envelope`

### `test_experiments.py` (16/16 ✅)
- `test_comparison_workloads_are_deterministic_and_engines_agree` × 9 params (2-1-mixed, 2-1-deep, 2-1-cancel, 33-5-mixed, 33-5-deep, 33-5-cancel, 300-1-mixed, 300-1-deep, 300-1-cancel)
- `test_comparison_book_retains_fifo_and_resting_execution_prices` × 2 engines (MatchingEngine, LinearMatchingEngine)
- `test_comparison_records_each_engine_repeat_and_correct_outcome`
- `test_timing_and_tracing_restore_state_after_failed_command`
- `test_workload_rejects_invalid_parameters` × 4 params
- `test_unknown_command_is_rejected`

### `test_launcher.py` (6/6 ✅)
- `test_other_healthy_service_is_not_reused_or_stopped`
- `test_existing_app_opens_selected_browser_without_rebuilding`
- `test_missing_browser_falls_back_to_system_default`
- `test_windows_shortcut_reports_missing_environment`
- `test_windows_shortcut_uses_its_folder_and_forwards_launch_options`
- `test_stopping_launcher_releases_server_port`

### `test_market_data.py` (5/5 ✅)
- `test_snapshot_preserves_prices_and_provenance_without_network`
- `test_missing_or_broken_snapshot_has_no_fabricated_prices`
- `test_cleaning_removes_invalid_bars_and_sorts_unique_days`
- `test_flat_rsi_drawdown_and_adjusted_growth`
- `test_history_filter_is_relative_to_data_date`

### `test_order_lifecycle.py` (3/3 ✅)
- `test_cancellation_churn_compacts_heap_and_price_recreation_is_safe` × 2 params (BUY-SELL-110.00, SELL-BUY-90.00)
- `test_mixed_order_lifecycle_matches_independent_reference`

### `test_portfolio.py` (9/9 ✅)
- `test_buy_sell_realized_unrealized_and_cash_conservation`
- `test_multiple_purchase_costs_and_average_cost_sale`
- `test_partial_market_fill_expires_and_only_filled_shares_are_booked`
- `test_rejections_keep_balances_positions_and_journal_unchanged`
- `test_paper_account_replays_after_restart`
- `test_invalid_cash_amounts_are_rejected` × 6 params (0, -1, NaN, Infinity, 0.001, no)

### `test_release_tools.py` (6/6 ✅)
- `test_signing_dry_plan_uses_store_identity_and_verifies`
- `test_signing_rejects_unsafe_targets_and_inputs` × 3 params
- `test_portable_package_checks_integrity_and_stale_inputs`
- `test_windows_icon_contains_crisp_common_sizes`

### `test_security.py` (18/18 ✅)
- `test_local_host_and_origin_protection` × 2 params
- `test_unsafe_configuration_fails_closed` × 6 params
- `test_private_sign_in_cookie_logout_and_bearer`
- `test_private_cross_origin_and_host_requests_are_rejected`
- `test_login_rate_limit_and_expiration`
- `test_body_limit_before_session_mutation`
- `test_malformed_host_is_rejected_without_server_error` × 4 params
- `test_local_mode_denies_non_loopback_clients`
- `test_rate_window_recovers_and_expensive_operations_are_limited`
- `test_private_websocket_requires_auth_and_checks_origin`
- `test_websocket_cookie_revocation_before_next_update`

### `test_session.py` (8/8 ✅)
- `test_export_and_replay_preserve_book_and_trades`
- `test_invalid_scenario_gives_event_number`
- `test_bundled_order_lifecycle_fixture`
- `test_recorded_execution_times_are_preserved_including_amendment`
- `test_legacy_execution_time_is_unknown_not_replay_time`
- `test_invalid_saved_timestamps_are_rejected` × 3 params (invalid, 2026-09-30T12:00:00, 123)

### `test_storage.py` (1/1 ✅)
- `test_database_failure_rolls_back_commands_metadata_and_receipt`

### `test_structures.py` (7/7 ✅)
- `test_hash_table_collision_chains_survive_resize_update_and_removal`
- `test_hash_table_randomized_operations_agree_with_dictionary`
- `test_bulk_heap_and_incremental_pushes_obey_priority` × 2 params (False, True)
- `test_queue_unlinks_middle_head_tail_and_reuses_empty_queue`
- `test_avl_balances_and_heights_hold_after_every_mutation`
- `test_fenwick_prefixes_remain_correct_at_capacity_boundaries`

### `test_windows_checks.py` (3/3 ✅)
- `test_server_uses_selector_transport_and_bounded_connections`
- `test_missing_runtime_is_reported_without_installing`
- `test_installed_windows_prerequisites`

### `test_workspace_api.py` (35/35 ✅)
- `test_new_sessions_are_empty_without_generated_liquidity`
- `test_removed_presets_cannot_replace_a_session` × 5 params
- `test_order_lifecycle_and_replay_are_real_engine_outcomes`
- `test_persistence_and_legacy_account_preservation`
- `test_trade_timestamps_survive_restart_and_export`
- `test_failed_save_rolls_back_every_mutation` × 5 params (place, modify, cancel, reset, import)
- `test_idempotency_survives_restart_and_rejects_different_inputs`
- `test_live_updates_follow_commits_and_are_session_isolated`
- `test_repeated_live_disconnects_release_listeners`
- `test_sparse_history_is_json_safe_without_fabricated_returns`
- `test_concurrent_orders_cannot_overfill_counterparty`
- `test_full_history_pagination_search_and_export`
- `test_watchdog_supports_user_symbols_without_preset_activity`
- `test_input_and_session_validation`
- `test_real_history_and_computed_metrics`
- `test_missing_data_does_not_prevent_order_entry`
- `test_failed_refresh_preserves_orders_and_snapshot`
- `test_successful_refresh_persists_outside_the_packaged_app`
- `test_benchmarks_do_not_change_the_active_session`

---

## Failure / Error Analysis

> [!NOTE]
> **No failures or errors were recorded.** This section is intentionally empty — all 160 tests passed cleanly with exit code 0.

---

## Import & Startup Checks

| Check | Command | Result |
|---|---|---|
| `app.py` top-level import | `python -c "import app"` | ✅ **OK** |
| `stock_engine` src import | `python -c "import sys; sys.path.insert(0,'src'); import stock_engine"` | ✅ **OK** |
| FastAPI application import | `python -c "from stock_engine.api import app as api_app"` | ✅ **OK** |

All three startup probes exited with code **0** and printed their expected confirmation messages. The server-side FastAPI application loads without errors.

---

## Recommendations

Since every test passes and all startup checks succeed, no corrective action is required. The following are general good-practice suggestions for the future:

1. **Coverage gate** — Consider adding `pytest-cov` and enforcing a minimum coverage threshold in CI to catch regressions in untested code paths.
2. **Type checking** — Integrate `mypy` or `pyright` into the CI pipeline for static type safety.
3. **Performance benchmarks** — The suite finishes in ~38 s across 160 tests. Monitor for slowdowns as new tests are added; consider marking heavy integration tests with a custom marker so a fast smoke suite can run on every commit.
4. **Dependency pinning** — Confirm `pyproject.toml` / `requirements.txt` pins are locked (e.g., via `pip-compile`) to avoid surprise upgrades breaking the environment.

---

*Generated automatically by the TradeVelocity test-runner agent on 2026-11-01.*
