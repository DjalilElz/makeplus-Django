"""
Brevo Statistics Synchronization Module

Syncs email campaign statistics from Brevo servers to local database.
Uses email + time-based filtering since messageId filtering doesn't work for transactional emails.
"""

from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
from .brevo_client import get_brevo_client
from .models_email import EmailCampaign, EmailRecipient


def sync_campaign_stats_from_brevo(campaign):
    """
    Sync campaign statistics from Brevo using email-based filtering
    
    Since Brevo's transactional email API doesn't support messageId filtering,
    we filter by email address and time window.
    
    Args:
        campaign: EmailCampaign instance
    
    Returns:
        dict: Sync results with counts
    """
    try:
        client = get_brevo_client()
        
        # Get all recipients that were sent
        recipients = campaign.recipients.filter(
            status__in=['sent', 'delivered']
        ).all()
        
        if not recipients.exists():
            return {
                'success': False,
                'error': 'No sent recipients found for this campaign'
            }
        
        print(f"\n{'='*70}")
        print(f"SYNCING STATS FOR CAMPAIGN: {campaign.name}")
        print(f"Campaign ID: {campaign.id}")
        print(f"Sent at: {campaign.sent_at}")
        print(f"Total recipients: {recipients.count()}")
        print(f"{'='*70}\n")
        
        # Track counts
        opens_synced = 0
        clicks_synced = 0
        recipients_updated = 0
        errors = []
        
        # Calculate days to fetch (from campaign sent date)
        campaign_sent_time = campaign.sent_at or timezone.now()
        days_since_sent = (timezone.now() - campaign_sent_time).days + 1
        days_to_fetch = min(days_since_sent + 1, 30)
        
        print(f"Fetching events from last {days_to_fetch} days\n")
        
        with transaction.atomic():
            # STEP 1: RESET ALL STATS TO ZERO
            print("STEP 1: Resetting all recipient stats to 0...")
            for recipient in recipients:
                recipient.open_count = 0
                recipient.opens_count = 0
                recipient.click_count = 0
                recipient.clicks_count = 0
                recipient.first_opened_at = None
                recipient.last_opened_at = None
                recipient.save()
            print(f"✓ Reset {recipients.count()} recipients\n")
            
            # STEP 2: FETCH EVENTS FOR EACH RECIPIENT
            print("STEP 2: Fetching events from Brevo...\n")
            
            for recipient in recipients:
                try:
                    print(f"→ {recipient.email}")
                    print(f"  Sent at: {recipient.sent_at}")
                    
                    # Fetch events for this specific email
                    events_result = client.get_email_events(
                        email=recipient.email,
                        days=days_to_fetch,
                        limit=1000
                    )
                    
                    events = events_result.get('events', [])
                    print(f"  Total events found: {len(events)}")
                    
                    # Filter events to only those AFTER this recipient was sent the email
                    recipient_sent_time = recipient.sent_at or campaign_sent_time
                    if recipient_sent_time.tzinfo is None:
                        recipient_sent_time = timezone.make_aware(recipient_sent_time)
                    
                    recipient_opens = 0
                    recipient_clicks = 0
                    first_open_time = None
                    last_open_time = None
                    
                    matched_events = 0
                    skipped_time = 0
                    
                    for event in events:
                        event_type = event.get('event')
                        event_date_str = event.get('date')
                        
                        # Parse event date
                        try:
                            if event_date_str.endswith('Z'):
                                event_date_str = event_date_str[:-1] + '+00:00'
                            event_date = datetime.fromisoformat(event_date_str)
                            if event_date.tzinfo is None:
                                event_date = timezone.make_aware(event_date)
                        except:
                            continue
                        
                        # Filter 1: Event must be AFTER email was sent
                        if event_date < recipient_sent_time:
                            skipped_time += 1
                            continue
                        
                        # Filter 2: Event must be within 7 days of sending
                        time_diff = (event_date - recipient_sent_time).total_seconds()
                        if time_diff > (7 * 24 * 3600):
                            skipped_time += 1
                            continue
                        
                        # NOTE: We don't filter by subject because Brevo personalizes it before sending
                        # So the event subject will have "test123" instead of "{{first_name}}"
                        
                        matched_events += 1
                        
                        # Count opens
                        if event_type == 'opened':
                            recipient_opens += 1
                            if first_open_time is None:
                                first_open_time = event_date
                            last_open_time = event_date
                            print(f"    ✓ Open at {event_date}")
                        
                        # Count clicks
                        elif event_type == 'clicks':
                            recipient_clicks += 1
                            print(f"    ✓ Click at {event_date}")
                    
                    print(f"  Matched events: {matched_events}")
                    print(f"  Skipped (time): {skipped_time}")
                    print(f"  Opens: {recipient_opens}, Clicks: {recipient_clicks}")
                    
                    # Update recipient
                    if recipient_opens > 0 or recipient_clicks > 0:
                        recipient.open_count = recipient_opens
                        recipient.opens_count = recipient_opens
                        recipient.click_count = recipient_clicks
                        recipient.clicks_count = recipient_clicks
                        
                        if first_open_time:
                            recipient.first_opened_at = first_open_time
                        if last_open_time:
                            recipient.last_opened_at = last_open_time
                        
                        recipient.save()
                        recipients_updated += 1
                        
                        opens_synced += recipient_opens
                        clicks_synced += recipient_clicks
                        
                        print(f"  ✓ UPDATED\n")
                    else:
                        recipient.save()
                        print(f"  - No activity\n")
                    
                except Exception as e:
                    error_msg = f"{recipient.email}: {str(e)}"
                    print(f"  ✗ ERROR: {error_msg}\n")
                    errors.append(error_msg)
                    continue
            
            # STEP 3: UPDATE CAMPAIGN TOTALS
            print("\nSTEP 3: Calculating campaign totals...")
            campaign.unique_opens = campaign.recipients.filter(open_count__gt=0).count()
            campaign.unique_clicks = campaign.recipients.filter(click_count__gt=0).count()
            campaign.total_opened = sum(r.open_count for r in campaign.recipients.all())
            campaign.total_clicked = sum(r.click_count for r in campaign.recipients.all())
            campaign.save()
            
            print(f"\n{'='*70}")
            print(f"SYNC COMPLETE")
            print(f"{'='*70}")
            print(f"Recipients updated: {recipients_updated}")
            print(f"Total opens synced: {opens_synced}")
            print(f"Total clicks synced: {clicks_synced}")
            print(f"Errors: {len(errors)}")
            print(f"\nCAMPAIGN TOTALS:")
            print(f"  Unique opens: {campaign.unique_opens} ({campaign.unique_opens / recipients.count() * 100:.1f}%)")
            print(f"  Unique clicks: {campaign.unique_clicks} ({campaign.unique_clicks / recipients.count() * 100:.1f}%)")
            print(f"  Total opens: {campaign.total_opened}")
            print(f"  Total clicks: {campaign.total_clicked}")
            print(f"{'='*70}\n")
        
        return {
            'success': True,
            'opens': opens_synced,
            'clicks': clicks_synced,
            'recipients_updated': recipients_updated,
            'errors': errors
        }
        
    except Exception as e:
        import traceback
        print(f"\n{'='*70}")
        print(f"FATAL ERROR")
        print(f"{'='*70}")
        traceback.print_exc()
        print(f"{'='*70}\n")
        return {
            'success': False,
            'error': str(e)
        }
