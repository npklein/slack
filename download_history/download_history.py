import os
import logging
import slack
import ssl as ssl_lib
import certifi
import json
import subprocess
from datetime import datetime, timedelta, time
import requests


def send_message(message, channel, web_client):
    message_block = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": (
                message
            ),
        },
    }

    payload = {
        "channel": channel,
        'username': 'history_downloader',
        "icon_emoji": ":robot_face:",
        "blocks": [
            message_block,
        ]}
    # Post the onboarding message in Slack
    response = web_client.chat_postMessage(**payload)

def start_downloading(web_client: slack.WebClient):
    '''Download all channels chat history. Download up to and including yesterday. Then transfer to the cluster'''
    print('finding the right channel to write messages to')
    
    excluded_channels = set(['lunch','random'])
    
    for channel in web_client.conversations_list()['channels']:
        channel_name = web_client.channels_info(channel=channel['id'])['channel']['name']
        if channel_name == 'download_history':
            channel_message_id = channel['id']
    send_message('Start downloading all history',channel_message_id, web_client)
    try:
        print('start downloading history')

            
        #send_message('Start downloading messages',web_client.conv 'test')
        # get date/time at midnight so only messages from yesterday can be downloaded
        midnight = datetime.combine(datetime.today(), time.min)
        # Get all the channel IDs
        for channel in web_client.conversations_list()['channels']:
            
            # Convert channel ID to channel name
            channel_name = web_client.channels_info(channel=channel['id'])['channel']['name']
            
            # exclude some channels
            
            if channel_name in excluded_channels:
                continue
            
            send_message('Downloading '+channel_name,channel_message_id, web_client)
            # Get the history of the channel (tried to do it using the python API but did not work, so using slack-history-export)
            subprocess_output = subprocess.check_output(['slack-history-export','--token',web_client.token,'--channel',channel_name])
            history = json.loads(subprocess_output.decode('utf-8'))
            
            prev_day = None
            out = None
            for message in history:
                message['isoDate'] = message['isoDate'].split('.')[0]
                message_date = datetime.strptime(message['isoDate'], "%Y-%m-%dT%H:%M:%S")
                message_date_str = message_date.strftime('%Y-%m-%d')
                if(message_date >= midnight):
                    # don't download messages from today
                    continue
                
                # download files from messages
                if 'files' in message:
                    for file_info in message['files']:
                        file_name = "".join([x if x.isalnum() else "_" for x in file_info['title']])+'.'+file_info['filetype']
                        download_link = file_info['url_private_download']
                        channel_dir = 'slack_history/'+channel_name+'/'+message_date_str
                        if not os.path.exists(channel_dir):
                            os.makedirs(channel_dir)
                        print('downloading '+download_link+' to' +channel_dir+'/'+file_name)
                        r = requests.get(download_link, headers={'Authorization': 'Bearer %s' % web_client.token})
                        open( channel_dir+'/'+file_name, 'wb').write(r.content)
                    
                # parse the message and organize by date
                user_info = web_client.users_info(user=message['user'])['user']
                if 'real_name' in user_info:
                    user_name = user_info['real_name']
                elif 'username' in user_info:
                    user_name = user_info['username']
                else:
                    user_name = 'Unknown'
                message_text = message['text']
                if message_text.endswith('has joined the channel') or message_text.endswith('has left the channel'):
                    continue 
                    
                if prev_day != message_date_str:
                    if out:
                        out.close()
                        
                    channel_dir = 'slack_history/'+channel_name+'/'+message_date_str+'/'
                    if not os.path.exists(channel_dir):
                        os.makedirs(channel_dir)
                    out = open(channel_dir+message_date_str+'.txt','w')
                    
                out.write(user_name+'::'+message_date.strftime("%Y-%m-%d-%H:%M:%S")+':: '+message_text+'\n')
                
                prev_day = message_date_str
        send_message('Finished downloading all messages',channel_message_id, web_client)
    except Exception as e:
        send_message('Got an error\n'+str(e),channel_message_id, web_client)
        raise
# ============== Message Events ============= #
# When a user sends a DM, the event type will be 'message'.
# Here we'll link the update_share callback to the 'message' event.
@slack.RTMClient.run_on(event="message")
def message(**payload):
    """Download all messages of current channel when getting a message
    that contains "download".
    Execute after the first message is received, then exit(). Allows for running this only once a day
    """
    web_client = payload["web_client"]
    start_downloading(web_client)

 
    
if __name__ == "__main__":
    ssl_context = ssl_lib.create_default_context(cafile=certifi.where())
    with open('/Users/NPK/UMCG/git_projects/slack/exportPapers/token.txt') as input_file:
        slack_token = input_file.read().strip()
    rtm_client = slack.RTMClient(token=slack_token, ssl=ssl_context)
    rtm_client.start()
    
