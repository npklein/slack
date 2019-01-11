import json
import subprocess
import argparse
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
import os
import re

parser = argparse.ArgumentParser('Get digest of papers channel from last week and, optionally, email it (using gmail for now)\n')
parser.add_argument("token", help="slack token")
parser.add_argument("--receiver_emails", help="comma separated list of emails to send digest to", required=False)
parser.add_argument("--sender_user", help="gmail username for sender", required="--emails" in sys.argv)
parser.add_argument("--sender_password", help="gmail password for sender", required="--emails" in sys.argv)
parser.add_argument("--testrun", help="Do a testrun, do not actually send email",action='store_true', required=False)
args = parser.parse_args()


def html_table(content_list, from_date, to_date):
    table  = '<html>'
    table += '  <head></head>\n'
    table += '  <body>'
    table += '    Dear all, <br><br>'
    table += '    We share interesting papers on our Slack channel, and I have been asked to forward these to the JC mailing list once in a while. <br>'
    table += '    Hereby the papers from '+from_date+' until '+ to_date+': <br><br><br>\n'
    table += '    <table>\n'
    for sublist in content_list:
        table += '      <tr><td>'
        table += '        </td><td>'.join(sublist)
        table += '      </td></tr>\n'
    table += '    </table>\n'
    table += '    <br>'
    table += '    <br>'
    table += '    If you don\'t think this should be sent occasionally, let me know at niekdeklein@gmail.com.<br><br>'
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
    #html = html.encode('utf-8')
    part2 = MIMEText(html, 'html')
    msg.attach(part2)

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.login(user, pwd)
    server.sendmail(user, TO, msg.as_string())
    server.close()
    return(msg['To'])

if __name__ == "__main__":
    logfile = os.path.dirname(os.path.realpath(__file__))+'/sendPapers.log'
    print('Read '+logfile+' to get info on previous session')
    today = datetime.date.today()
    send_papers_from_this_date = today - datetime.timedelta(days=7)
    if not os.path.exists(logfile):
        print(logfile,'does not exist, only send papers from one week ago (since',send_papers_from_this_date,')')
    else:
        with open(logfile) as prev_logfile:
            logdata = prev_logfile.read()
            date_sent = logdata.split('Last sent at: ')[1].split('\n')[0]
            if 'email sent to' in logdata:
                print('Last time email was sent was at',date_sent,', sending all papers since that time')
                print(date_sent)
                send_papers_from_this_date = datetime.datetime.strptime(date_sent.split('.')[0], '%Y-%m-%d %H:%M:%S')
            else:
                print('Last time it was run the e-mail did not get sent. Trying to send all papers of previous week (since',send_papers_from_this_date,')')
                send_papers_from_this_date = datetime.datetime.strptime(date_sent.split('.')[0], '%Y-%m-%d %H:%M:%S')

    print('Sending papers from',send_papers_from_this_date, 'until', today)

    papers = json.loads(subprocess.check_output(['slack-history-export','--token',args.token,'--channel','papers']).decode('utf-8'))
    subject = 'Occasional papers list: '+send_papers_from_this_date.strftime('%Y-%b-%d')+' until '+today.strftime('%Y-%b-%d')
    content_list = []
    for message in papers:
        ### uncomment below if you want it per week or per day
        # per week:
        # send_papers_from_this_data = datetime_now - datetime.timedelta(days=7)
        # per day:
        # send_papers_from_this_data = datetime_now.isoformat() < message['isoDate']:
        if not send_papers_from_this_date.isoformat() < message['isoDate']:
            continue
        if 'attachments' in message:
            attachments = message['attachments']
            for attachment in attachments:
                if 'title' not in attachment:
                    continue
                content_list.append([attachment['title'],attachment['title_link']])
        elif 'http' in message['text']:
            title = message['text'].split('<')[0].strip()
            link = message['text'].split('<')[1].split('>')[0]
            content_list.append([title,link])

    if args.receiver_emails and content_list:
        html_msg = html_table(content_list, send_papers_from_this_date.strftime('%Y-%b-%d'), today.strftime('%Y-%b-%d'))
        if not args.testrun:
            send_email(args.sender_user, args.sender_password,args.receiver_emails.split(','), subject, html_msg)
        else:
            print('TESTRUN, NOT SENDING EMAIL')
            print('emails to send to:',args.receiver_emails)
            print('subject:',subject)

        print('HTML msg:\n\n')
        print(html_msg)
        if not args.testrun:
            print('\n\nEmail sent to:', args.receiver_emails)

    if args.testrun:
        print('TESTRUN, not writing to logfile so that last sent date does not get overwritten')
    else:
        print('write to '+logfile)
        with open(logfile,'w') as out:
            out.write('Last sent at: '+str(datetime.datetime.now()))
            out.write('\nemail sent to: '+args.receiver_emails )
