from threading import Thread
from flask import current_app, flash
from flask_mail import Message
from app import mail

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body, 
            attachments=None, sync=False):
    emails_sent_to = []
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    if attachments:
        for attachment in attachments:
            msg.attach(*attachment)
    Thread(target=send_async_email, 
            args=(current_app._get_current_object(), msg)).start()
    print(recipients)
    truefalse = "not " if current_app.config.get('MAIL_SUPPRESS_SEND') else ''
    current_app.logger.info(f'Email {truefalse}sent to: ' + ", ".join(msg.recipients) + '\n')
    flash(f'Email notifications <b>{truefalse}</b>sent to: <b>' + ", ".join(msg.recipients) + '</b>', 'info')
