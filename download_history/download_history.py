import slack
import ssl as ssl_lib
import certifi
import json
import subprocess
from message import Message
import os
import datetime
import argparse
from werkzeug.datastructures import is_immutable

parser = argparse.ArgumentParser(description='Download all available slack messages up until last midnight.')
parser.add_argument('token', help='Slack Token. You can generate it from here https://api.slack.com/custom-integrations/legacy-tokens')
parser.add_argument('outdir', help='Direcotry to write slack message files to')
parser.add_argument('--exclude_channels', help='Comma separated list of channels to exclude')

args = parser.parse_args()

today = date.today()
print("Today's date:", today)

if args.exclude_channels:
    print('Downloading chat history of channels, excluding '+ args.exclude_channels)
else:
    print('Downloading chat history of all channels')


print('Send a message in any slack channel or direct message to start downloading....')

class Downloader():
    def __init__(self, web_client):
        self.web_client = web_client

    def start_downloading_messages(self, outdir):
        '''Download all channels chat history. Download up to and including yesterday. Then transfer to the cluster'''
        print('start downloading history')

        # Get all the channel IDs
        for channel in self.web_client.conversations_list(types='public_channel,private_channel,mpim')['channels']:
            # Convert channel ID to channel name

            # exclude some channels

            # Get the history of the channel (tried to do it using the python API but did not work, so using slack-history-export)
            if channel['is_im']:
                search_type = 'username'
                name = None
                for user in self.web_client.users_list()['members']:
                    if user['id'] == channel['user']:
                        name = user['name']
                        break
                if not name:
                    raise RuntimeError('User ID '+channel['id']+' not found')
            elif channel['is_channel']:
                search_type = 'channel'
                name = channel['name']

            elif channel['is_group']:
                search_type = 'group'
                name = channel['name']

            outdir = args.outdir+'/'+name+'/'
            print('downloading messages from '+name+'. Might take a bit.')

            if args.exclude_channels and name in args.exclude_channels.split(','):
                continue
            
            slack_command = ['slack-history-export','--token',
                                          self.web_client.token, '--'+search_type, name]
            subprocess_output = subprocess.check_output(slack_command)
            history = json.loads(subprocess_output.decode('utf-8'))
            prev_out = None
            out = None
            slack_message = None
            for message_data in history:
                # this is in the for loop instead of out because only want to make it if there is at least 1
                # output file to be written
                if not os.path.exists(outdir):
                    os.makedirs(outdir)
            
                slack_message = Message(message_data, name, self.web_client)
                outfile = name + slack_message.date_str+'.txt'
                if(slack_message.is_today()):
                    # don't download messages from today
                    continue
                
                # download files from messages
                if slack_message.has_file:
                    for file_name, content in slack_message.download_files():
                        files_dir = args.outdir+'/'+name+'/'+slack_message.date_str
                        if not os.path.exists(files_dir):
                            os.makedirs(files_dir)
                        if os.path.exists(files_dir+'/'+file_name):
                            continue
                        open( files_dir+'/'+file_name, 'wb').write(content)
                outfile = outdir+'/'+ slack_message.date_str+'.txt'

                # because we have multiple messages from different dates, check when the messages are from a different date, then write to different file
                if outfile != prev_out:
                    # if running for first time and file already exists, skip
                    if os.path.exists(outfile):
                        continue
                    if out:
                        print('written to '+prev_out)
                        out.close()
                    out = open(outfile,'w')
                    
                text = slack_message.parse_text()
                if text:
                    out.write(text)
                prev_out = outfile

# ============== Message Events ============= #
# When a user sends a DM, the event type will be 'slack_message'.
# Here we'll link the update_share callback to the 'slack_message' event.    

@slack.RTMClient.run_on(event="message")
def react_to_message(**payload):
    """Download all messages of current channel when getting any message (using this as trigger as I haven't figured out how to let it run without trigger)
    Execute after the first message is received, then exit(). Allows for running this only once a day
    """
    web_client = payload["web_client"]

    downloader = Downloader(web_client)
    downloader.start_downloading_messages(args.outdir)
    exit()
 
    
if __name__ == "__main__":
    ssl_context = ssl_lib.create_default_context(cafile=certifi.where())
    slack_token = args.token
    rtm_client = slack.RTMClient(token=slack_token, ssl=ssl_context)
    rtm_client.start()
    
