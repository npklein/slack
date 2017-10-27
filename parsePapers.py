import json
import subprocess
import argparse
import datetime
import smtplib
from email.mime.text import MIMEText
import sys

parser = argparse.ArgumentParser('Get digest of papers channel from last week and, optionally, email it (using gmail for now)\n')
parser.add_argument("token", help="slack token")
parser.add_argument("--receiver_emails", help="comma separated list of emails to send digest to", required=False)
parser.add_argument("--sender_user", help="gmail username for sender", required="--emails" in sys.argv)
parser.add_argument("--sender_password", help="gmail password for sender", required="--emails" in sys.argv)
args = parser.parse_args()



def send_email(user, pwd, recipient, subject, body):
    import smtplib

    gmail_user = user
    gmail_pwd = pwd
    FROM = user
    TO = recipient if type(recipient) is list else [recipient]
    SUBJECT = subject
    TEXT = body

    # Prepare actual message
    message = """From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_pwd)
        server.sendmail(FROM, TO, message)
        server.close()
        print 'successfully sent the mail'
    except:
        print "failed to send mail"


papers = json.loads(subprocess.check_output(['slack-history-export','--token',args.token,'--channel','papers']).decode('utf-8'))
subject = 'Weekly digest Papers channel'

msg = 'Weekly Slack Papers channel links\n'

for message in papers:
    if 'attachments' in message:
        datetime_now = datetime.date.today()
        week_ago = datetime_now - datetime.timedelta(days=7)
        if week_ago.isoformat() < message['isoDate']:
            attachments = message['attachments']
            for attachment in attachments:
                print(attachment['title'], attachment['title_link'])
                if args.receiver_emails:
                    msg += '\n'+attachment['title']+'\t'+attachment['title_link']

if args.receiver_emails:
    for receiver_email in args.receiver_emails.split(','):
        send_email(args.sender_user, args.sender_password, receiver_email, subject, msg)
