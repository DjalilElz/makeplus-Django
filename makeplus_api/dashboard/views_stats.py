"""
Views for displaying email campaign and form analytics statistics.
Provides Postmark-like interface for viewing detailed stats.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q, Avg, Sum, F
from django.db.models.functions import Trunc
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta, datetime, time
from .models_email import EmailCampaign, EmailRecipient, EmailLink, EmailClick, EmailOpen
from .models_form import FormConfiguration, FormAnalytics, FormView, FormFieldInteraction
from .views import is_staff_user
from .stats_insights import build_insights, chart_payload, person_name


@login_required
def campaign_stats_detail(request, campaign_id):
    """Detailed statistics for an email campaign (Postmark-style)"""
    campaign = get_object_or_404(EmailCampaign, id=campaign_id)
    
    # Overall statistics
    total_recipients = campaign.recipients.count()
    # Count 'sent' and 'delivered' as delivered
    delivered = campaign.recipients.filter(status__in=['sent', 'delivered']).count()
    bounced = campaign.recipients.filter(status='bounced').count()
    unsubscribed = campaign.recipients.filter(status='unsubscribed').count()
    
    # Engagement stats - recalculate from actual opens
    unique_opens = campaign.recipients.filter(open_count__gt=0).count()
    unique_clicks = campaign.recipients.filter(click_count__gt=0).count()
    
    # Calculate rates based on delivered
    open_rate = round((unique_opens / delivered * 100) if delivered > 0 else 0, 2)
    click_rate = round((unique_clicks / delivered * 100) if delivered > 0 else 0, 2)
    
    # Click-to-open rate (CTOR)
    ctor = round((unique_clicks / unique_opens * 100) if unique_opens > 0 else 0, 2)
    
    # Get top performing links
    top_links = EmailLink.objects.filter(campaign=campaign).order_by('-unique_clicks')[:10]
    
    # Get most engaged recipients
    top_recipients = EmailRecipient.objects.filter(
        campaign=campaign
    ).annotate(
        engagement_score=F('open_count') + (F('click_count') * 2)
    ).order_by('-engagement_score')[:20]
    
    # Detailed recipient lists
    all_recipients_list = campaign.recipients.all().order_by('-open_count', '-click_count')
    
    # Recipients who opened (at least once)
    recipients_who_opened = campaign.recipients.filter(open_count__gt=0).order_by('-open_count')
    
    # Recipients who clicked (at least once) with unique links count
    recipients_who_clicked = []
    for recipient in campaign.recipients.filter(click_count__gt=0).order_by('-click_count'):
        # Count unique links this recipient clicked
        unique_links = EmailClick.objects.filter(recipient=recipient).values('link').distinct().count()
        recipient.unique_links_clicked = unique_links
        recipients_who_clicked.append(recipient)
    
    # Recipients who did not open
    recipients_not_opened = campaign.recipients.filter(open_count=0).order_by('email')
    
    # Timeline data - opens and clicks over time
    opens_timeline = EmailOpen.objects.filter(
        recipient__campaign=campaign
    ).annotate(
        hour=Trunc('opened_at', 'hour')
    ).values('hour').annotate(count=Count('id')).order_by('hour')
    
    clicks_timeline = EmailClick.objects.filter(
        recipient__campaign=campaign
    ).annotate(
        hour=Trunc('clicked_at', 'hour')
    ).values('hour').annotate(count=Count('id')).order_by('hour')
    
    # Device/client breakdown (from user agents)
    device_stats = {
        'desktop': 0,
        'mobile': 0,
        'tablet': 0,
        'unknown': 0
    }
    
    for recipient in campaign.recipients.all():
        opens = EmailOpen.objects.filter(recipient=recipient).first()
        if opens and opens.user_agent:
            ua_lower = opens.user_agent.lower()
            if 'mobile' in ua_lower or 'android' in ua_lower or 'iphone' in ua_lower:
                device_stats['mobile'] += 1
            elif 'tablet' in ua_lower or 'ipad' in ua_lower:
                device_stats['tablet'] += 1
            elif 'mozilla' in ua_lower or 'chrome' in ua_lower or 'safari' in ua_lower:
                device_stats['desktop'] += 1
            else:
                device_stats['unknown'] += 1
    
    # Geographic data (top locations by IP)
    locations = EmailOpen.objects.filter(
        recipient__campaign=campaign,
        ip_address__isnull=False
    ).values('ip_address').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    context = {
        'campaign': campaign,
        'total_recipients': total_recipients,
        'delivered': delivered,
        'bounced': bounced,
        'unsubscribed': unsubscribed,
        'unique_opens': unique_opens,
        'unique_clicks': unique_clicks,
        'open_rate': open_rate,
        'click_rate': click_rate,
        'ctor': ctor,
        'top_links': top_links,
        'top_recipients': top_recipients,
        'all_recipients_list': all_recipients_list,
        'recipients_who_opened': recipients_who_opened,
        'recipients_who_clicked': recipients_who_clicked,
        'recipients_not_opened': recipients_not_opened,
        'opens_timeline': list(opens_timeline),
        'clicks_timeline': list(clicks_timeline),
        'device_stats': device_stats,
        'locations': locations,
    }
    
    response = render(request, 'dashboard/campaign_stats_detail.html', context)
    # Add cache control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response


@login_required
def campaign_recipient_detail(request, campaign_id, recipient_id):
    """Detailed view of a single recipient's engagement"""
    campaign = get_object_or_404(EmailCampaign, id=campaign_id)
    recipient = get_object_or_404(EmailRecipient, id=recipient_id, campaign=campaign)
    
    # Get all opens
    opens = EmailOpen.objects.filter(recipient=recipient).order_by('-opened_at')
    
    # Get all clicks
    clicks = EmailClick.objects.filter(recipient=recipient).select_related('link').order_by('-clicked_at')
    
    # Get link summary - which links were clicked and how many times
    links_clicked = EmailClick.objects.filter(recipient=recipient).values('link').distinct()
    links_clicked_summary = []
    for link_data in links_clicked:
        link = EmailLink.objects.get(id=link_data['link'])
        click_events = EmailClick.objects.filter(recipient=recipient, link=link).order_by('clicked_at')
        links_clicked_summary.append({
            'url': link.original_url,
            'click_count': click_events.count(),
            'first_click': click_events.first().clicked_at if click_events.exists() else None,
            'last_click': click_events.last().clicked_at if click_events.exists() else None,
        })
    
    # Sort by click count descending
    links_clicked_summary = sorted(links_clicked_summary, key=lambda x: x['click_count'], reverse=True)
    
    context = {
        'campaign': campaign,
        'recipient': recipient,
        'opens': opens,
        'clicks': clicks,
        'links_clicked_summary': links_clicked_summary,
    }
    
    return render(request, 'dashboard/campaign_recipient_detail.html', context)


