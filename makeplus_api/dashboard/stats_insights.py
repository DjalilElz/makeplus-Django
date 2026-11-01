"""
Insights for the event Stats dashboard and its Excel export: activity over
time, per-account scan figures (controllers and exposants), peak times,
refused scans, double scans and the stand ranking.

Everything is grouped by the database (one row per hour / per account),
never by loading every scan, so the page stays fast with thousands of
scans. The only row-level pass is the double-scan detection, which reads a
few narrow columns.
"""
from collections import defaultdict
from datetime import timedelta

from django.db.models import Count, Max, Min, Q, Sum
from django.db.models.functions import TruncHour
from django.utils import timezone

# Same badge scanned again by the same controller within this window =
# a double scan (scanner glitch or a mistake), not a real second entry.
DOUBLE_SCAN_WINDOW = timedelta(minutes=5)

# Up to this many distinct days the timeline is per hour, beyond it per day.
HOURLY_MAX_DAYS = 2


def person_name(first, last, username):
    return f'{first or ""} {last or ""}'.strip() or username or '—'


def _hourly(qs, field, extra=None):
    """{local hour datetime: {'n': count, ...extra sums}} for a queryset."""
    annotations = {'n': Count('id')}
    annotations.update(extra or {})
    rows = qs.order_by().annotate(bucket=TruncHour(field)).values('bucket').annotate(**annotations)
    out = {}
    for row in rows:
        if row['bucket'] is None:
            continue
        out[timezone.localtime(row['bucket'])] = row
    return out


def _hourly_by(qs, field, key):
    """{account key: {local hour datetime: count}}."""
    rows = qs.order_by().annotate(bucket=TruncHour(field)).values(key, 'bucket').annotate(n=Count('id'))
    out = defaultdict(dict)
    for row in rows:
        if row['bucket'] is None:
            continue
        out[row[key]][timezone.localtime(row['bucket'])] = row['n']
    return out


