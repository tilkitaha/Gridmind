# Polish market study boundary and reproducible interface

22 September 2026. Intended application: a price-taking BESS trader in the PL bidding zone. No Polish empirical market performance has been computed.

## Implemented

`polish_market.py` supplies delivery-day indexing, strict CSV validation, a deterministic BESS MILP, physical checks and realized-price scoring. Nameplate energy is 2 MWh; the 10-90 percent range provides 1.6 MWh of usable swing. Power and grid exchange are 1 MW. Both efficiencies are 0.95 and start/end inventory is 1 MWh. A binary variable rules out simultaneous charging and discharging under negative prices. Throughput cost defaults to 10 EUR/MWh for each AC direction.

Local dates use Europe/Warsaw, while unique interval keys are UTC. Clock-change days contain 92 or 100 quarter-hours rather than 96. The model accepts only an exact complete 15-minute day, including its clock-change length. It does not silently turn hourly prices into four observations.

## Canonical CSV contract

Forecast CSV columns: `timestamp_utc,value_eur_mwh,issued_at`. Realized-price CSV columns: `timestamp_utc,value_eur_mwh`. Timestamps require explicit offsets, records must be strictly ordered and complete, and values must be finite EUR/MWh. Forecast issue time must be strictly before noon Europe/Warsaw on D-1. This checks metadata consistency, not its authenticity. Preserve original downloads, query parameters, units, publication revisions, source URL and retrieval time in a separate provenance manifest.

```bash
PYTHONPATH=src python scripts/evaluate_polish_day.py --day YYYY-MM-DD --forecast forecast.csv --realized realized.csv --output results/new_day.json
```

The command fixes the forecast-based schedule before reading realized prices. It refuses to overwrite an existing output. Inputs are required; no invented market data are bundled. Evaluated profit assumes full order acceptance, no imbalance settlement and no network/exchange charges. The default zero ledger monetary charge is an explicit assumption; local gas has not been converted to a market fee.

## Data and sources

ENTSO-E zone `10YPL-AREA-----S`, energy prices 12.1.D, is the proposed source. Candidate training: 2025-10-01 to 2026-05-31; validation: June 2026; candidate test: July-August 2026. No raw data, published-version audit or independent-test access audit has been completed. The proposed protocol is therefore not data-frozen. API access requires registration and a security token; do not put tokens in source files or the archive.

- [ENTSO-E market design](https://www.entsoe.eu/network_codes/cacm/implementation/sdac/)
- [PSE 15-minute launch announcement](https://www.pse.pl/-/pomyslne-uruchomienie-projektu-15-mtu-na-rynku-dnia-nastepnego)
- [ENTSO-E API access](https://transparencyplatform.zendesk.com/hc/en-us/articles/12845911031188-How-to-get-security-token)
- [SciPy MILP documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html)

## Remaining research

LEAR/boosting/Transformer forecasts, forecast-conditioned Polish PPO, risk-constrained optimization, partial order acceptance, imbalance charges and ten-owner physical disaggregation are unimplemented. Synthetic analytical tests of the scheduling module are not backtests. A future daily policy must not consume realized intraday prices when scoring a schedule that was supposedly fixed on D-1.

The original Irish data evaluate a different community and tariff model. Do not join their unverified source clock to Polish prices or rescale their savings to the 1 MW system.
