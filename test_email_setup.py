"""
Quick Email Setup Test Script
Run this after configuring your .env file to test email sending.
"""

import os
import sys
import django

# Add the project directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'makeplus_api'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'makeplus_api.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings


def test_email_configuration():
    """Test if email is properly configured"""
    print("=" * 60)
    print("📧 EMAIL CONFIGURATION TEST")
    print("=" * 60)
    
    # Check settings
    print("\n✅ Current Email Settings:")
    print(f"   Backend: {settings.EMAIL_BACKEND}")
    print(f"   Host: {settings.EMAIL_HOST}")
    print(f"   Port: {settings.EMAIL_PORT}")
    print(f"   Use TLS: {settings.EMAIL_USE_TLS}")
    print(f"   From Email: {settings.DEFAULT_FROM_EMAIL}")
    print(f"   Site URL: {settings.SITE_URL}")
    
    # Check if credentials are set
    if not settings.EMAIL_HOST_USER:
        print("\n❌ ERROR: EMAIL_HOST_USER is not set in .env file")
        return False
    
    if not settings.EMAIL_HOST_PASSWORD:
        print("\n❌ ERROR: EMAIL_HOST_PASSWORD is not set in .env file")
        return False
    
    print(f"   Username: {settings.EMAIL_HOST_USER}")
    print(f"   Password: {'*' * 10} (hidden)")
    
    # Ask for test recipient
    print("\n" + "=" * 60)
    test_email = input("Enter email address to send test email to: ").strip()
    
    if not test_email or '@' not in test_email:
        print("❌ Invalid email address")
        return False
    
    # Try sending test email
    print(f"\n📤 Sending test email to {test_email}...")
    
    try:
        result = send_mail(
            subject='✅ MakePlus Email Setup Test',
            message='If you receive this email, your email configuration is working correctly!',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_email],
            fail_silently=False,
            html_message="""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2 style="color: #28a745;">✅ Email Setup Successful!</h2>
                    <p>Congratulations! Your MakePlus email campaign system is now configured and working.</p>
                    
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3>What's Working:</h3>
                        <ul>
                            <li>✅ SMTP Configuration</li>
                            <li>✅ Email Delivery</li>
                            <li>✅ HTML Email Support</li>
                        </ul>
                    </div>
                    
                    <h3>Next Steps:</h3>
                    <ol>
                        <li>Create your first email campaign in the admin panel</li>
                        <li>Add recipients to your campaign</li>
                        <li>Send your campaign and track opens/clicks</li>
                        <li>View detailed statistics at /dashboard/campaigns/</li>
                    </ol>
                    
                    <p style="color: #666; font-size: 12px; margin-top: 30px;">
                        This is a test email from MakePlus Campaign System<br>
                        Sent on: ${new Date().toLocaleString()}
                    </p>
                </body>
            </html>
            """
        )
        
        if result == 1:
            print("\n" + "=" * 60)
            print("✅ SUCCESS! Email sent successfully!")
            print("=" * 60)
            print(f"\n📬 Check your inbox at: {test_email}")
            print("\n💡 Tips:")
            print("   • Check spam folder if you don't see it")
            print("   • It may take 1-2 minutes to arrive")
            print("   • Gmail users: Check 'All Mail' folder")
            print("\n🚀 Your email system is ready to send campaigns!")
            return True
        else:
            print("\n❌ Email sending failed (no error thrown)")
            return False
            
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ ERROR SENDING EMAIL")
        print("=" * 60)
        print(f"\nError Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        
        # Provide specific help based on error
        if "Authentication" in str(e):
            print("\n🔧 Fix: Check your email username and password")
            print("   Gmail: Use App Password (not regular password)")
            print("   Brevo/SendGrid: Use SMTP key from dashboard")
            
        elif "Connection" in str(e):
            print("\n🔧 Fix: Check your EMAIL_HOST and EMAIL_PORT")
            print("   Gmail: smtp.gmail.com:587")
            print("   Brevo: smtp-relay.brevo.com:587")
            print("   SendGrid: smtp.sendgrid.net:587")
            
        elif "Sender" in str(e) or "refused" in str(e).lower():
            print("\n🔧 Fix: Check your DEFAULT_FROM_EMAIL")
            print("   Must match your verified sender email")
            
        return False


def test_campaign_system():
    """Test creating a campaign and recipient"""
    print("\n" + "=" * 60)
    print("🧪 TESTING CAMPAIGN SYSTEM")
    print("=" * 60)
    
    try:
        from dashboard.models_email import EmailCampaign, EmailRecipient
        
        # Create test campaign
        campaign = EmailCampaign.objects.create(
            name="Test Campaign - Email Setup",
            subject="Test Email Subject",
            body_html="<h1>Test</h1><p>This is a test campaign.</p>",
            from_email=settings.DEFAULT_FROM_EMAIL,
            track_opens=True,
            track_clicks=True,
            status='draft'
        )
        
        print(f"\n✅ Campaign created: #{campaign.id} - {campaign.name}")
        
        # Ask for recipient
        recipient_email = input("\nEnter email to add as test recipient (or press Enter to skip): ").strip()
        
        if recipient_email and '@' in recipient_email:
            recipient = EmailRecipient.objects.create(
                campaign=campaign,
                email=recipient_email,
                name="Test Recipient"
            )
            print(f"✅ Recipient added: {recipient.email}")
            print(f"   Tracking token: {recipient.tracking_token}")
            
            # Ask if they want to send
            send_now = input("\nSend test campaign to this recipient now? (yes/no): ").strip().lower()
            
            if send_now in ['yes', 'y']:
                from dashboard.utils_campaign import send_campaign_email
                
                print("\n📤 Sending campaign email...")
                send_campaign_email(recipient)
                
                recipient.refresh_from_db()
                print(f"\n✅ Email sent!")
                print(f"   Status: {recipient.status}")
                print(f"   Sent at: {recipient.sent_at}")
                print(f"\n📊 Track opens at: {settings.SITE_URL}/track/email/open/{recipient.tracking_token}/")
                
        print("\n✅ Campaign system is working!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing campaign system: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🚀 MakePlus Email Setup Test\n")
    
    # Test basic email configuration
    email_ok = test_email_configuration()
    
    if email_ok:
        # Ask if they want to test campaign system
        print("\n" + "=" * 60)
        test_campaigns = input("\nTest campaign system too? (yes/no): ").strip().lower()
        
        if test_campaigns in ['yes', 'y']:
            test_campaign_system()
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    
    if email_ok:
        print("\n✅ Your email system is configured and working!")
        print("\n📝 Next steps:")
        print("   1. Go to admin panel: http://127.0.0.1:8000/admin/")
        print("   2. Create an email campaign")
        print("   3. Add recipients")
        print("   4. Send your first real campaign!")
        print("   5. View stats: http://127.0.0.1:8000/dashboard/campaigns/")
    else:
        print("\n❌ Email configuration needs attention")
        print("\n📖 See EMAIL_SETUP_GUIDE.md for detailed setup instructions")
    
    print()
