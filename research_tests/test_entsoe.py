import unittest

import pandas as pd

from gridmind_research.entsoe import (
    feature_query,
    parse_prices,
    parse_quantities,
    query,
    split_days,
    to_quarter_hours,
)
from gridmind_research.polish_market import delivery_index, validate_day

NS = 'urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:3'


def document(periods, curve='A01', currency='EUR', unit='MWH'):
    """periods: list of (start, end, resolution, {position: price})."""
    body = ''.join(
        f'<Period><timeInterval><start>{s}</start><end>{e}</end></timeInterval><resolution>{r}</resolution>'
        + ''.join(f'<Point><position>{k}</position><price.amount>{v}</price.amount></Point>' for k, v in pts.items())
        + '</Period>' for s, e, r, pts in periods)
    return (f'<Publication_MarketDocument xmlns="{NS}"><TimeSeries><currency_Unit.name>{currency}</currency_Unit.name>'
            f'<price_Measure_Unit.name>{unit}</price_Measure_Unit.name><curveType>{curve}</curveType>{body}'
            '</TimeSeries></Publication_MarketDocument>').encode()


def utc_bounds(day):
    idx = delivery_index(day)
    return idx[0].strftime('%Y-%m-%dT%H:%MZ'), (idx[-1] + pd.Timedelta(minutes=15)).strftime('%Y-%m-%dT%H:%MZ'), len(idx)


class EntsoeTests(unittest.TestCase):
    def test_full_quarter_hour_day_passes_the_contract(self):
        s, e, n = utc_bounds('2026-07-01')
        frame, res, _ = parse_prices(document([(s, e, 'PT15M', {k: 50 + k for k in range(1, n + 1)})]))
        self.assertEqual(res, ['PT15M'])
        day = split_days(frame)['2026-07-01']
        values = validate_day(day, '2026-07-01')
        self.assertEqual(len(values), 96)
        self.assertEqual(values[0], 51)

    def test_clock_change_days_have_92_and_100_intervals(self):
        for day, n in [('2026-03-29', 92), ('2026-10-25', 100)]:
            s, e, m = utc_bounds(day)
            self.assertEqual(m, n)
            frame, _, _ = parse_prices(document([(s, e, 'PT15M', {k: 1.0 for k in range(1, n + 1)})]))
            self.assertEqual(len(validate_day(split_days(frame)[day], day)), n)

    def test_a03_repeats_omitted_prices(self):
        s, e, _ = utc_bounds('2026-07-01')
        frame, _, _ = parse_prices(document([(s, e, 'PT15M', {1: 10.0, 5: -3.5, 90: 7.0})], curve='A03'))
        v = validate_day(split_days(frame)['2026-07-01'], '2026-07-01')
        self.assertEqual(list(v[:6]), [10, 10, 10, 10, -3.5, -3.5])
        self.assertEqual(v[-1], 7.0)
        with self.assertRaises(ValueError):
            parse_prices(document([(s, e, 'PT15M', {1: 10.0, 5: 3.0})], curve='A01'))

    def test_hourly_prices_are_not_split_into_quarter_hours(self):
        s, e, _ = utc_bounds('2025-07-01')
        frame, res, _ = parse_prices(document([(s, e, 'PT60M', {k: 1.0 for k in range(1, 25)})]))
        self.assertEqual(res, ['PT60M'])
        self.assertEqual(len(frame), 24)
        with self.assertRaises(ValueError):
            validate_day(split_days(frame)['2025-07-01'], '2025-07-01')

    def test_rejects_units_conflicts_and_acknowledgements(self):
        s, e, _ = utc_bounds('2026-07-01')
        frame, _, currency = parse_prices(document([(s, e, 'PT15M', {1: 400.0})], curve='A03', currency='PLN'))
        self.assertEqual(currency, 'PLN')
        self.assertEqual(list(frame.columns), ['timestamp_utc', 'value_pln_mwh'])  # kept, never converted
        with self.assertRaises(ValueError):
            parse_prices(document([(s, e, 'PT15M', {1: 1.0})], curve='A03', unit='KWH'))
        with self.assertRaises(ValueError):
            parse_prices(document([(s, e, 'PT15M', {1: -650.0})], curve='A03'))  # below the SDAC floor
        twice = document([(s, e, 'PT15M', {1: 1.0}), (s, e, 'PT15M', {1: 2.0})], curve='A03')
        with self.assertRaises(ValueError):
            parse_prices(twice)
        ack = (b'<Acknowledgement_MarketDocument xmlns="urn:x"><Reason><code>999</code>'
               b'<text>No matching data found</text></Reason></Acknowledgement_MarketDocument>')
        with self.assertRaisesRegex(LookupError, 'No matching data'):
            parse_prices(ack)

    def test_query_has_no_token_and_requires_offsets(self):
        q = query(pd.Timestamp('2026-06-30T22:00Z'), pd.Timestamp('2026-07-01T22:00Z'))
        self.assertEqual(q['periodStart'], '202606302200')
        self.assertNotIn('securityToken', q)
        with self.assertRaises(ValueError):
            query(pd.Timestamp('2026-06-30 22:00'), pd.Timestamp('2026-07-01 22:00'))


