from celery import shared_task
from django.core.mail import EmailMultiAlternatives


@shared_task(autoretry_for=(OSError,), retry_backoff=True, max_retries=3)
def enviar_email(subject, body, from_email, recipients, alternatives, headers):
    """Transport already-rendered mail outside the HTTP request (RNF06)."""
    message = EmailMultiAlternatives(subject, body, from_email, recipients, headers=headers)
    for content, mimetype in alternatives:
        message.attach_alternative(content, mimetype)
    message.send()
