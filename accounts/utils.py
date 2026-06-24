from django.core.mail import send_mail
from django.conf import settings


# Send email notification to user
def send_user_notification(subject, message, user_email):
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )
        return True

    except Exception as e:
        print(f"Error sending email to {user_email}: {e}")
        return False