@login_required
def form_stats_detail(request, form_id):
    """Detailed statistics for a form (Postmark-style)"""
    form = get_object_or_404(FormConfiguration, id=form_id)
    
    # Get or create analytics
    analytics, created = FormAnalytics.objects.get_or_create(form=form)
    
    # Overall stats
    total_views = analytics.total_views
    total_submissions = analytics.total_submissions
    conversion_rate = analytics.conversion_rate
    
    # Device breakdown
    device_breakdown = analytics.device_breakdown or {}
    desktop_views = device_breakdown.get('desktop', 0)
    mobile_views = device_breakdown.get('mobile', 0)
    tablet_views = device_breakdown.get('tablet', 0)
    
    # Traffic sources
    traffic_sources = analytics.traffic_sources or {}
    top_sources = sorted(traffic_sources.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Field-level analytics
    field_stats = FormFieldInteraction.objects.filter(
        form_view__form=form
    ).values('field_name').annotate(
        total_interactions=Count('id'),
        avg_time_spent=Avg('time_spent'),
        avg_changes=Avg('changes_count'),
        completion_rate=Count('id', filter=Q(completed=True)) * 100.0 / Count('id')
    ).order_by('-total_interactions')
    
    # Conversion funnel
    views_with_interaction = FormView.objects.filter(form=form).exclude(
        fieldinteractions__isnull=True
    ).distinct().count()
    
    started_rate = round((views_with_interaction / total_views * 100) if total_views > 0 else 0, 2)
    
    # Timeline - views and submissions over time
    views_timeline = FormView.objects.filter(form=form).extra(
        select={'date': "date(viewed_at)"}
    ).values('date').annotate(count=Count('id')).order_by('date')
    
    # Top UTM campaigns
    utm_campaigns = FormView.objects.filter(
        form=form,
        utm_campaign__isnull=False
    ).values('utm_campaign').annotate(
        views=Count('id'),
        conversions=Count('id', filter=Q(completed=True))
    ).order_by('-views')[:10]
    
    # Browser stats
    browser_stats = FormView.objects.filter(
        form=form,
        browser__isnull=False
    ).values('browser').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Average time on form
    avg_time_stats = FormFieldInteraction.objects.filter(
        form_view__form=form
    ).aggregate(
        avg_time=Avg('time_spent')
    )
    
    # Dropout fields (fields with low completion rate)
    dropout_fields = FormFieldInteraction.objects.filter(
        form_view__form=form
    ).values('field_name').annotate(
        started=Count('id'),
        completed=Count('id', filter=Q(completed=True)),
        dropout_rate=(Count('id') - Count('id', filter=Q(completed=True))) * 100.0 / Count('id')
    ).order_by('-dropout_rate')[:10]
    
    context = {
        'form': form,
        'analytics': analytics,
        'total_views': total_views,
        'total_submissions': total_submissions,
        'conversion_rate': conversion_rate,
        'started_rate': started_rate,
        'desktop_views': desktop_views,
        'mobile_views': mobile_views,
        'tablet_views': tablet_views,
        'top_sources': top_sources,
        'field_stats': field_stats,
        'views_timeline': list(views_timeline),
        'utm_campaigns': utm_campaigns,
        'browser_stats': browser_stats,
        'avg_time': avg_time_stats['avg_time'] or 0,
        'dropout_fields': dropout_fields,
    }
    
    return render(request, 'dashboard/form_stats_detail.html', context)


@login_required
def campaign_list_with_stats(request):
    """List all campaigns with summary stats"""
    from events.models import Event
    from django.views.decorators.cache import never_cache
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    event_filter = request.GET.get('event', '')
    
    # Base queryset
    campaigns = EmailCampaign.objects.select_related('event').order_by('-created_at')
    
    # Apply filters
    if status_filter:
        campaigns = campaigns.filter(status=status_filter)
    if event_filter:
        campaigns = campaigns.filter(event_id=event_filter)
    
    # Get all events for filter dropdown
    events = Event.objects.all().order_by('-created_at')
    
    # Calculate counts for filter buttons
    all_campaigns = EmailCampaign.objects.all()
    total_count = all_campaigns.count()
    draft_count = all_campaigns.filter(status='draft').count()
    sent_count = all_campaigns.filter(status='sent').count()
    sending_count = all_campaigns.filter(status='sending').count()
    
    # Add stats to each campaign
    campaign_stats = []
    for campaign in campaigns:
        recipients = campaign.recipients.all()
        total_recipients = recipients.count()
        sent_count_campaign = recipients.filter(status__in=['sent', 'delivered']).count()
        opened_count = recipients.filter(open_count__gt=0).count()
        clicked_count = recipients.filter(click_count__gt=0).count()
        
        campaign_stats.append({
            'campaign': campaign,
            'total_recipients': total_recipients,
            'sent_count': sent_count_campaign,
            'opened_count': opened_count,
            'clicked_count': clicked_count,
            'open_rate': campaign.get_open_rate(),
            'click_rate': campaign.get_click_rate(),
            'status': campaign.status,
        })
    
    context = {
        'campaign_stats': campaign_stats,
        'events': events,
        'total_count': total_count,
        'draft_count': draft_count,
        'sent_count': sent_count,
        'sending_count': sending_count,
    }
    
    response = render(request, 'dashboard/campaign_list_with_stats.html', context)
    # Add cache control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response


@login_required
def form_list_with_stats(request):
    """List all forms with summary stats"""
    forms = FormConfiguration.objects.select_related('event', 'created_by').order_by('-created_at')
    
    # Add analytics to each form
    form_stats = []
    for form in forms:
        try:
            analytics = FormAnalytics.objects.get(form=form)
        except FormAnalytics.DoesNotExist:
            analytics = FormAnalytics.objects.create(form=form)
        
        form_stats.append({
            'form': form,
            'analytics': analytics,
        })
    
    context = {
        'form_stats': form_stats,
    }

    return render(request, 'dashboard/form_list_with_stats.html', context)


# ==================== Event Stats (combined caisse/attendance/scans) ====================

# Dashboard tables here (transactions, presence, scans) are display-only
# overviews, not exports -- capped so a large event's history can't make
# this page itself slow to render.
_EVENT_STATS_LIST_LIMIT = 200


def _parse_stats_date_range(request):
    """
    (date_from, date_to, date_from_str, date_to_str) from ?date_from=&date_to=,
    submitted by an <input type="datetime-local"> so the filter can narrow
    to an exact hour/minute ("between X and Y"), not just a whole day.
    date_from/date_to come back as exact timezone-aware instants (no
    start/end-of-day padding) since the input already carries a time.
    A bare YYYY-MM-DD (an older bookmarked link, or a browser that only
    submits a date) is still accepted and expanded to the full day so
    those links keep working. Invalid/missing values fall back to no
    bound (the empty string is also what re-populates the form's own
    inputs).
    """
    date_from_str = request.GET.get('date_from', '').strip()
    date_to_str = request.GET.get('date_to', '').strip()
    date_from = None
    date_to = None
    if date_from_str:
        try:
            date_from = timezone.make_aware(datetime.strptime(date_from_str, '%Y-%m-%dT%H:%M'))
        except ValueError:
            try:
                date_from = timezone.make_aware(
                    datetime.combine(datetime.strptime(date_from_str, '%Y-%m-%d').date(), time.min)
                )
            except ValueError:
                date_from_str = ''
    if date_to_str:
        try:
            date_to = timezone.make_aware(datetime.strptime(date_to_str, '%Y-%m-%dT%H:%M'))
        except ValueError:
            try:
                date_to = timezone.make_aware(
                    datetime.combine(datetime.strptime(date_to_str, '%Y-%m-%d').date(), time.max)
                )
            except ValueError:
                date_to_str = ''
    return date_from, date_to, date_from_str, date_to_str


def _in_date_range(queryset, field, date_from, date_to):
    if date_from:
        queryset = queryset.filter(**{f'{field}__gte': date_from})
    if date_to:
        queryset = queryset.filter(**{f'{field}__lte': date_to})
    return queryset


def _gather_event_stats(request, event):
    """
    Shared filter + query logic for the Stats page and its PDF/Excel
    exports, so an export always matches exactly what's on screen for the
    same filters (date range/hour, caisse, presence search, scan search).
    Returns unsliced querysets -- the page caps list sizes for render
    speed (_EVENT_STATS_LIST_LIMIT), the exports don't, since an export is
    explicitly asked for the full detail.
    """
    from events.models import ParticipantEventRegistration, ControllerScan, ExposantScan
    from caisse.models import Caisse, CaisseTransaction

    date_from, date_to, date_from_str, date_to_str = _parse_stats_date_range(request)
    scan_search = request.GET.get('scan_search', '').strip()
    presence_search = request.GET.get('presence_search', '').strip()

    caisses = list(Caisse.objects.filter(event=event).order_by('name'))
    caisse_id = request.GET.get('caisse_id', '').strip()
    selected_caisse = None
    if caisse_id:
        selected_caisse = next((c for c in caisses if str(c.id) == caisse_id), None)
        if not selected_caisse:
            caisse_id = ''  # unknown/stale id -- fall back to "all caisses"

    # ---- Money & transactions (every caisse station combined, unless one
    # is selected in the filter bar) ----
    # NOTE: the per-caisse .values().annotate() grouping below must run
    # against an UN-ordered queryset -- Django folds order_by() fields into
    # GROUP BY for a .values().annotate() call, which would silently break
    # the grouping (one row per transaction instead of per caisse) if
    # '-created_at' were applied first. The list(...) call materializes it
    # immediately, so reordering the queryset afterwards for display is safe.
    transactions_base_qs = CaisseTransaction.objects.filter(caisse__event=event, status='completed')
    if selected_caisse:
        transactions_base_qs = transactions_base_qs.filter(caisse=selected_caisse)
    transactions_base_qs = _in_date_range(transactions_base_qs, 'created_at', date_from, date_to)

    # Totals by payment mode -- the same payment_breakdown() the caisse
    # screen uses, so both always show the same figures. money_stats is
    # derived from it rather than queried separately.
    from caisse.services import payment_breakdown
    payment_totals = payment_breakdown(transactions_base_qs)
    money_stats = {
        'total_amount': payment_totals['total']['amount'],
        'transaction_count': payment_totals['total']['count'],
        'total_participants': payment_totals['total']['participants'],
    }
    # Per-mode sums come BEFORE total_amount: that annotation shadows the
    # model field of the same name for anything annotated after it.
    per_caisse_stats = list(transactions_base_qs.values('caisse_id', 'caisse__name').annotate(
        cash_amount=Sum('total_amount', filter=Q(payment_method='cash')),
        bank_transfer_amount=Sum('total_amount', filter=Q(payment_method='bank_transfer')),
        sponsoring_amount=Sum('total_amount', filter=Q(payment_method='sponsoring')),
        transaction_count=Count('id'),
        total_participants=Count('participant_id', distinct=True),
        total_amount=Sum('total_amount'),
    ).order_by('caisse__name'))

    transactions_qs = transactions_base_qs.select_related(
        'caisse', 'participant__user', 'sponsor',
    ).prefetch_related('items').order_by('-created_at')

    # ---- Presence (event-wide check-in, set by the caisse only). The
    # base queryset feeds the figures and charts; the name/e-mail/badge
    # search only narrows the detail list. ----
    presence_base_qs = _in_date_range(
        ParticipantEventRegistration.objects.filter(event=event, is_checked_in=True),
        'checked_in_at', date_from, date_to,
    )
    presence_qs = presence_base_qs.select_related('participant__user')
    if presence_search:
        presence_qs = presence_qs.filter(
            Q(participant__user__first_name__icontains=presence_search)
            | Q(participant__user__last_name__icontains=presence_search)
            | Q(participant__user__email__icontains=presence_search)
            | Q(participant__badge_id__icontains=presence_search)
        )
    presence_qs = presence_qs.order_by('-checked_in_at')
    presence_total = presence_base_qs.count()
    presence_count = presence_qs.count() if presence_search else presence_total
    total_registered = ParticipantEventRegistration.objects.filter(event=event).count()

    # ---- Scans (badge controllers + exhibitor booth visits) ----
    # One "Compte" filter for both kinds of account: ?account=c<user id>
    # for a controller, e<participant id> for an exposant. The older
    # controller_id / exposant_id parameters still work (bookmarks).
    controller_options = [
        {'key': f"c{row['controller_id']}",
         'name': person_name(row['controller__first_name'], row['controller__last_name'], row['controller__username'])}
        for row in ControllerScan.objects.filter(event=event).order_by()
        .values('controller_id', 'controller__first_name', 'controller__last_name', 'controller__username').distinct()
    ]
    exposant_options = [
        {'key': f"e{row['exposant_id']}",
         'name': person_name(row['exposant__user__first_name'], row['exposant__user__last_name'], row['exposant__user__username'])}
        for row in ExposantScan.objects.filter(event=event).order_by()
        .values('exposant_id', 'exposant__user__first_name', 'exposant__user__last_name', 'exposant__user__username').distinct()
    ]
    controller_options.sort(key=lambda o: o['name'].lower())
    exposant_options.sort(key=lambda o: o['name'].lower())

    account = request.GET.get('account', '').strip()
    if not account and request.GET.get('controller_id', '').strip():
        account = 'c' + request.GET['controller_id'].strip()
    elif not account and request.GET.get('exposant_id', '').strip():
        account = 'e' + request.GET['exposant_id'].strip()
    selected_account = next((o for o in controller_options + exposant_options if o['key'] == account), None)
    if not selected_account:
        account = ''
    controller_id = account[1:] if account.startswith('c') else ''
    exposant_id = account[1:] if account.startswith('e') else ''

    controller_scans_base_qs = _in_date_range(
        ControllerScan.objects.filter(event=event), 'scanned_at', date_from, date_to,
    )
    exposant_scans_base_qs = _in_date_range(
        ExposantScan.objects.filter(event=event), 'scanned_at', date_from, date_to,
    )
    if controller_id:
        controller_scans_base_qs = controller_scans_base_qs.filter(controller_id=controller_id)
        exposant_scans_base_qs = exposant_scans_base_qs.none()
    elif exposant_id:
        exposant_scans_base_qs = exposant_scans_base_qs.filter(exposant_id=exposant_id)
        controller_scans_base_qs = controller_scans_base_qs.none()

    controller_scans_qs = controller_scans_base_qs.select_related('controller')
    exposant_scans_qs = exposant_scans_base_qs.select_related('exposant__user', 'scanned_participant__user')
    if scan_search:
        controller_scans_qs = controller_scans_qs.filter(
            Q(participant_name__icontains=scan_search)
            | Q(participant_email__icontains=scan_search)
            | Q(badge_id__icontains=scan_search)
        )
        exposant_scans_qs = exposant_scans_qs.filter(
            Q(scanned_participant__user__first_name__icontains=scan_search)
            | Q(scanned_participant__user__last_name__icontains=scan_search)
            | Q(scanned_participant__user__email__icontains=scan_search)
            | Q(scanned_participant__badge_id__icontains=scan_search)
        )
    controller_scans_qs = controller_scans_qs.order_by('-scanned_at')
    exposant_scans_qs = exposant_scans_qs.order_by('-scanned_at')

    return {
        'date_from_str': date_from_str, 'date_to_str': date_to_str,
        'scan_search': scan_search, 'presence_search': presence_search,
        'caisses': caisses, 'caisse_id': caisse_id, 'selected_caisse': selected_caisse,
        'money_stats': money_stats, 'per_caisse_stats': per_caisse_stats, 'payment_totals': payment_totals,
        'transactions_base_qs': transactions_base_qs, 'transactions_qs': transactions_qs,
        'presence_base_qs': presence_base_qs, 'presence_qs': presence_qs,
        'presence_total': presence_total, 'presence_count': presence_count, 'total_registered': total_registered,
        'controller_scans_base_qs': controller_scans_base_qs, 'exposant_scans_base_qs': exposant_scans_base_qs,
        'controller_scans_qs': controller_scans_qs, 'exposant_scans_qs': exposant_scans_qs,
        'account': account, 'selected_account': selected_account,
        'controller_options': controller_options, 'exposant_options': exposant_options,
    }


def _event_day_shortcuts(event, data):
    """Quick period buttons: 'Tout l'événement' + one per event day (max 14)."""
    from urllib.parse import urlencode

    keep = {k: v for k, v in (('caisse_id', data['caisse_id']), ('account', data['account'])) if v}
    shortcuts = [{
        'label': "Tout l'événement", 'query': urlencode(keep),
        'active': not data['date_from_str'] and not data['date_to_str'],
    }]
    if event.start_date and event.end_date:
        first = timezone.localtime(event.start_date).date()
        last = timezone.localtime(event.end_date).date()
        for index in range(min((last - first).days + 1, 14)):
            day = first + timedelta(days=index)
            date_from, date_to = f'{day.isoformat()}T00:00', f'{day.isoformat()}T23:59'
            shortcuts.append({
                'label': f'Jour {index + 1} · {day.strftime("%d/%m")}',
                'query': urlencode({**keep, 'date_from': date_from, 'date_to': date_to}),
                'active': data['date_from_str'] == date_from and data['date_to_str'] == date_to,
            })
    # "Aujourd'hui" only when today isn't already one of the event-day buttons.
    today = timezone.localdate()
    date_from, date_to = f'{today.isoformat()}T00:00', f'{today.isoformat()}T23:59'
    if not any(sc['query'].endswith(f'date_to={today.isoformat()}T23%3A59') for sc in shortcuts):
        shortcuts.append({
            'label': "Aujourd'hui",
            'query': urlencode({**keep, 'date_from': date_from, 'date_to': date_to}),
            'active': data['date_from_str'] == date_from and data['date_to_str'] == date_to,
        })
    return shortcuts


@login_required
@user_passes_test(is_staff_user)
def event_stats(request, event_id):
    """
    Event dashboard: one filter bar (period, caisse, account) applied to
    everything -- money, presence, scans, charts and both exports -- then
    key figures, insights (peaks, refusals, double scans, stand ranking),
    charts, and the detail lists folded underneath.
    """
    from events.models import Event

    event = get_object_or_404(Event, id=event_id)
    data = _gather_event_stats(request, event)
    insights = build_insights(data)

    transaction_count = data['money_stats']['transaction_count'] or 0
    controller_scans_qs = data['controller_scans_qs']
    exposant_scans_qs = data['exposant_scans_qs']
    controller_scans_count = controller_scans_qs.count() if data['scan_search'] else insights['controller_totals']['scans']
    exposant_scans_count = exposant_scans_qs.count() if data['scan_search'] else insights['exposant_totals']['scans']
    total_registered = data['total_registered']

    context = {
        'event': event,
        'date_from': data['date_from_str'],
        'date_to': data['date_to_str'],
        'scan_search': data['scan_search'],
        'presence_search': data['presence_search'],
        'account': data['account'],
        'selected_account': data['selected_account'],
        'controller_options': data['controller_options'],
        'exposant_options': data['exposant_options'],
        'caisses': data['caisses'],
        'caisse_id': data['caisse_id'],
        'selected_caisse': data['selected_caisse'],
        'day_shortcuts': _event_day_shortcuts(event, data),
        'money_stats': data['money_stats'],
        'payment_totals': data['payment_totals'],
        'per_caisse_stats': data['per_caisse_stats'],
        'insights': insights,
        'chart_data': chart_payload(insights, data['per_caisse_stats']),
        'presence_total': data['presence_total'],
        'presence_rate': round(100 * data['presence_total'] / total_registered) if total_registered else 0,
        'total_registered': total_registered,
        'transactions': data['transactions_qs'][:_EVENT_STATS_LIST_LIMIT],
        'transactions_total_count': transaction_count,
        'transactions_truncated': transaction_count > _EVENT_STATS_LIST_LIMIT,
        'presence_list': data['presence_qs'][:_EVENT_STATS_LIST_LIMIT],
        'presence_count': data['presence_count'],
        'presence_truncated': data['presence_count'] > _EVENT_STATS_LIST_LIMIT,
        'controller_scans': controller_scans_qs[:_EVENT_STATS_LIST_LIMIT],
        'controller_scans_count': controller_scans_count,
        'exposant_scans': exposant_scans_qs[:_EVENT_STATS_LIST_LIMIT],
        'exposant_scans_count': exposant_scans_count,
        'list_limit': _EVENT_STATS_LIST_LIMIT,
        'export_querystring': request.GET.urlencode(),
    }
    return render(request, 'dashboard/event_stats.html', context)


def _readable_stats_date(value, fallback):
    # '2026-10-28T09:30' -> '28/10/2026 09:30'
    if not value:
        return fallback
    try:
        return datetime.fromisoformat(value).strftime('%d/%m/%Y %H:%M')
    except ValueError:
        return value


def _stats_period_label(data):
    return (f"{_readable_stats_date(data['date_from_str'], 'depuis le début')} → "
            f"{_readable_stats_date(data['date_to_str'], 'aujourd’hui')}")


@login_required
@user_passes_test(is_staff_user)
def event_stats_export_excel(request, event_id):
    """
    One workbook with everything behind the Stats dashboard, for the exact
    filters applied on screen (period, caisse, account): summary and
    insights, activity over time, per-account figures, stand ranking, the
    account x time grid, payments, double scans, and every transaction,
    check-in and scan (uncapped -- the page caps its lists, the export
    doesn't).
    """
    from django.utils.text import slugify
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    from events.models import Event

    event = get_object_or_404(Event, id=event_id)
    data = _gather_event_stats(request, event)
    insights = build_insights(data)
    money_stats = data['money_stats']
    payment_totals = data['payment_totals']
    ctotals = insights['controller_totals']

    header_fill = PatternFill(start_color="2D1B6B", end_color="2D1B6B", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    section_font = Font(bold=True, color="872C7A", size=12)
    bold = Font(bold=True)

    def local(dt, fmt='%d/%m/%Y %H:%M'):
        return timezone.localtime(dt).strftime(fmt) if dt else ''

    def header(ws, labels):
        ws.append(labels)
        for cell in ws[ws.max_row]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

    def section(ws, title):
        if ws.max_row > 1:
            ws.append([])
        ws.append([title])
        ws.cell(row=ws.max_row, column=1).font = section_font

    def widths(ws, values):
        for col, width in enumerate(values, start=1):
            ws.column_dimensions[get_column_letter(col)].width = width

    def table_sheet(title, labels, rows, col_widths):
        ws = wb.create_sheet(title)
        header(ws, labels)
        for row in rows:
            ws.append(row)
        ws.freeze_panes = 'A2'
        if rows:
            ws.auto_filter.ref = ws.dimensions
        widths(ws, col_widths)
        return ws

    wb = Workbook()

    # ---- Résumé ----
    ws = wb.active
    ws.title = "Résumé"
    ws.append([f"Tableau de bord — {event.name}"])
    ws.cell(row=1, column=1).font = Font(bold=True, size=14, color="2D1B6B")
    ws.append(["Période", _stats_period_label(data)])
    ws.append(["Caisse", data['selected_caisse'].name if data['selected_caisse'] else 'Toutes les caisses'])
    ws.append(["Compte", data['selected_account']['name'] if data['selected_account'] else 'Tous les comptes'])
    ws.append(["Exporté le", timezone.localtime().strftime('%d/%m/%Y %H:%M')])

    section(ws, "Chiffres clés")
    total_registered = data['total_registered']
    for label, value in (
        ("Montant total (DZD)", float(money_stats['total_amount'] or 0)),
        ("Transactions", money_stats['transaction_count'] or 0),
        ("Participants traités en caisse", money_stats['total_participants'] or 0),
        ("Participants présents", data['presence_total']),
        ("Total inscrits", total_registered),
        ("Taux de présence (%)", round(100 * data['presence_total'] / total_registered, 1) if total_registered else 0),
        ("Scans contrôleurs", ctotals['scans']),
        ("Participants distincts scannés (contrôleurs)", ctotals['distinct']),
        ("Laissés entrer", ctotals['granted']),
        ("Accès refusé", ctotals['denied']),
        ("Sans décision", ctotals['undecided']),
        ("Scans « non inscrit »", ctotals['not_registered']),
        ("Scans refusés (refus + non inscrits)", ctotals['refused']),
        ("Doubles scans (< 5 min)", ctotals['doubles']),
        ("Scans exposants", insights['exposant_totals']['scans']),
        ("Visiteurs distincts des stands", insights['exposant_totals']['distinct']),
        ("Stands actifs", len(insights['stands'])),
    ):
        ws.append([label, value])

    section(ws, "Pointes d'activité")
    for label, peak in (("Arrivées", insights['peaks']['arrivals']), ("Scans", insights['peaks']['scans']),
                        ("Paiements", insights['peaks']['payments'])):
        ws.append([label, peak['label'] if peak else '—', peak['count'] if peak else 0])
    widths(ws, [44, 34, 14])

    # ---- Activité (per hour or per day) ----
    timeline = insights['timeline']
    unit = 'Jour' if timeline['granularity'] == 'day' else 'Heure'
    buckets = insights['buckets']
    rows = []
    for i, key in enumerate(buckets.keys):
        rows.append([
            buckets.range_label(key), timeline['arrivals'][i], timeline['payments'][i], timeline['amounts'][i],
            timeline['controller_scans'][i], timeline['exposant_scans'][i],
        ])
    table_sheet("Activité", [unit, "Arrivées", "Paiements", "Montant (DZD)", "Scans contrôleurs", "Scans exposants"],
                rows, [22, 12, 12, 16, 18, 18])

    # ---- Contrôleurs ----
    rows = [[
        a['name'], a['scans'], a['distinct'], a['granted'], a['denied'], a['undecided'], a['not_registered'],
        a['doubles'], a['peak']['label'] if a['peak'] else '', a['peak']['count'] if a['peak'] else 0,
        local(a['first_at']), local(a['last_at']),
    ] for a in insights['controllers']]
    table_sheet("Contrôleurs", [
        "Contrôleur", "Scans", "Participants distincts", "Laissés entrer", "Accès refusé", "Sans décision",
        "Non inscrits", "Doubles scans", "Pointe", "Scans à la pointe", "Premier scan", "Dernier scan",
    ], rows, [28, 10, 14, 14, 13, 13, 12, 13, 18, 12, 17, 17])

    # ---- Stands (exposants ranking) ----
    rows = [[
        st['rank'], st['name'], st['distinct'], st['scans'], st['peak']['label'] if st['peak'] else '',
        st['peak']['count'] if st['peak'] else 0, local(st['first_at']), local(st['last_at']),
    ] for st in insights['stands']]
    table_sheet("Stands", ["Rang", "Exposant", "Visiteurs distincts", "Scans", "Pointe", "Scans à la pointe",
                           "Premier scan", "Dernier scan"], rows, [7, 28, 16, 10, 18, 12, 17, 17])

    # ---- Account x time grid ----
    labels = [buckets.label(k) for k in buckets.keys]
    rows = [[a['name'], 'Contrôleur'] + a['series'] + [a['scans']] for a in insights['controllers']]
    rows += [[st['name'], 'Exposant'] + st['series'] + [st['scans']] for st in insights['stands']]
    table_sheet(f"Compte par {unit.lower()}", ["Compte", "Rôle"] + labels + ["Total"], rows,
                [28, 12] + [9] * len(labels) + [10])

    # ---- Paiements ----
    ws = wb.create_sheet("Paiements")
    section(ws, "Par mode de règlement")
    header(ws, ["Mode", "Organisme", "Transactions", "Montant (DZD)"])
    ws.append(["Espèces", "", payment_totals['cash']['count'], float(payment_totals['cash']['amount'])])
    ws.append(["Virement bancaire", "", payment_totals['bank_transfer']['count'], float(payment_totals['bank_transfer']['amount'])])
    ws.append(["Prise en charge", "Tous", payment_totals['sponsoring']['count'], float(payment_totals['sponsoring']['amount'])])
    for row in payment_totals['sponsors']:
        ws.append(["  Prise en charge", row['name'], row['count'], float(row['amount'])])
    if payment_totals['other']['count']:
        ws.append(["Mixte (ancien)", "", payment_totals['other']['count'], float(payment_totals['other']['amount'])])
    ws.append(["TOTAL", "", payment_totals['total']['count'], float(payment_totals['total']['amount'])])
    for cell in ws[ws.max_row]:
        cell.font = bold
    section(ws, "Par caisse")
    header(ws, ["Caisse", "Montant (DZD)", "Espèces", "Virement bancaire", "Prise en charge", "Transactions", "Participants"])
    for row in data['per_caisse_stats']:
        ws.append([
            row['caisse__name'], float(row['total_amount'] or 0), float(row['cash_amount'] or 0),
            float(row['bank_transfer_amount'] or 0), float(row['sponsoring_amount'] or 0),
            row['transaction_count'], row['total_participants'],
        ])
    widths(ws, [26, 22, 14, 18, 16, 14, 14])

    # ---- Doubles scans ----
    rows = [[d['participant'], d['badge_id'], d['controller'], d['count'],
             local(d['first_at'], '%d/%m/%Y %H:%M:%S'), local(d['last_at'], '%d/%m/%Y %H:%M:%S')]
            for d in insights['double_incidents']]
    table_sheet("Doubles scans", ["Participant", "Badge", "Contrôleur", "Scans", "Premier", "Dernier"],
                rows, [28, 16, 24, 8, 20, 20])

    # ---- Detail lists ----
    rows = [[
        txn.participant.user.get_full_name() or txn.participant.user.username, txn.participant.user.email,
        txn.caisse.name, ', '.join(i.name for i in txn.items.all()), float(txn.total_amount), txn.payment_display,
        local(txn.created_at),
    ] for txn in data['transactions_qs']]
    table_sheet("Transactions", ["Participant", "E-mail", "Caisse", "Articles", "Montant (DZD)", "Mode de règlement", "Date"],
                rows, [28, 30, 18, 40, 14, 26, 17])

    rows = [[
        reg.participant.user.get_full_name() or reg.participant.user.username, reg.participant.user.email,
        reg.participant.badge_id, local(reg.checked_in_at),
    ] for reg in data['presence_qs']]
    table_sheet("Présence", ["Participant", "E-mail", "Badge", "Présent depuis"], rows, [28, 30, 18, 17])

    decision_labels = {'granted': 'Laissé entrer', 'denied': 'Accès refusé'}
    result_labels = {'success': 'Inscrit', 'not_registered': 'Non inscrit', 'error': 'Erreur'}
    rows = [[
        local(scan.scanned_at, '%d/%m/%Y'), local(scan.scanned_at, '%H:%M:%S'),
        scan.controller.get_full_name() or scan.controller.username,
        scan.participant_name, scan.participant_email, scan.badge_id,
        result_labels.get(scan.status, scan.status), decision_labels.get(scan.access_decision, 'Sans décision'),
        local(scan.decided_at, '%H:%M:%S'),
    ] for scan in data['controller_scans_qs']]
    table_sheet("Scans contrôleurs", ["Date", "Heure", "Contrôleur", "Participant", "E-mail", "Badge", "Résultat",
                                      "Décision", "Heure de décision"], rows, [12, 10, 24, 28, 30, 16, 13, 15, 16])

    rows = [[
        local(scan.scanned_at, '%d/%m/%Y'), local(scan.scanned_at, '%H:%M:%S'),
        scan.exposant.user.get_full_name() or scan.exposant.user.username,
        scan.scanned_participant.user.get_full_name() or scan.scanned_participant.user.username,
        scan.scanned_participant.user.email, scan.notes or '',
    ] for scan in data['exposant_scans_qs']]
    table_sheet("Scans exposants", ["Date", "Heure", "Exposant", "Participant scanné", "E-mail", "Notes"],
                rows, [12, 10, 24, 28, 30, 40])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f'stats_{slugify(event.name)[:60]}_{timezone.localdate()}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response


@login_required
@user_passes_test(is_staff_user)
def event_stats_export_pdf(request, event_id):
    """
    "Rapport de caisse" (dashboard.caisse_report): MakePlus-branded PDF of
    the completed payments -- totals by payment mode, transactions per
    caisse, every payment line -- following the stats page's own filters
    (period, caisse) so it always matches what's on screen.
    """
    from django.utils.text import slugify
    from events.models import Event
    from .caisse_report import build_caisse_report

    event = get_object_or_404(Event, id=event_id)
    data = _gather_event_stats(request, event)

    scope_lines = []
    if data['date_from_str'] or data['date_to_str']:
        scope_lines.append('Période : ' + _stats_period_label(data))
    if data['selected_caisse']:
        scope_lines.append('Caisse : ' + data['selected_caisse'].name)
    edited_by = request.user.get_full_name().strip() or request.user.username
    pdf = build_caisse_report(event, data['transactions_qs'], edited_by, scope_lines)

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="rapport-caisse_{slugify(event.name)}_{timezone.localdate()}.pdf"'
    )
    return response
