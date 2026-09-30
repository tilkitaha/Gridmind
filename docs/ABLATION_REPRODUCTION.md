# Follow-up experiment reproduction

22 September 2026. All measured results reuse June 1-14 and remain exploratory.

## Saved evidence audit

```bash
export PYTHONPATH=src
python scripts/verify_follow_up.py
python -m unittest discover -s research_tests -v
```

The audit checks sixty distinct runs, every checkpoint hash, data/protocol identity, replay cost parity, original-reference parity, 15,840 household records and 1,056 records from forecast substitution. It does not rerun training or claim an independent test.

## Replay and training

```bash
python -m gridmind_research.ablations --evaluate-only
python -m gridmind_research.ablations
python -m gridmind_research.forecast_control
```

Preserve an unchanged copy before training or forecast reruns. Evaluation-only writes `replay.json` and `household_replay.csv`; it does not replace training results. The original ten models remain under `results/extension/models`. The additional sixty remain under `results/ablations/models`.

The two action parameterizations differ in distribution, deterministic evaluation rule and entropy scale as well as support. The 300-update condition also provides more validation checkpoint opportunities. These limits are part of the intervention, not hidden away in interpretation.

The fairness branches add own cumulative signed saving and community mean to both arms. The penalty is a fixed change in negative population variance, normalized by 1 EUR. Gamma is one and the terminal potential is retained, so the objective changes. This is not policy-invariant shaping. Checkpoint selection remains economic in both arms.

## Observed conclusions

- All ten discrete 300-update policies reproduce idle cost 159.408258 EUR with zero executed throughput.
- Continuous 300-update mean costs are 166.142207 EUR for IPPO and 170.810777 EUR for MAPPO.
- The fixed fairness penalty does not consistently improve cost or dispersion.
- The sixty saved-policy replays match logged costs with maximum difference 0.0 EUR. The discrete-60 reference matches the original ten results within 2.85e-14 EUR.
- Persistence, previous-day, Ridge and oracle MPC cost 159.160427, 160.305059, 158.861848 and 153.761379 EUR respectively.
- Ridge MPC has slightly worse first-step MAE but better horizon MAE and lower total cost than persistence. H1 and H5 still lose relative to idle.

`results/forecast_control/ridge_coefficients.npz` retains the fitted transformation and coefficients. The original aggregate Ridge in Chapter 5 is a different model and target. The new predictor feeds MPC; it does not feed the existing learned actors.
