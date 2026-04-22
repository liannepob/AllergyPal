from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os

def send_reset_email(to_email, reset_link):
    message = Mail(
        from_email="noreply@allergypal.com",          # what email sends from?
        to_emails=to_email,           # who receives it?
        subject= "AllergyPal: Reset Password",             # what's the subject line?
        html_content=f'<p>Hi AllergyPal user! Click <a href="{reset_link}">here</a> to reset your password. Link expires in 30 minutes.</p>'    )
    
    sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))  # what env variable?
    sg.send(message)