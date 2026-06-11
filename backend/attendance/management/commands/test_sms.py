from django.core.management.base import BaseCommand
from django.conf import settings
from attendance.utils import send_sms
import os

class Command(BaseCommand):
    help = 'Test SMS configuration'

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("SMS CONFIGURATION TEST (Django Settings)")
        self.stdout.write("=" * 60)
        
        # Check using os.getenv (what utils.py uses)
        self.stdout.write("\nChecking environment variables (os.getenv):")
        sid = os.getenv("TWILIO_ACCOUNT_SID")
        token = os.getenv("TWILIO_AUTH_TOKEN")
        phone = os.getenv("TWILIO_PHONE_NUMBER")
        
        self.stdout.write(f"TWILIO_ACCOUNT_SID: {sid}")
        self.stdout.write(f"TWILIO_AUTH_TOKEN: {'*' * 20 if token else 'NOT SET'}")
        self.stdout.write(f"TWILIO_PHONE_NUMBER: {phone}")
        
        # Try sending a test SMS
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("SENDING TEST SMS")
        self.stdout.write("=" * 60)
        
        test_number = "+919964534677"
        test_message = "Test SMS from Django attendance system"
        
        self.stdout.write(f"\nAttempting to send to: {test_number}")
        result = send_sms(test_number, test_message)
        
        if result:
            self.stdout.write(self.style.SUCCESS(f"✓ SMS sent! SID: {result}"))
        else:
            self.stdout.write(self.style.ERROR("✗ SMS failed"))
