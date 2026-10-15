"""ENTSO-E Transparency data for the Polish study.

Day-ahead prices (12.1.D, A44) are parsed into the realized-price contract of
polish_market.validate_day: timestamp_utc,value_eur_mwh; hourly price periods are
never split into quarter-hours. Load (6.1.A/B, A65) and generation per type
(16.1.B&C, A75) are parsed as MW levels. The security token is read from the
environment by the caller and must never be written to disk or logs. The price
parser was checked against live responses for October 2025 to June 2026.
"""
import xml.etree.ElementTree as ET

import pandas as pd

API = 'https://web-api.tp.entsoe.eu/api'
PL = '10YPL-AREA-----S'
# Harmonised SDAC clearing-price limits; the floor is -600 EUR/MWh from the 28 May 2026 trading date.
PRICE_LIMITS_EUR_MWH = (-600.0, 4000.0)
RESOLUTION = {'PT15M': pd.Timedelta(minutes=15), 'PT30M': pd.Timedelta(minutes=30), 'PT60M': pd.Timedelta(hours=1)}


def query(start_utc, end_utc, zone=PL):
    """Request parameters without the token, for provenance records."""
    fmt = '%Y%m%d%H%M'
    start, end = pd.Timestamp(start_utc), pd.Timestamp(end_utc)
    if start.tzinfo is None or end.tzinfo is None:
        raise ValueError('Query bounds require explicit UTC offsets')
    return {'documentType': 'A44', 'in_Domain': zone, 'out_Domain': zone,
            'periodStart': start.tz_convert('UTC').strftime(fmt), 'periodEnd': end.tz_convert('UTC').strftime(fmt)}


def _local(tag):
    return tag.rsplit('}', 1)[-1]


def _find(node, name):
    for child in node:
        if _local(child.tag) == name:
            return child
    return None


def _all(node, name):
    return [c for c in node.iter() if _local(c.tag) == name]


def parse_prices(xml_bytes):
    """Return (frame, resolutions, currency); raise on acknowledgements, mixed units or conflicts.

    EUR prices come as value_eur_mwh, the realized-price contract. Any other currency is kept
    as value_<currency>_mwh, never converted here: a conversion needs a recorded FX source.
    """
    root = ET.fromstring(xml_bytes)
    if _local(root.tag) == 'Acknowledgement_MarketDocument':
        text = ' '.join(t.text or '' for t in _all(root, 'text'))
        raise LookupError(f'ENTSO-E acknowledgement: {text.strip()}')
    if _local(root.tag) != 'Publication_MarketDocument':
        raise ValueError(f'Unexpected document {_local(root.tag)}')
    values, resolutions, currencies = {}, set(), set()
    for series in _all(root, 'TimeSeries'):
        currency = _find(series, 'currency_Unit.name')
        unit = _find(series, 'price_Measure_Unit.name')
        if currency is None or not currency.text or unit is None or unit.text != 'MWH':
            raise ValueError('Expected a currency per MWh')
        currencies.add(currency.text)
        if len(currencies) > 1:
            raise ValueError(f'Mixed currencies {sorted(currencies)}')
        curve = _find(series, 'curveType')
        curve = curve.text if curve is not None else 'A01'
        if curve not in ('A01', 'A03'):
            raise ValueError(f'Unsupported curve type {curve}')
        for period in _all(series, 'Period'):
            interval = _find(period, 'timeInterval')
            start = pd.Timestamp(_find(interval, 'start').text).tz_convert('UTC')
            end = pd.Timestamp(_find(interval, 'end').text).tz_convert('UTC')
            res = _find(period, 'resolution').text
            if res not in RESOLUTION:
                raise ValueError(f'Unsupported resolution {res}')
            step = RESOLUTION[res]
            resolutions.add(res)
            n = int((end - start) / step)
            if start + n * step != end:
                raise ValueError('Period is not a whole number of steps')
            points = {}
            for p in _all(period, 'Point'):
                pos = int(_find(p, 'position').text)
                if not 1 <= pos <= n or pos in points:
                    raise ValueError(f'Bad or duplicate position {pos}')
                points[pos] = float(_find(p, 'price.amount').text)
            if 1 not in points:
                raise ValueError('Period lacks its first point')
            current = None
            for pos in range(1, n + 1):
                if pos in points:
                    current = points[pos]
                elif curve == 'A01':
                    raise ValueError(f'Missing position {pos} in an A01 curve')
                # A03 omits a point when the price repeats the previous one.
                t = start + (pos - 1) * step
                if t in values and values[t] != current:
                    raise ValueError(f'Conflicting prices at {t}')
                values[t] = current
    if not values:
        raise LookupError('No price points in response')
    (currency,) = currencies
    prices = [values[t] for t in sorted(values)]
    if currency == 'EUR':
        low, high = PRICE_LIMITS_EUR_MWH
        if min(prices) < low or max(prices) > high:
            raise ValueError('Price outside the harmonised SDAC limits')
    frame = pd.DataFrame({'timestamp_utc': [t.isoformat() for t in sorted(values)],
                          f'value_{currency.lower()}_mwh': prices})
    return frame, sorted(resolutions), currency


