"""
Views for displaying email campaign and form analytics statistics.
Provides Mailerlite-like interface for viewing detailed stats.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Avg, Sum, F
from django.db.models.functions import Trunc
from django.utils import timezone
from datetime import timedelta
from .models_email import EmailCampaign, EmailRecipient, EmailLink, EmailClick, EmailOpen
from .models_form import FormConfiguration, FormAnalytics, FormView, FormFieldInteraction


@login_required
def campaign_stats_detail(request, campaign_id):
    """Detailed statistics for an email campaign (Mailerlite-style)"""
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
    
    return render(request, 'dashboard/campaign_stats_detail.html', context)


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
    """Detailed statistics for a form (Mailerlite-style)"""
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
    campaigns = EmailCampaign.objects.select_related('event').order_by('-created_at')
    
    # Add stats to each campaign
    campaign_stats = []
    for campaign in campaigns:
        campaign_stats.append({
            'campaign': campaign,
            'total_recipients': campaign.recipients.count(),
            'open_rate': campaign.get_open_rate(),
            'click_rate': campaign.get_click_rate(),
            'status': campaign.status,
        })
    
    context = {
        'campaign_stats': campaign_stats,
    }
    
    return render(request, 'dashboard/campaign_list_with_stats.html', context)


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
