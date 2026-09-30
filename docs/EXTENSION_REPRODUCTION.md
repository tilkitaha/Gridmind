> This document describes the original experiment. The later July–December study is documented in LATER_PERIOD_REPRODUCTION.md. For the 22 September 2026 follow-up results and current scope, read ABLATION_REPRODUCTION.md and POLISH_MARKET_STUDY.md.

# Completed battery learning and local ledger experiments

Version 0.3 implements the three previously proposed components. This is a research simulation with measured household load/PV, assumed batteries and tariffs, trained policies, and a Solidity contract actually executed on a local EVM. No real money is used.

## Run

Use Python 3.12 from the project root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install torch==2.14.0 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements-extension.txt
export PYTHONPATH=src
python -m unittest discover -s research_tests -v
python -m gridmind_research.learned_control --evaluate-only
python scripts/summarize_extension.py
python -m gridmind_research.ledger_experiment
```

The ten trained models are included; evaluation-only skips training and preserves `control_results.json`, writing `evaluation_results.json` instead. To retrain all ten models, omit `--evaluate-only`. This replaces checkpoints and training outputs. Keep a copy of the delivered results if comparing reruns. Windows PowerShell uses `$env:PYTHONPATH = "src"` instead of `export`.

The compiled Solidity ABI/bytecode and exact compiler input are included. Optional source recompilation:

```bash
npm install --no-save solc@0.8.30
node contracts/compile.cjs
```

## Protocol

`configs/extension_protocol.json` records the scenario. Six batteries: 2 kWh nominal, 0.2–1.8 kWh state bounds, 2 kW AC power, 95% efficiencies, 0.01 EUR/kWh AC-throughput cost. Each complete four-hour episode starts and ends at 1 kWh per battery. A reachability guard enforces terminal equality; restoration is paid through grid exchanges. Missing intervals are not imputed or skipped while carrying state. Prior observed net load is the causal persistence forecast; the current target is hidden.

There are 404 January–April training episodes, 105 May validation episodes and 44 June 1–14 test episodes. The 704 test intervals are 52.38% of the possible two-week period. Test dates were already inspected in the first allocation pilot: this is exploratory chronological evaluation, not a new untouched confirmatory sample. A raw-data expansion failed integrity/access checks; the previously delivered processed subset was retained. No later-period data or results are invented.

IPPO and MAPPO use the same local parameter-sharing actor, action requests and shared economic reward. Only MAPPO has centralized critic observations during training. Each method has five seeds (11,22,33,44,55), 60 updates, 12 episodes/update and four PPO epochs. Validation checkpoint selection occurs every ten updates. No test tuning was performed. The common actor has two 32-unit tanh layers. Projection can alias multiple requests to the same action. This is a short fixed training budget, not a convergence claim.

MPC has continuous actions and community observations. Its remaining-horizon LP uses only persistence forecasts and the known tariff schedule. Under the assumed positive prices and degradation cost, simultaneous cycling is unprofitable; every solution is checked. MPC-versus-RL compares complete controllers; IPPO-versus-MAPPO matches local actor information and actions.

## Measured result

Total cost over identical test episodes, including degradation:

| Controller | Mean EUR | Seed SD EUR |
|---|---:|---:|
| Idle sharing |159.4083|—|
| Self-consumption |171.1107|—|
| Causal MPC |159.1604|—|
| IPPO, five seeds |173.3106|19.5128|
| MAPPO, five seeds |182.8197|22.4156|

The trained policies did not beat MPC. Two IPPO seeds match idle by taking no battery action. Losses remain in the household CSV. Jain is undefined when its nonnegative-benefit interpretation fails, and idle's all-zero incremental benefit is not perfect fairness. Episode CVaR is diagnostic, not enforcement of a daily risk budget. The original fairness-shaped learning hypothesis remains unconfirmed.

## Ledger

`EnergySettlement.sol` runs on eth-tester/PyEVM. The first 64 positive trades from fixed MAPPO seed 11 are replayed against an Ed25519-signed SQLite ledger. Both end with exactly equal balances and conserve all six billion accounting credit units. The transaction stream expresses micro-kWh and micro-EUR; it does not move real currency. The operator remains trusted for metering and allocation. Database signatures require a separately trusted public key. A local EVM does not test distributed consensus or public-chain finality. Gas is measured; fiat gas fees are not assumed. Local one-pass latency is not a production throughput benchmark.

`results/extension/test_log.txt` records 24 research tests. `ledger_results.json` records ten additional successful checks, including replay, authorization, overspend rollback and signature tampering. Model files, source, data, results, receipts, ABI and bytecode are included. Run timings, signatures and transaction hashes can vary; numerical controller totals and integer balances should reproduce at stated precision.

Primary references: [MAPPO paper](https://arxiv.org/abs/2103.01955), [PyTorch](https://docs.pytorch.org/docs/2.14/distributions.html), [Ethereum testing](https://ethereum.org/developers/docs/smart-contracts/testing/), [Solidity 0.8.30](https://docs.soliditylang.org/en/v0.8.30/).

## Additional descriptive audit and retained-signature verification

From the package root, after installing extension dependencies:

```bash
python scripts/analyze_defense_results.py
python scripts/verify_saved_ledger.py
```

The first command writes `results/extension/defense_analysis.json` from retained CSV records. It includes start-hour coverage, positive MPC episodes, household losses, seed variation and fixed-dispatch fee sensitivity. It does not reoptimize or retrain. The second opens the delivered database read-only, verifies all signatures using the supplied public key, matches the stream and reconstructs balances. Independent key authentication is still required for signer identity.
