import requests

from app.core.config import RESEND_API_KEY, RESEND_FROM_EMAIL

RESEND_URL = "https://api.resend.com/emails"   # http request is made to this to tell resend to send the mail to the user mail id 


def _send_email(to_email: str, subject: str, text_body: str, html_body: str = None) -> None:
    payload = {
        "from": RESEND_FROM_EMAIL,
        "to": [to_email],   #here to_email is a list beacus "to" is treated as a list recipient 
        "subject": subject,
        "text": text_body,
    }
    if html_body:    #only if html body exists , do this 
        payload["html"] = html_body
    # Make the HTTP POST request
    response = requests.post(
        RESEND_URL,
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=10,  #If Resend doesn't respond within about 10 seconds, the request will time out and an exception will occur.
    )
    response.raise_for_status()   #This checks the HTTP response.


def send_reset_email(to_email: str, username: str, reset_link: str) -> None:
    subject = "Reset your password"

    text_body = (
        f"Hi {username},\n\n"
        f"We got a request to reset the password for your Parse account.\n"
        f"Reset your password here: {reset_link}\n\n"
        f"This link expires in 15 minutes and can be used once.\n\n"
        f"Didn't ask for this? You can ignore this email.\n\n"
        f"-- Parse Support Team"
    )

    html_body = f"""
    <p>Hi {username},</p>
    <p>We got a request to reset the password for your Parse account.</p>
    <p><a href="{reset_link}">Click here to reset the password.</a></p>
    <p>This link expires in 15 minutes and can be used once.</p>
    <p>Didn't ask for this? You can ignore this email.</p>
    <p>-- Parse Support Team</p>
    """

    _send_email(to_email, subject, text_body, html_body)


def send_password_changed_email(to_email: str, username: str) -> None:
    subject = "Your password was changed"

    text_body = (
        f"Hi {username},\n\n"
        f"The password for your Parse account was just changed.\n\n"
        f"If this was you, nothing else to do.\n\n"
        f"If it wasn't, contact us right away - someone else may have access to your account.\n\n"
        f"-- Parse Support Team"
    )

    _send_email(to_email, subject, text_body)