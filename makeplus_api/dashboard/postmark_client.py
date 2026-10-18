"""
Postmark API client (https://postmarkapp.com).

Thin wrapper around Postmark's HTTP API using the server's "Server API
Token" (Servers -> a server -> API Tokens -> Server API token). That
token identifies both the sending account and which Message Stream
("outbound" by default) the email is attributed to.
"""

import base64
import requests
from django.conf import settings


class PostmarkClient:
    """Postmark API client for sending email and checking server status."""

    BASE_URL = "https://api.postmarkapp.com"

    def __init__(self, server_token=None):
        self.server_token = server_token or getattr(settings, 'POSTMARK_SERVER_TOKEN', '')
        if not self.server_token:
            raise ValueError("POSTMARK_SERVER_TOKEN not configured in settings")

    def _headers(self):
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Postmark-Server-Token': self.server_token,
        }

    def _request(self, method, endpoint, data=None, params=None):
        url = f"{self.BASE_URL}{endpoint}"
        response = requests.request(
            method, url, headers=self._headers(),
            json=data, params=params, timeout=30,
        )
        try:
            payload = response.json()
        except ValueError:
            payload = {}

        if not response.ok:
            message = payload.get('Message') or response.text or f'HTTP {response.status_code}'
            raise Exception(f'Postmark API error {response.status_code}: {message}')

        return payload

    def send_email(self, to_email, to_name, subject, html_content,
                    from_email=None, from_name=None,
                    track_opens=True, track_clicks=True,
                    attachments=None, tag=None, message_stream=None):
        """
        Send a single email through Postmark.

        Args:
            attachments: optional list of {'name': str, 'content': base64 str, 'mimetype': str,
                'content_id': optional str}. When content_id is set, the attachment is inlined
                (not shown as a downloadable file) and can be referenced in html_content as
                <img src="cid:{content_id}">.
            tag: optional short string used by Postmark to group/filter messages (max 1)

        Returns:
            dict: Postmark's response, including 'MessageID'
        """
        from_address = from_email or settings.DEFAULT_FROM_EMAIL
        sender_name = from_name or 'MakePlus'
        to_display_name = to_name or ''

        data = {
            'From': f'{sender_name} <{from_address}>' if sender_name else from_address,
            'To': f'{to_display_name} <{to_email}>' if to_display_name else to_email,
            'Subject': subject,
            'HtmlBody': html_content,
            'TrackOpens': bool(track_opens),
            'TrackLinks': 'HtmlAndText' if track_clicks else 'None',
            'MessageStream': message_stream or getattr(settings, 'POSTMARK_MESSAGE_STREAM', 'outbound'),
        }
        if tag:
            data['Tag'] = tag[:1000]
        if attachments:
            postmark_attachments = []
            for att in attachments:
                entry = {
                    'Name': att['name'],
                    'Content': att['content'],
                    'ContentType': att.get('mimetype', 'application/octet-stream'),
                }
                if att.get('content_id'):
                    entry['ContentID'] = f"cid:{att['content_id']}"
                postmark_attachments.append(entry)
            data['Attachments'] = postmark_attachments

        return self._request('POST', '/email', data=data)

    def get_server_info(self):
        """Fetch this server's info (name, color, tracking defaults, ...)."""
        return self._request('GET', '/server')

    def get_message_details(self, message_id):
        """Look up a previously-sent message by its MessageID."""
        return self._request('GET', f'/messages/outbound/{message_id}/details')

    def search_outbound_messages(self, recipient=None, count=10):
        """List/search recent outbound messages on this server."""
        params = {'count': count, 'offset': 0}
        if recipient:
            params['recipient'] = recipient
        return self._request('GET', '/messages/outbound', params=params)

    def test_connection(self):
        """Return True if the configured token authenticates successfully."""
        try:
            self.get_server_info()
            return True
        except Exception:
            return False


def get_postmark_client():
    """Get a configured Postmark client instance."""
    return PostmarkClient()


def encode_attachment_content(raw_bytes):
    """Base64-encode raw attachment bytes the way Postmark's API expects."""
    return base64.b64encode(raw_bytes).decode('ascii')
