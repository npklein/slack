from datetime import datetime, time
import os
import requests

class Message():
    '''Save json data of message'''
    def __init__(self, message_json, channel_name, web_client):
        self.isoData = message_json['isoDate'].split('.')[0]
        self.datetime = datetime.strptime(self.isoData, "%Y-%m-%dT%H:%M:%S")
        self.date_str = self.datetime.strftime('%Y-%m-%d')
        self.has_file = False
        self.channel_name = channel_name
        if 'files' in message_json:
            self.has_file = True
            self.files = message_json['files']
        
        self.message_text = message_json['text']        
        self.web_client = web_client
        
        if 'user' in message_json:
            user_info = web_client.users_info(user=message_json['user'])['user']
        else:
            self.user_name = 'Unknown'
            return
            
        if 'real_name' in user_info:
            self.user_name = user_info['real_name']
        elif 'username' in user_info:
            self.user_name = user_info['username']
        else:
            self.user_name = 'Unknown'

    
    def is_today(self):
        '''Return True if message is from today, else False'''
        # get date/time at midnight so only messages from yesterday can be downloaded
        midnight = datetime.combine(datetime.today(), time.min)
        return(self.datetime >= midnight)
    
    def download_files(self):
        '''If the message contains a file, download it'''
        for file_info in self.files:
            if 'title' in file_info:
                file_name = "".join([x if x.isalnum() else "_" for x in file_info['title']])
            else:
                file_name = self.date_str+'_noTitle'
            if 'filetype' in file_info:
                extension = file_info['filetype']
            else:
                extension = 'uunknown'
            file_name.rstrip('_'+extension)
            file_name = file_name + '.' + extension
            if not 'url_private_download' in file_info:
                continue
            download_link = file_info['url_private_download']
            r = requests.get(download_link, headers={'Authorization': 'Bearer %s' % self.web_client.token})
            
            yield (file_name, r.content)
            
    
    def parse_text(self):
        '''Parse the text message and save the info'''
        # parse the message and organize by date
        
        if self.message_text.endswith('has joined the channel') or self.message_text.endswith('has left the channel'):
            return None
            

        return(self.user_name+'::'+self.datetime.strftime("%Y-%m-%d-%H:%M:%S")+':: '+self.message_text+'\n')    
