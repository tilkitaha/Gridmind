"""Exploratory forecast-to-MPC intervention on the existing StoreNet episodes.

No new independent test data are introduced. Forecasts use strictly past meter
values; the oracle arm is explicitly non-causal. Units: kWh per 15 min, EUR.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from .battery import BatteryBatch, load_episodes, mpc_action


def load_net(path="data/storenet_h1_h6_15min.csv"):
    raw = pd.read_csv(path, index_col=0, parse_dates=True)
    return pd.DataFrame(raw.iloc[:, ::2].to_numpy() - raw.iloc[:, 1::2].to_numpy(), index=raw.index)


def clock(t):
    h = t.hour + t.minute / 60
    return [np.sin(h * np.pi / 12), np.cos(h * np.pi / 12)]


def fit_model(history):
    training = history.loc[:"2020-04-30 23:45"]
    X, Y = [], []
    for t, y in training.iterrows():
        previous = training.reindex([t - pd.Timedelta(minutes=15), t - pd.Timedelta(days=1)])
        if np.isfinite(previous.to_numpy()).all() and np.isfinite(y.to_numpy()).all():
            X.append(np.r_[previous.iloc[0], previous.iloc[1], clock(t)])
            Y.append(y.to_numpy())
    model = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
    model.fit(np.asarray(X), np.asarray(Y))
    return model, len(X)


def predict(history, current, horizon, method, model=None):
    # Cut off observed values once, before generating the complete horizon.
    known = history.loc[history.index < current]
    last = known.reindex([current - pd.Timedelta(minutes=15)]).to_numpy()[0]
    if not np.isfinite(last).all():
        raise ValueError("Missing previous interval")
    out, fallbacks = [], 0
    previous = last.copy()
    for t in pd.date_range(current, periods=horizon, freq="15min"):
        daily = known.reindex([t - pd.Timedelta(days=1)]).to_numpy()[0]
        if not np.isfinite(daily).all():
            daily = last.copy()
            fallbacks += 1
        if method == "persistence":
            y = last.copy()
        elif method == "daily":
            y = daily.copy()
        elif method == "ridge":
            y = model.predict(np.r_[previous, daily, clock(t)][None])[0]
        else:
            raise ValueError(method)
        out.append(y)
        previous = y
    return np.asarray(out), fallbacks


def run():
    outdir = Path("results/forecast_control")
    outdir.mkdir(parents=True, exist_ok=True)
    protocol_path = Path("configs/forecast_control_protocol.json")
    protocol = json.loads(protocol_path.read_text())
    history = load_net()
    model, training_rows = fit_model(history)
    np.savez(outdir / "ridge_coefficients.npz", mean=model[0].mean_, scale=model[0].scale_, coef=model[1].coef_, intercept=model[1].intercept_)
    rows, summaries = [], []
    episodes = load_episodes("test")
    for method in protocol["methods"]:
        total_cost = total_gain = throughput = error1 = errorh = residual = terminal = 0.0
        count1 = counth = fallback_count = 0
        for episode in episodes:
            env = BatteryBatch([episode])
            cost = np.zeros(6)
            gain = np.zeros(6)
            for step in range(16):
                current = pd.Timestamp(episode["start"]) + pd.Timedelta(minutes=15 * step)
                H = 16 - step
                if method == "oracle":
                    forecast = episode["net"][step:].copy()
                else:
                    forecast, missing = predict(history, current, H, method, model)
                    fallback_count += missing if method != "persistence" else 0
                error = np.abs(forecast - episode["net"][step:])
                error1 += error[0].sum()
                count1 += 6
                errorh += error.sum()
                counth += error.size
                action = mpc_action(env, forecast)
                _, _, _, d = env.step(action)
                cost += d["cost"][0]
                gain += d["benefit"][0]
                throughput += np.abs(d["ac"]).sum()
                residual = max(residual, float(np.abs(d["residual"]).max()))
            terminal = max(terminal, float(np.abs(env.soc - 1).max()))
            for i in range(6):
                rows.append(dict(method=method, start=episode["start"], household=f"H{i+1}", cost_eur=float(cost[i]), saving_eur=float(gain[i])))
            total_cost += cost.sum()
            total_gain += gain.sum()
        summaries.append(dict(method=method, cost_eur=float(total_cost), saving_eur=float(total_gain), throughput_kwh=float(throughput), first_step_mae_kwh=float(error1/count1), horizon_mae_kwh=float(errorh/counth), first_step_values=count1, horizon_values=counth, daily_fallback_forecast_slots=fallback_count, energy_residual=residual, terminal_residual=terminal))
        print(method, summaries[-1], flush=True)
    pd.DataFrame(rows).to_csv(outdir / "household_results.csv", index=False)
    pd.DataFrame(summaries).to_csv(outdir / "summary.csv", index=False)
    result = dict(status="exploratory_reused_June", protocol_sha256=hashlib.sha256(protocol_path.read_bytes()).hexdigest(), data_sha256=hashlib.sha256(Path("data/storenet_h1_h6_15min.csv").read_bytes()).hexdigest(), training_rows=training_rows, episodes=len(episodes), summaries=summaries)
    (outdir / "results.json").write_text(json.dumps(result, indent=2))


if __name__ == "__main__":
    run()
