import json
import subprocess
import argparse
import datetime

parser = argparse.ArgumentParser('Get digest of papers channel from last week')
parser.add_argument("token", help="slack token")
args = parser.parse_args()

papers = json.loads(subprocess.check_output(['slack-history-export','--token',args.token,'--channel','papers']).decode('utf-8'))

for message in papers:
    if 'attachments' in message:
        datetime_now = datetime.date.today()
        week_ago = datetime_now - datetime.timedelta(days=7)
        if week_ago.isoformat() < message['isoDate']:
            attachments = message['attachments']
            for attachment in attachments:
                print(attachment['title'], attachment['title_link'])