GL = 'urn:iec62325.351:tc57wg16:451-6:generationloaddocument:3:0'


def gl_series(points, res='PT15M', psr=None, zone_tag='outBiddingZone_Domain.mRID', unit='MAW', start='2026-06-30T22:00Z', end='2026-07-01T22:00Z'):
    psr_xml = f'<MktPSRType><psrType>{psr}</psrType></MktPSRType>' if psr else ''
    pts = ''.join(f'<Point><position>{k}</position><quantity>{v}</quantity></Point>' for k, v in points.items())
    return (f'<TimeSeries><{zone_tag} codingScheme="A01">10YPL-AREA-----S</{zone_tag}>'
            f'<quantity_Measure_Unit.name>{unit}</quantity_Measure_Unit.name><curveType>A01</curveType>{psr_xml}'
            f'<Period><timeInterval><start>{start}</start><end>{end}</end></timeInterval><resolution>{res}</resolution>{pts}</Period></TimeSeries>')


def gl_document(*series):
    return f'<GL_MarketDocument xmlns="{GL}">{"".join(series)}</GL_MarketDocument>'.encode()


class EntsoeFeatureTests(unittest.TestCase):
    def test_load_series_and_hourly_levels(self):
        f = parse_quantities(gl_document(gl_series({k: 15000 + k for k in range(1, 97)})))
        self.assertEqual(set(f.key), {'total'})
        self.assertEqual(len(f), 96)
        hourly = parse_quantities(gl_document(gl_series({k: 100.0 * k for k in range(1, 25)}, res='PT60M')))
        q = to_quarter_hours(hourly)
        self.assertEqual(len(q), 96)
        self.assertEqual(list(q.value_mw[:5]), [100.0, 100.0, 100.0, 100.0, 200.0])

    def test_generation_keeps_production_and_drops_consumption(self):
        doc = gl_document(gl_series({k: 50.0 for k in range(1, 97)}, psr='B16', zone_tag='inBiddingZone_Domain.mRID'),
                          gl_series({k: 70.0 for k in range(1, 97)}, psr='B19', zone_tag='inBiddingZone_Domain.mRID'),
                          gl_series({k: 9.0 for k in range(1, 97)}, psr='B10', zone_tag='outBiddingZone_Domain.mRID'))
        f = parse_quantities(doc)
        self.assertEqual(set(f.key), {'B16', 'B19'})

    def test_rejects_wrong_units_and_prices_documents(self):
        with self.assertRaises(ValueError):
            parse_quantities(gl_document(gl_series({1: 1.0}, unit='MWH')))
        s, e, n = utc_bounds('2026-07-01')
        with self.assertRaises(ValueError):
            parse_quantities(document([(s, e, 'PT15M', {k: 1.0 for k in range(1, n + 1)})]))

    def test_feature_queries_name_the_right_domain(self):
        start, end = pd.Timestamp('2026-06-30T22:00Z'), pd.Timestamp('2026-07-01T22:00Z')
        self.assertEqual(feature_query('load_forecast', start, end)['outBiddingZone_Domain'], '10YPL-AREA-----S')
        self.assertEqual(feature_query('load_forecast', start, end)['processType'], 'A01')
        self.assertEqual(feature_query('generation', start, end)['in_Domain'], '10YPL-AREA-----S')
        self.assertNotIn('securityToken', feature_query('load_actual', start, end))


if __name__ == '__main__':
    unittest.main()