class _Buckets:
    """
    Turns local hour datetimes into the timeline's buckets: hours when the
    activity spans up to HOURLY_MAX_DAYS days, whole days beyond that.
    """

    def __init__(self, hours):
        days = sorted({h.date() for h in hours})
        self.daily = len(days) > HOURLY_MAX_DAYS
        self.multi_day = len(days) > 1
        if not hours:
            self.keys = []
        elif self.daily:
            first, last = days[0], days[-1]
            self.keys = [first + timedelta(days=i) for i in range((last - first).days + 1)]
        else:
            first = min(hours).replace(minute=0, second=0, microsecond=0)
            last = max(hours).replace(minute=0, second=0, microsecond=0)
            count = int((last - first).total_seconds() // 3600) + 1
            self.keys = [first + timedelta(hours=i) for i in range(count)]
        self.granularity = 'day' if self.daily else 'hour'

    def key(self, hour):
        return hour.date() if self.daily else hour

    def label(self, key):
        if self.daily:
            return key.strftime('%d/%m')
        return key.strftime('%d/%m %Hh') if self.multi_day else key.strftime('%Hh')

    def range_label(self, key):
        """'10h–11h' (or '28/10 10h–11h') for an hour, '28/10/2026' for a day."""
        if self.daily:
            return key.strftime('%d/%m/%Y')
        end = (key + timedelta(hours=1)).strftime('%Hh')
        prefix = key.strftime('%d/%m ') if self.multi_day else ''
        return f'{prefix}{key.strftime("%Hh")}–{end}'

    def fold(self, hourly_counts):
        """{hour: n} -> list of counts aligned on self.keys."""
        totals = defaultdict(int)
        for hour, n in hourly_counts.items():
            totals[self.key(hour)] += n
        return [totals.get(k, 0) for k in self.keys]


def _peak(buckets, values, unit):
    if not values or max(values) == 0:
        return None
    index = max(range(len(values)), key=lambda i: values[i])
    return {'label': buckets.range_label(buckets.keys[index]), 'count': values[index], 'unit': unit}


def _double_scans(controller_scans_qs, controller_names):
    """
    Same participant scanned again by the same controller within
    DOUBLE_SCAN_WINDOW of their previous scan. Returns (incidents,
    extra scans per controller id).
    """
    rows = controller_scans_qs.order_by('controller_id', 'participant_user_id', 'scanned_at').values_list(
        'controller_id', 'participant_user_id', 'participant_name', 'badge_id', 'scanned_at',
    )
    incidents = []
    per_controller = defaultdict(int)
    current = None
    previous = None
    for controller_id, user_id, name, badge, scanned_at in rows.iterator():
        same = previous and previous[0] == controller_id and previous[1] == user_id
        if same and scanned_at - previous[2] <= DOUBLE_SCAN_WINDOW:
            if current is None:
                current = {
                    'controller': controller_names.get(controller_id, '—'),
                    'participant': name, 'badge_id': badge,
                    'first_at': previous[2], 'last_at': scanned_at, 'count': 2,
                }
                incidents.append(current)
            else:
                current['count'] += 1
                current['last_at'] = scanned_at
            per_controller[controller_id] += 1
        else:
            current = None
        previous = (controller_id, user_id, scanned_at)
    incidents.sort(key=lambda i: i['first_at'], reverse=True)
    return incidents, per_controller


def build_insights(data):
    """
    data: the dict from views_stats._gather_event_stats (base querysets,
    i.e. date/caisse/account filters applied, detail searches not).
    """
    controller_qs = data['controller_scans_base_qs']
    exposant_qs = data['exposant_scans_base_qs']
    presence_qs = data['presence_base_qs']
    transactions_qs = data['transactions_base_qs']

    # ---- Activity over time ----
    arrivals_h = {h: r['n'] for h, r in _hourly(presence_qs, 'checked_in_at').items()}
    controller_h = {h: r['n'] for h, r in _hourly(controller_qs, 'scanned_at').items()}
    exposant_h = {h: r['n'] for h, r in _hourly(exposant_qs, 'scanned_at').items()}
    payments_raw = _hourly(transactions_qs, 'created_at', {'amount': Sum('total_amount')})
    payments_h = {h: r['n'] for h, r in payments_raw.items()}

    buckets = _Buckets(set(arrivals_h) | set(controller_h) | set(exposant_h) | set(payments_h))
    timeline = {
        'granularity': buckets.granularity,
        'labels': [buckets.label(k) for k in buckets.keys],
        'arrivals': buckets.fold(arrivals_h),
        'controller_scans': buckets.fold(controller_h),
        'exposant_scans': buckets.fold(exposant_h),
        'payments': buckets.fold(payments_h),
        'amounts': [0.0] * len(buckets.keys),
    }
    amount_by_key = defaultdict(float)
    for hour, row in payments_raw.items():
        amount_by_key[buckets.key(hour)] += float(row['amount'] or 0)
    timeline['amounts'] = [amount_by_key.get(k, 0.0) for k in buckets.keys]

    all_scans = [a + b for a, b in zip(timeline['controller_scans'], timeline['exposant_scans'])]
    peaks = {
        'arrivals': _peak(buckets, timeline['arrivals'], 'arrivées'),
        'scans': _peak(buckets, all_scans, 'scans'),
        'payments': _peak(buckets, timeline['payments'], 'paiements'),
    }

    # ---- Controllers ----
    controller_rows = list(controller_qs.order_by().values(
        'controller_id', 'controller__first_name', 'controller__last_name', 'controller__username',
    ).annotate(
        scans=Count('id'),
        distinct=Count('participant_user_id', distinct=True),
        granted=Count('id', filter=Q(access_decision='granted')),
        denied=Count('id', filter=Q(access_decision='denied')),
        not_registered=Count('id', filter=Q(status='not_registered')),
        refused=Count('id', filter=Q(access_decision='denied') | Q(status='not_registered')),
        first_at=Min('scanned_at'),
        last_at=Max('scanned_at'),
    ))
    controller_names = {
        r['controller_id']: person_name(r['controller__first_name'], r['controller__last_name'], r['controller__username'])
        for r in controller_rows
    }
    double_incidents, doubles_by_controller = _double_scans(controller_qs, controller_names)
    controller_hourly = _hourly_by(controller_qs, 'scanned_at', 'controller_id')

    accounts = []
    for r in controller_rows:
        series = buckets.fold(controller_hourly.get(r['controller_id'], {}))
        accounts.append({
            'key': f"c{r['controller_id']}", 'role': 'Contrôleur', 'name': controller_names[r['controller_id']],
            'scans': r['scans'], 'distinct': r['distinct'],
            'granted': r['granted'], 'denied': r['denied'], 'undecided': r['scans'] - r['granted'] - r['denied'],
            'not_registered': r['not_registered'], 'refused': r['refused'],
            'doubles': doubles_by_controller.get(r['controller_id'], 0),
            'first_at': r['first_at'], 'last_at': r['last_at'],
            'peak': _peak(buckets, series, 'scans'), 'series': series,
        })

    # ---- Exposants (stands) ----
    exposant_rows = list(exposant_qs.order_by().values(
        'exposant_id', 'exposant__user__first_name', 'exposant__user__last_name', 'exposant__user__username',
    ).annotate(
        scans=Count('id'),
        distinct=Count('scanned_participant_id', distinct=True),
        first_at=Min('scanned_at'),
        last_at=Max('scanned_at'),
    ))
    exposant_hourly = _hourly_by(exposant_qs, 'scanned_at', 'exposant_id')
    stands = []
    for r in exposant_rows:
        series = buckets.fold(exposant_hourly.get(r['exposant_id'], {}))
        stands.append({
            'key': f"e{r['exposant_id']}", 'role': 'Exposant',
            'name': person_name(r['exposant__user__first_name'], r['exposant__user__last_name'], r['exposant__user__username']),
            'scans': r['scans'], 'distinct': r['distinct'],
            'first_at': r['first_at'], 'last_at': r['last_at'],
            'peak': _peak(buckets, series, 'visites'), 'series': series,
        })
    # Ranking: most distinct visitors first, total visits as tie-break.
    stands.sort(key=lambda s: (-s['distinct'], -s['scans'], s['name'].lower()))
    for rank, stand in enumerate(stands, start=1):
        stand['rank'] = rank

    accounts.sort(key=lambda a: (-a['scans'], a['name'].lower()))

    controller_totals = {
        'scans': sum(a['scans'] for a in accounts),
        'distinct': controller_qs.order_by().values('participant_user_id').distinct().count(),
        'granted': sum(a['granted'] for a in accounts),
        'denied': sum(a['denied'] for a in accounts),
        'undecided': sum(a['undecided'] for a in accounts),
        'not_registered': sum(a['not_registered'] for a in accounts),
        'refused': sum(a['refused'] for a in accounts),
        'doubles': sum(a['doubles'] for a in accounts),
    }
    exposant_totals = {
        'scans': sum(s['scans'] for s in stands),
        'distinct': exposant_qs.order_by().values('scanned_participant_id').distinct().count(),
    }

    return {
        'buckets': buckets,
        'timeline': timeline,
        'peaks': peaks,
        'controllers': accounts,
        'stands': stands,
        'controller_totals': controller_totals,
        'exposant_totals': exposant_totals,
        'double_incidents': double_incidents,
    }


def chart_payload(insights, per_caisse_stats):
    """JSON-safe data for the dashboard's charts (rendered with json_script)."""
    timeline = insights['timeline']
    return {
        'timeline': {k: timeline[k] for k in ('granularity', 'labels', 'arrivals', 'controller_scans', 'exposant_scans', 'payments')},
        'controllers': [
            {'name': a['name'], 'granted': a['granted'], 'denied': a['denied'], 'undecided': a['undecided'],
             'series': a['series']}
            for a in insights['controllers']
        ],
        'stands': [
            {'name': s['name'], 'scans': s['scans'], 'distinct': s['distinct'], 'series': s['series']}
            for s in insights['stands']
        ],
        'caisses': [
            {'name': row['caisse__name'], 'cash': float(row['cash_amount'] or 0),
             'bank_transfer': float(row['bank_transfer_amount'] or 0),
             'sponsoring': float(row['sponsoring_amount'] or 0)}
            for row in per_caisse_stats
        ],
    }
