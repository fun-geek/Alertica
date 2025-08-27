import sendgrid
from sendgrid.helpers.mail import Mail
from config import SENDGRID_API_KEY, EMAIL_FROM

def send_email(to_email, subject, content):
    try:
        sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
        mail = Mail(
            from_email=EMAIL_FROM,
            to_emails=to_email,
            subject=subject,
            plain_text_content=content
        )
        response = sg.send(mail)
        return response.status_code == 202
    except Exception as e:
        print(f"Email Error: {e}")
        return False
