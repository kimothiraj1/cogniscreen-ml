"""
Twilio SMS Alert
Triggered when stage == 3 (high concern).
Sends to caregiver phone stored in user profile.
"""

import os
from twilio.rest import Client


def send_caregiver_alert(caregiver_phone: str, user_id: str, explanation: str):
    """
    Sends SMS alert to caregiver.
    Raises exception if Twilio is not configured — caller handles it.
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token  = os.getenv("TWILIO_AUTH_TOKEN")
    from_phone  = os.getenv("TWILIO_FROM_PHONE")

    if not all([account_sid, auth_token, from_phone]):
        raise ValueError("Twilio credentials not configured in .env")

    client = Client(account_sid, auth_token)

    message_body = (
        f"CogniScreen Alert: A high concern pattern has been detected "
        f"in today's session. {explanation} "
        f"Please check in with your family member soon."
    )

    client.messages.create(
        body=message_body,
        from_=from_phone,
        to=caregiver_phone
    )
