"""Check the disposable SMTP receiver with certificate verification."""

import smtplib
import ssl
import sys

try:
    context = ssl.create_default_context(cafile="/run/smtp/ca.pem")
    with smtplib.SMTP("smtp-capture", 1025, timeout=2) as client:
        client.ehlo()
        client.starttls(context=context)
except (OSError, smtplib.SMTPException):
    sys.exit(1)
