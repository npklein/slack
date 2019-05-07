import json
import subprocess
import argparse
import datetime
import smtplib
import sys
import os
import re

parser = argparse.ArgumentParser('Download messages from all channels and private messages that you have access to')
parser.add_argument("token", help="slack token")
args = parser.parse_args()


if __name__ == "__main__":
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

        print('write to '+logfile)
        with open(logfile,'w') as out:
            out.write('Last sent at: '+str(datetime.datetime.now()))
            out.write('\nemail sent to: '+args.receiver_emails )
