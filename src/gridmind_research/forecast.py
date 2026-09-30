"""Causal one-step net-energy forecast experiment; separate from ex-post clearing."""

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def build_features(frame):
    load = frame.filter(like="_load_kwh").sum(axis=1, min_count=6)
    pv = frame.filter(like="_pv_kwh").sum(axis=1, min_count=6)
    net = load - pv
    X = pd.DataFrame({f"lag_{lag}": net.shift(lag) for lag in [1, 4, 96, 672]})
    slot = frame.index.hour * 4 + frame.index.minute / 15
    X["sin_day"], X["cos_day"] = np.sin(slot * 2 * np.pi / 96), np.cos(slot * 2 * np.pi / 96)
    X["sin_week"] = np.sin(frame.index.dayofweek * 2 * np.pi / 7)
    X["cos_week"] = np.cos(frame.index.dayofweek * 2 * np.pi / 7)
    return X, net


def benchmark(frame):
    X, net = build_features(frame)
    valid = X.notna().all(axis=1) & net.notna()
    train = valid & (frame.index < "2020-05-01")
    val = valid & (frame.index >= "2020-05-01") & (frame.index < "2020-06-01")
    test = valid & (frame.index >= "2020-06-01") & (frame.index < "2020-06-15")
    if min(train.sum(), val.sum(), test.sum()) < 100:
        raise ValueError("Insufficient complete forecasting records")
    models = []
    for alpha in [0.1, 1.0, 10.0, 100.0]:
        model = make_pipeline(StandardScaler(), Ridge(alpha=alpha))
        model.fit(X.loc[train], net.loc[train])
        loss = float(np.abs(model.predict(X.loc[val]) - net.loc[val]).mean())
        models.append((loss, alpha, model))
    _, alpha, model = min(models, key=lambda x: x[0])
    # Refit chosen configuration on train+validation, before June test labels.
    model.fit(X.loc[train | val], net.loc[train | val])
    actual = net.loc[test]
    predictions = {
        "persistence": X.loc[test, "lag_1"].to_numpy(),
        "previous_day": X.loc[test, "lag_96"].to_numpy(),
        "ridge": model.predict(X.loc[test]),
    }
    out = pd.DataFrame({"actual_net_kwh": actual})
    result = {
        "task": "one-step 15-minute aggregate net-energy forecast",
        "not_day_ahead": True,
        "not_used_by_clearing": True,
        "train_end": "2020-04-30",
        "validation_month": "2020-05",
        "test_start": "2020-06-01",
        "test_end": "2020-06-14",
        "selected_alpha": alpha,
        "train_n": int(train.sum()),
        "validation_n": int(val.sum()),
        "test_n": int(test.sum()),
        "methods": {},
    }
    for name, pred in predictions.items():
        errors = pred - actual.to_numpy()
        result["methods"][name] = {
            "mae_kwh": float(np.abs(errors).mean()),
            "rmse_kwh": float(np.sqrt(np.mean(errors**2))),
        }
        out[name] = pred
    return result, out
