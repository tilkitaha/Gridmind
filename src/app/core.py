def dispatch(payload: dict) -> dict:
    price = float(payload.get("price", 0.20))
    soc = float(payload.get("battery_soc", 0.50))
    pv = float(payload.get("pv_kw", 0))
    load = float(payload.get("load_kw", 0))
    if pv > load:
        action = "charge" if soc < 0.90 else "export"
    elif price > 0.30 and soc > 0.25:
        action = "discharge"
    else:
        action = "import"
    return {"action": action, "net_kw": round(pv - load, 3), "battery_soc": soc}


def baseline_forecast(payload: dict) -> dict:
    values = payload.get("history", [0])
    avg = sum(values) / len(values) if values else 0
    horizon = int(payload.get("horizon", 24))
    return {"forecast": [round(avg, 3)] * horizon, "method": "mean-baseline"}