def split_days(frame, zone='Europe/Warsaw'):
    """Group a parsed frame by local delivery date."""
    local = pd.to_datetime(frame.timestamp_utc, utc=True).dt.tz_convert(zone).dt.date
    return {str(day): part.reset_index(drop=True) for day, part in frame.groupby(local)}


# Feature series; all are MW levels. Only the day-ahead load forecast is published before
# the D-1 12:00 gate for day D; actual load and generation are used with a two-day lag.
FEATURES = {
    'load_forecast': {'documentType': 'A65', 'processType': 'A01', 'domain': 'outBiddingZone_Domain'},
    'load_actual': {'documentType': 'A65', 'processType': 'A16', 'domain': 'outBiddingZone_Domain'},
    'generation': {'documentType': 'A75', 'processType': 'A16', 'domain': 'in_Domain'},
}


def feature_query(kind, start_utc, end_utc, zone=PL):
    """Request parameters for a feature series, without the token."""
    spec = FEATURES[kind]
    q = query(start_utc, end_utc, zone)
    return {'documentType': spec['documentType'], 'processType': spec['processType'], spec['domain']: zone,
            'periodStart': q['periodStart'], 'periodEnd': q['periodEnd']}


def parse_quantities(xml_bytes):
    """Return a frame timestamp_utc, key, value_mw, resolution from an A65 or A75 document.

    key is the production type (B16 solar, B19 wind onshore, ...) or 'total' for load.
    Generation series that belong to consumption (outBiddingZone only, e.g. pumping) are dropped.
    """
    root = ET.fromstring(xml_bytes)
    if _local(root.tag) == 'Acknowledgement_MarketDocument':
        text = ' '.join(t.text or '' for t in _all(root, 'text'))
        raise LookupError(f'ENTSO-E acknowledgement: {text.strip()}')
    if _local(root.tag) != 'GL_MarketDocument':
        raise ValueError(f'Unexpected document {_local(root.tag)}')
    values = {}
    for series in _all(root, 'TimeSeries'):
        unit = _find(series, 'quantity_Measure_Unit.name')
        if unit is None or unit.text != 'MAW':
            raise ValueError('Expected MW (MAW)')
        psr = next((x.text for x in _all(series, 'psrType')), None)
        if psr is not None and _find(series, 'inBiddingZone_Domain.mRID') is None:
            continue
        key = psr or 'total'
        curve = _find(series, 'curveType')
        curve = curve.text if curve is not None else 'A01'
        if curve not in ('A01', 'A03'):
            raise ValueError(f'Unsupported curve type {curve}')
        for period in _all(series, 'Period'):
            interval = _find(period, 'timeInterval')
            start = pd.Timestamp(_find(interval, 'start').text).tz_convert('UTC')
            end = pd.Timestamp(_find(interval, 'end').text).tz_convert('UTC')
            res = _find(period, 'resolution').text
            if res not in RESOLUTION:
                raise ValueError(f'Unsupported resolution {res}')
            step = RESOLUTION[res]
            n = int((end - start) / step)
            points = {int(_find(p, 'position').text): float(_find(p, 'quantity').text) for p in _all(period, 'Point')}
            if 1 not in points or max(points) > n:
                raise ValueError('Bad positions in period')
            current = None
            for pos in range(1, n + 1):
                if pos in points:
                    current = points[pos]
                elif curve == 'A01':
                    raise ValueError(f'Missing position {pos} in an A01 curve')
                t = start + (pos - 1) * step
                if (key, t) in values and values[(key, t)][0] != current:
                    raise ValueError(f'Conflicting values for {key} at {t}')
                values[(key, t)] = (current, res)
    if not values:
        raise LookupError('No points in response')
    rows = [{'timestamp_utc': t.isoformat(), 'key': k, 'value_mw': v, 'resolution': r} for (k, t), (v, r) in sorted(values.items())]
    return pd.DataFrame(rows)


def to_quarter_hours(frame):
    """Spread coarser MW levels onto 15-minute stamps (a level holds for each quarter of its period)."""
    out = []
    for _, r in frame.iterrows():
        n = int(RESOLUTION[r.resolution] / RESOLUTION['PT15M'])
        start = pd.Timestamp(r.timestamp_utc)
        out += [{'timestamp_utc': (start + k * RESOLUTION['PT15M']).isoformat(), 'key': r.key, 'value_mw': r.value_mw}
                for k in range(n)]
    return pd.DataFrame(out).drop_duplicates(['timestamp_utc', 'key'])
