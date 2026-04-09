"""
Brevo (Sendinblue) API v3 Client

Complete implementation for transactional emails, contact management,
campaign management, and statistics tracking.
"""

import json
import urllib.request
import urllib.error
from django.conf import settings


class BrevoClient:
    """Brevo API v3 client for email operations"""
    
    BASE_URL = "https://api.brevo.com/v3"
    
    def __init__(self, api_key=None):
        self.api_key = api_key or getattr(settings, 'BREVO_API_KEY', '')
        if not self.api_key:
            raise ValueError("BREVO_API_KEY not configured in settings")
    
    def _make_request(self, endpoint, method='GET', data=None):
        """Make HTTP request to Brevo API"""
        url = f"{self.BASE_URL}{endpoint}"
        headers = {
            'api-key': self.api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        request_data = json.dumps(data).encode('utf-8') if data else None
        
        try:
            req = urllib.request.Request(
                url,
                data=request_data,
                headers=headers,
                method=method
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = response.read().decode('utf-8')
                return json.loads(response_data) if response_data else {}
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            try:
                error_json = json.loads(error_body)
                error_msg = error_json.get('message', str(error_json))
            except:
                error_msg = error_body
            raise Exception(f'Brevo API error {e.code}: {error_msg}')
        except Exception as e:
            raise Exception(f'Request failed: {str(e)}')
    
    def send_transactional_email(self, to_email, to_name, subject, html_content, 
                                 from_email=None, from_name=None, 
                                 track_opens=True, track_clicks=True):
        """
        Send a single transactional email with tracking
        
        Args:
            to_email: Recipient email address
            to_name: Recipient name
            subject: Email subject
            html_content: HTML body
            from_email: Sender email (optional, uses DEFAULT_FROM_EMAIL)
            from_name: Sender name (optional, defaults to 'MakePlus')
            track_opens: Enable open tracking (default: True)
            track_clicks: Enable click tracking (default: True)
        
        Returns:
            dict: Response with messageId
        """
        from_address = from_email or settings.DEFAULT_FROM_EMAIL
        sender_name = from_name or 'MakePlus'
        
        data = {
            'sender': {
                'name': sender_name,
                'email': from_address
            },
            'to': [{
                'email': to_email,
                'name': to_name
            }],
            'subject': subject,
            'htmlContent': html_content,
            'params': {
                'trackOpens': track_opens,
                'trackClicks': track_clicks
            }
        }
        
        return self._make_request('/smtp/email', method='POST', data=data)
    
    def get_message_stats(self, message_id):
        """
        Get statistics for a specific message (transactional email)
        
        NOTE: Brevo's transactional email stats API doesn't support individual message lookup.
        We need to use the events API instead.
        
        Args:
            message_id: Message ID returned when sending email
        
        Returns:
            dict: Message statistics including opens, clicks, etc.
        """
        # Brevo doesn't have a direct messageId stats endpoint for transactional emails
        # We need to use the events API with messageId filter
        # Extract UUID from message ID if it's in email format
        if message_id.startswith('<') and message_id.endswith('>'):
            message_id = message_id[1:-1]  # Remove < and >
        
        if '@' in message_id:
            message_id = message_id.split('@')[0]  # Get part before @
        
        # Use events API with messageId filter
        return self.get_email_events(message_id=message_id, days=7, limit=1000)
    
    def get_aggregated_report(self, start_date, end_date, days=None, tag=None):
        """
        Get aggregated email statistics report
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            days: Number of days (alternative to start/end dates)
            tag: Filter by tag
        
        Returns:
            dict: Aggregated statistics
        """
        params = {}
        
        if days:
            params['days'] = days
        else:
            params['startDate'] = start_date
            params['endDate'] = end_date
        
        if tag:
            params['tag'] = tag
        
        query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
        endpoint = f'/smtp/statistics/aggregatedReport?{query_string}'
        
        return self._make_request(endpoint)
    
    def get_email_events(self, email=None, event_type=None, days=30, limit=100, offset=0, message_id=None, tags=None):
        """
        Get email events (opens, clicks, etc.)
        
        Args:
            email: Filter by recipient email
            event_type: Filter by event type (delivered, opened, clicks, etc.)
            days: Number of days to look back (default: 30)
            limit: Max results (default: 100)
            offset: Pagination offset (default: 0)
            message_id: Filter by message ID
            tags: Filter by tags
        
        Returns:
            dict: Events data
        """
        params = {
            'limit': limit,
            'offset': offset,
            'days': days
        }
        
        if email:
            params['email'] = email
        if event_type:
            params['event'] = event_type
        if message_id:
            params['messageId'] = message_id
        if tags:
            params['tags'] = tags
        
        query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
        endpoint = f'/smtp/statistics/events?{query_string}'
        
        return self._make_request(endpoint)
    
    def get_events_for_message_ids(self, message_ids, days=30):
        """
        Get events for multiple message IDs
        
        Args:
            message_ids: List of message IDs
            days: Number of days to look back
        
        Returns:
            dict: email -> events mapping
        """
        all_events = {}
        
        # Fetch events for each message ID
        for message_id in message_ids:
            if not message_id:
                continue
            try:
                result = self.get_email_events(message_id=message_id, days=days, limit=1000)
                events = result.get('events', [])
                
                for event in events:
                    email = event.get('email', '').lower()
                    if email not in all_events:
                        all_events[email] = []
                    all_events[email].append(event)
            except Exception as e:
                print(f"Error fetching events for message_id {message_id}: {str(e)}")
                continue
        
        return all_events
    
    def get_campaign_stats(self, campaign_id):
        """
        Get statistics for a specific campaign
        
        Args:
            campaign_id: Campaign ID
        
        Returns:
            dict: Campaign statistics
        """
        return self._make_request(f'/emailCampaigns/{campaign_id}')
    
    def create_contact(self, email, attributes=None, list_ids=None):
        """
        Create or update a contact
        
        Args:
            email: Contact email
            attributes: Dict of contact attributes (name, etc.)
            list_ids: List of list IDs to add contact to
        
        Returns:
            dict: Contact data
        """
        data = {
            'email': email,
            'attributes': attributes or {},
            'listIds': list_ids or [],
            'updateEnabled': True
        }
        
        return self._make_request('/contacts', method='POST', data=data)
    
    def get_contact_lists(self, limit=50, offset=0):
        """
        Get all contact lists
        
        Args:
            limit: Max results (default: 50)
            offset: Pagination offset (default: 0)
        
        Returns:
            dict: Lists data
        """
        endpoint = f'/contacts/lists?limit={limit}&offset={offset}'
        return self._make_request(endpoint)
    
    def get_account_info(self):
        """
        Get account information including sending limits
        
        Returns:
            dict: Account data with plan limits
        """
        return self._make_request('/account')
    
    def get_or_create_default_folder(self):
        """
        Get or create a default folder for campaign contact lists
        
        Returns:
            int: Folder ID
        """
        try:
            # Try to get existing folders
            folders = self._make_request('/contacts/folders')
            
            # Look for a folder named "Campaign Lists"
            for folder in folders.get('folders', []):
                if folder.get('name') == 'Campaign Lists':
                    return folder['id']
            
            # Create the folder if it doesn't exist
            folder_data = {'name': 'Campaign Lists'}
            result = self._make_request('/contacts/folders', method='POST', data=folder_data)
            return result['id']
        except:
            # If folders API fails, return None and we'll create list without folder
            return None
    
    def create_contact_list(self, name, folder_id=None):
        """
        Create a new contact list
        
        Args:
            name: List name
            folder_id: Optional folder ID (will use default if not provided)
        
        Returns:
            dict: List data with 'id'
        """
        # Get default folder if not provided
        if folder_id is None:
            folder_id = self.get_or_create_default_folder()
        
        data = {
            'name': name
        }
        
        # Only add folderId if we have one
        if folder_id:
            data['folderId'] = folder_id
        
        return self._make_request('/contacts/lists', method='POST', data=data)
    
    def add_contacts_to_list(self, list_id, emails):
        """
        Add multiple contacts to a list
        
        Args:
            list_id: List ID
            emails: List of email addresses
        
        Returns:
            dict: Response
        """
        data = {
            'emails': emails
        }
        
        return self._make_request(f'/contacts/lists/{list_id}/contacts/add', method='POST', data=data)
    
    def import_contacts_to_list(self, list_id, contacts):
        """
        Import contacts with attributes to a list
        
        Args:
            list_id: List ID
            contacts: List of dicts with 'email' and optional attributes
        
        Returns:
            dict: Import process ID
        """
        # First, create/update contacts
        for contact in contacts:
            try:
                self.create_contact(
                    email=contact['email'],
                    attributes=contact.get('attributes', {}),
                    list_ids=[list_id]
                )
            except:
                pass  # Contact might already exist
        
        return {'success': True, 'count': len(contacts)}
    
    def create_email_campaign(self, name, subject, sender_name, sender_email, 
                             html_content, recipients_list_ids=None, recipients=None,
                             scheduled_at=None):
        """
        Create an email campaign
        
        Args:
            name: Campaign name
            subject: Email subject
            sender_name: Sender name
            sender_email: Sender email
            html_content: HTML content
            recipients_list_ids: List of contact list IDs (for list-based campaigns)
            recipients: List of recipient dicts with 'email' (for direct recipients)
            scheduled_at: ISO datetime string for scheduling (optional)
        
        Returns:
            dict: Campaign data with 'id'
        """
        data = {
            'name': name,
            'subject': subject,
            'sender': {
                'name': sender_name,
                'email': sender_email
            },
            'htmlContent': html_content,
            'recipients': {}
        }
        
        # Add recipients - either from lists or direct emails
        if recipients_list_ids:
            data['recipients']['listIds'] = recipients_list_ids
        elif recipients:
            # For direct recipients, we need to create a temporary list
            # or use the batch sending approach
            data['recipients']['listIds'] = []
        
        if scheduled_at:
            data['scheduledAt'] = scheduled_at
        
        return self._make_request('/emailCampaigns', method='POST', data=data)
    
    def send_email_campaign(self, campaign_id):
        """
        Send an email campaign immediately
        
        Args:
            campaign_id: Campaign ID
        
        Returns:
            dict: Response
        """
        return self._make_request(f'/emailCampaigns/{campaign_id}/sendNow', method='POST')
    
    def delete_contact_list(self, list_id):
        """
        Delete a contact list
        
        Args:
            list_id: List ID
        
        Returns:
            dict: Response
        """
        return self._make_request(f'/contacts/lists/{list_id}', method='DELETE')
    
    def send_batch_emails(self, emails_data):
        """
        Send multiple emails in batch (using transactional API)
        
        Args:
            emails_data: List of dicts with email data:
                - to_email: Recipient email
                - to_name: Recipient name
                - subject: Email subject
                - html_content: HTML body
                - params: Optional dict of template variables
        
        Returns:
            list: List of results for each email
        """
        results = []
        for email_data in emails_data:
            try:
                result = self.send_transactional_email(
                    to_email=email_data['to_email'],
                    to_name=email_data.get('to_name', ''),
                    subject=email_data['subject'],
                    html_content=email_data['html_content'],
                    from_email=email_data.get('from_email'),
                    from_name=email_data.get('from_name'),
                    track_opens=email_data.get('track_opens', True),
                    track_clicks=email_data.get('track_clicks', True)
                )
                results.append({
                    'email': email_data['to_email'],
                    'success': True,
                    'message_id': result.get('messageId')
                })
            except Exception as e:
                results.append({
                    'email': email_data['to_email'],
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    def test_connection(self):
        """
        Test API connection by fetching account info
        
        Returns:
            bool: True if connection successful
        """
        try:
            self._make_request('/account')
            return True
        except:
            return False


def get_brevo_client():
    """Get configured Brevo client instance"""
    return BrevoClient()
