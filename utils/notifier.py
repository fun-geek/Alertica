from utils.sms import send_sms
from utils.email import send_email

def send_alert(message, region, methods):
    success = True
    contacts = {
        'sms': ['+91XXXXXXXXXX'],
        'email': ['example@gmail.com']
    }

    if 'sms' in methods:
        for number in contacts['sms']:
            if not send_sms(number, message):
                success = False

    if 'email' in methods:
        for email in contacts['email']:
            if not send_email(email, f"Alert for {region}", message):
                success = False

    # Push notifications can be added here

    return success
