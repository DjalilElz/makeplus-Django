"""
MailerLite API Client for MakePlus

Full integration with MailerLite API v2 for:
- Sending transactional emails
- Bulk campaign sending
- Tracking opens, clicks, bounces
- Subscriber management
- Stats synchronization
"""

import json
import urllib.request
import urllib.error
from django.conf import settings
from django.utils import timezone


class MailerLiteClient:
    """MailerLite API v2 Client"""
    
    BASE_URL = "https://connect.mailerlite.com/api"
    
    def __init__(self, api_token=None):
        self.api_token = api_token or getattr(settings, 'MAILERLITE_API_TOKEN', '')
        if not self.api_token:
            raise ValueError("MailerLite API token not configured")
    
    def _make_request(self, method, endpoint, data=None):
        """Make HTTP request to MailerLite API"""
        url = f"{self.BASE_URL}/{endpoint}"
        
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        body = json.dumps(data).encode('utf-8') if data else None
        
        try:
            req = urllib.request.Request(url, data=body, headers=headers, method=method)
            
            with urllib.request.urlopen(req, timeout=60) as response:
                response_data = response.read().decode('utf-8')
                if response_data:
                    return {'success': True, 'data': json.loads(response_data), 'status': response.status}
                return {'success': True, 'data': {}, 'status': response.status}
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            try:
                error_json = json.loads(error_body)
            except:
                error_json = {'message': error_body}
            return {'success': False, 'error': error_json, 'status': e.code}
        except urllib.error.URLError as e:
            return {'success': False, 'error': {'message': str(e.reason)}, 'status': 0}
        except Exception as e:
            return {'success': False, 'error': {'message': str(e)}, 'status': 0}
    
    # ==================== SUBSCRIBERS ====================
    
    def create_or_update_subscriber(self, email, name=None, fields=None, groups=None):
        """
        Create or update a subscriber in MailerLite.
        
        Args:
            email: Subscriber email
            name: Optional name
            fields: Optional dict of custom fields
            groups: Optional list of group IDs
        
        Returns:
            dict with subscriber data or error
        """
        data = {'email': email}
        
        if name:
            # Split name into first and last
            parts = name.split(' ', 1)
            data['fields'] = {
                'name': parts[0],
                'last_name': parts[1] if len(parts) > 1 else ''
            }
        
        if fields:
            if 'fields' not in data:
                data['fields'] = {}
            data['fields'].update(fields)
        
        if groups:
            data['groups'] = groups
        
        return self._make_request('POST', 'subscribers', data)
    
    def get_subscriber(self, email_or_id):
        """Get subscriber by email or ID"""
        return self._make_request('GET', f'subscribers/{email_or_id}')
    
    def delete_subscriber(self, subscriber_id):
        """Delete a subscriber"""
        return self._make_request('DELETE', f'subscribers/{subscriber_id}')
    
    # ==================== CAMPAIGNS ====================
    
    def create_campaign(self, name, subject, from_email, from_name, html_content, 
                        language='en', track_opens=True, track_clicks=True):
        """
        Create a new campaign in MailerLite.
        
        Returns:
            dict with campaign data including campaign ID
        """
        data = {
            'name': name,
            'type': 'regular',
            'emails': [{
                'subject': subject,
                'from_name': from_name,
                'from': from_email,
                'content': html_content,
            }],
            'settings': {
                'track_opens': track_opens,
                'track_clicks': track_clicks,
                'use_google_analytics': False,
            }
        }
        
        return self._make_request('POST', 'campaigns', data)
    
    def get_campaign(self, campaign_id):
        """Get campaign details including stats"""
        return self._make_request('GET', f'campaigns/{campaign_id}')
    
    def get_campaign_subscribers_activity(self, campaign_id, activity_type='opened', page=1):
        """
        Get subscribers who performed an action on a campaign.
        
        activity_type: 'opened', 'clicked', 'bounced', 'unsubscribed', 'junk', 'sent'
        """
        return self._make_request('GET', f'campaigns/{campaign_id}/reports/subscriber-activity?filter[type]={activity_type}&page={page}')
    
    def schedule_campaign(self, campaign_id, groups=None, segments=None):
        """
        Schedule/send campaign immediately.
        
        Args:
            campaign_id: MailerLite campaign ID
            groups: List of group IDs to send to (optional)
            segments: List of segment IDs to send to (optional)
        """
        data = {
            'delivery': 'instant'
        }
        
        if groups:
            data['groups'] = groups
        if segments:
            data['segments'] = segments
        
        return self._make_request('POST', f'campaigns/{campaign_id}/schedule', data)
    
    # ==================== TRANSACTIONAL EMAILS ====================
    
    def send_transactional_email(self, to_email, to_name, subject, html_content, 
                                  from_email=None, from_name=None, 
                                  track_opens=True, track_clicks=True,
                                  personalization=None):
        """
        Send a single transactional email via MailerLite.
        
        This is the preferred method for sending campaign emails as it:
        - Handles delivery
        - Tracks opens/clicks automatically
        - Handles bounces
        - Fast and reliable
        
        Args:
            to_email: Recipient email
            to_name: Recipient name
            subject: Email subject
            html_content: HTML body
            from_email: Sender email (uses default if not provided)
            from_name: Sender name
            track_opens: Enable open tracking
            track_clicks: Enable click tracking
            personalization: Dict of variables to replace in content
        
        Returns:
            dict with success status and message ID
        """
        data = {
            'from': {
                'email': from_email or settings.DEFAULT_FROM_EMAIL,
                'name': from_name or 'MakePlus'
            },
            'to': [{
                'email': to_email,
                'name': to_name or to_email.split('@')[0]
            }],
            'subject': subject,
            'html': html_content,
            'settings': {
                'track_opens': track_opens,
                'track_clicks': track_clicks
            }
        }
        
        if personalization:
            data['personalization'] = [{
                'email': to_email,
                'data': personalization
            }]
        
        return self._make_request('POST', 'campaigns/send', data)
    
    # ==================== GROUPS ====================
    
    def get_groups(self):
        """Get all groups"""
        return self._make_request('GET', 'groups')
    
    def create_group(self, name):
        """Create a new group"""
        return self._make_request('POST', 'groups', {'name': name})
    
    def add_subscriber_to_group(self, group_id, subscriber_id):
        """Add subscriber to a group"""
        return self._make_request('POST', f'subscribers/{subscriber_id}/groups/{group_id}')
    
    # ==================== BATCH OPERATIONS ====================
    
    def batch_create_subscribers(self, subscribers):
        """
        Create multiple subscribers at once.
        
        Args:
            subscribers: List of dicts with 'email', 'name', 'fields'
        
        Returns:
            dict with results
        """
        data = {
            'subscribers': subscribers
        }
        return self._make_request('POST', 'subscribers/import', data)
    
    # ==================== STATS ====================
    
    def get_campaign_stats(self, campaign_id):
        """
        Get detailed campaign statistics.
        
        Returns opens, clicks, bounces, unsubscribes, etc.
        """
        result = self.get_campaign(campaign_id)
        
        if result['success'] and 'data' in result:
            campaign_data = result['data'].get('data', result['data'])
            stats = campaign_data.get('stats', {})
            return {
                'success': True,
                'stats': {
                    'sent': stats.get('sent', 0),
                    'delivered': stats.get('delivered', 0),
                    'opens': stats.get('opens_count', 0),
                    'unique_opens': stats.get('unique_opens_count', 0),
                    'open_rate': stats.get('open_rate', {}).get('float', 0),
                    'clicks': stats.get('clicks_count', 0),
                    'unique_clicks': stats.get('unique_clicks_count', 0),
                    'click_rate': stats.get('click_rate', {}).get('float', 0),
                    'unsubscribes': stats.get('unsubscribes_count', 0),
                    'bounces': stats.get('hard_bounces_count', 0) + stats.get('soft_bounces_count', 0),
                    'spam_complaints': stats.get('spam_count', 0),
                }
            }
        return result


