import json
import subprocess
import argparse
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
import os

parser = argparse.ArgumentParser('Get digest of papers channel from last week and, optionally, email it (using gmail for now)\n')
parser.add_argument("token", help="slack token")
parser.add_argument("--receiver_emails", help="comma separated list of emails to send digest to", required=False)
parser.add_argument("--sender_user", help="gmail username for sender", required="--emails" in sys.argv)
parser.add_argument("--sender_password", help="gmail password for sender", required="--emails" in sys.argv)
args = parser.parse_args()


def html_table(content_list):
    table  = '<html>'
    table += '  <head></head>\n'
    table += '  <body>'
    table += '    Dear all, <br><br>'
    table += '    We share interesting papers on our Slack channel, and I have been asked to share this with the JC list once a week. Hereby this weeks papers: <br><br><br>\n'
    table += '    <table>\n'
    for sublist in content_list:
        table += '      <tr><td>'
        table += '        </td><td>'.join(sublist)
        table += '      </td></tr>\n'
    table += '    </table>\n'
    table += '    <br>'
    table += '    <br>'
    table += '    If you don\'t think this should be sent weekly, let me know.<br><br>'
    table += '    Kind regards,<br>'
    table += '    Niek'
    table += '  </body>\n'
    table += '</html>'
    return(table)

def send_email(user, pwd, recipient, subject, html):
    TO = recipient if type(recipient) is list else [recipient]
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = user
    msg['To'] = ', '.join(TO)

    part2 = MIMEText(html, 'html')
    msg.attach(part2)

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.login(user, pwd)
    server.sendmail(user, TO, msg.as_string())
    server.close()
    with open(os.path.dirname(os.path.realpath(__file__))+'/sendPapers.log','a') as out:
        out.write('\nemail sent to: \n'+msg['To'] )

if __name__ == "__main__":
    logfile = os.path.dirname(os.path.realpath(__file__))+'/sendPapers.log'
    print('write to '+logfile)
    with open(logfile,'w') as out:
        out.write('Trying to send at: '+str(datetime.datetime.now()))

    papers = json.loads(subprocess.check_output(['slack-history-export','--token',args.token,'--channel','papers']).decode('utf-8'))
    subject = 'Weekly papers list'
    content_list = []
    for message in papers:
        if 'attachments' in message:
            datetime_now = datetime.date.today()
            week_ago = datetime_now - datetime.timedelta(days=7)
            if week_ago.isoformat() < message['isoDate']:
                attachments = message['attachments']
                for attachment in attachments:
                    #print(attachment['title'], attachment['title_link'])
                    if args.receiver_emails:
                        content_list.append([attachment['title'],attachment['title_link']])

    if args.receiver_emails and content_list:
        html_msg = html_table(content_list)
        send_email(args.sender_user, args.sender_password,args.receiver_emails.split(','), subject, html_msg)
