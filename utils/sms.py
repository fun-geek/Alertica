from twilio.rest import Client
from config import TWILIO_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE

def send_sms(to_number, message):
    try:
        client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=message,
            from_=TWILIO_PHONE,
            to=to_number
        )
        return True
    except Exception as e:
        print(f"SMS Error: {e}")
        return False