# ==================== HELPER FUNCTIONS ====================

def send_email_via_mailerlite(to_email, to_name, subject, html_content, 
                               from_email=None, from_name=None,
                               track_opens=True, track_clicks=True):
    """
    Simple helper function to send a single email via MailerLite.
    
    Returns:
        tuple: (success: bool, error_message: str or None, message_id: str or None)
    """
    try:
        client = MailerLiteClient()
        result = client.send_transactional_email(
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            html_content=html_content,
            from_email=from_email,
            from_name=from_name,
            track_opens=track_opens,
            track_clicks=track_clicks
        )
        
        if result['success']:
            message_id = result.get('data', {}).get('id', result.get('data', {}).get('data', {}).get('id'))
            return True, None, message_id
        else:
            error = result.get('error', {})
            error_msg = error.get('message', str(error))
            return False, error_msg, None
            
    except Exception as e:
        return False, str(e), None


def sync_campaign_stats_from_mailerlite(mailerlite_campaign_id, local_campaign):
    """
    Sync stats from MailerLite campaign to local EmailCampaign model.
    
    Args:
        mailerlite_campaign_id: The MailerLite campaign ID
        local_campaign: The local EmailCampaign instance
    
    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    try:
        client = MailerLiteClient()
        result = client.get_campaign_stats(mailerlite_campaign_id)
        
        if result['success']:
            stats = result['stats']
            local_campaign.total_sent = stats['sent']
            local_campaign.total_delivered = stats['delivered']
            local_campaign.total_opens = stats['opens']
            local_campaign.total_clicks = stats['clicks']
            local_campaign.total_bounces = stats['bounces']
            local_campaign.total_unsubscribes = stats['unsubscribes']
            local_campaign.save()
            return True, None
        else:
            error = result.get('error', {})
            return False, error.get('message', str(error))
            
    except Exception as e:
        return False, str(e)
