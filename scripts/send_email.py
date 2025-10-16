#!/usr/bin/env python3
import argparse
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

def send_email(smtp_user, smtp_pass, smtp_host, smtp_port, to_email, subject, body, files):
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    for path in files:
        with open(path, 'rb') as f:
            part = MIMEApplication(f.read(), Name=os.path.basename(path))
        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(path)}"'
        msg.attach(part)
    with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)

def main():
    parser = argparse.ArgumentParser(description='Send email with attachments')
    parser.add_argument('--subject', required=True, help='Email subject')
    parser.add_argument('--to', required=True, help='Recipient email address')
    parser.add_argument('--files', nargs='+', required=True, help='Files to attach')
    args = parser.parse_args()
    smtp_user = os.environ.get('SMTP_USER')
    smtp_pass = os.environ.get('SMTP_PASS')
    smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', '465'))
    if not smtp_user or not smtp_pass:
        raise RuntimeError('SMTP_USER and SMTP_PASS environment variables must be set')
    send_email(smtp_user, smtp_pass, smtp_host, smtp_port, args.to, args.subject, 'Please see attached files.', args.files)

if __name__ == '__main__':
    main()
